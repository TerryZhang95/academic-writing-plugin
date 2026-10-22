#!/usr/bin/env python3
"""Local draft inventory and context batching. No model or network calls."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 128_000
DISPLAY = re.compile(r'(?<!\\)\$\$(?P<dollar>.*?)\$\$|\\\[(?P<bracket>.*?)\\\]|\\begin\{(?P<env>equation\*?|align\*?|aligned|gather\*?|gathered|flalign\*?|alignat\*?|eqnarray\*?|[A-Z]{4}eqnarray|split|multline\*?|displaymath)\}(?P<latex>.*?)\\end\{(?P=env)\}|^[ \t]*```math[ \t]*\r?\n(?P<fenced>.*?)\r?\n[ \t]*```[ \t]*(?=\r?\n|$)', re.S | re.M)
RELATION = re.compile(r'(?<![<>=!])=(?!=)|\\(?:triangleq|coloneqq|equiv|leq?|geq?)\b|[≤≥]')
SEPARATOR = re.compile(r'\\(?:q?quad|hspace\{[^}]*\}|hfill)|&(?!=)|[,;]|\\\\(?:\[[^]]*\])?')


class ReviewError(ValueError):
    pass


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def comments_masked(text):
    # Keep offsets for locations and original snippets.
    return re.sub(r'(?<!\\)%[^\n]*', lambda m: ' ' * len(m[0]), text)


def displays(text):
    return list(DISPLAY.finditer(comments_masked(text)))


def scan(text, material_id='draft'):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', material_id):
        raise ReviewError('Use a request-local material ID')
    rows = []
    masked = comments_masked(text)
    for index, match in enumerate(displays(text), 1):
        body = next(match[n] for n in ('dollar', 'bracket', 'latex', 'fenced') if match[n] is not None)
        pieces = SEPARATOR.split(body)
        reasons = []
        if sum(bool(RELATION.search(piece)) for piece in pieces) > 1:
            reasons.append('separated_relations')
        if len(re.findall(r'\\(?:triangleq|coloneqq)\b', body)) > 1:
            reasons.append('multiple_definitions')
        if reasons and match['env'] == 'equation' and '\\\\' in body:
            reasons.append('relations_share_numbered_environment')
        if reasons and re.search(r'\\tag\{', body):
            reasons.append('relations_share_explicit_tag')
        if re.search(r'\\(?:min|max|argmin|argmax)\b|subject\s+to|\\text\{\s*s\.?t', body):
            reasons.append('optimization_requires_semantic_review')
        rows.append({'display_id': f'{material_id}-display-{index}', 'material_id': material_id,
                     'start_line': text.count('\n', 0, match.start()) + 1,
                     'end_line': text.count('\n', 0, match.end()) + 1,
                     'start_offset': match.start(), 'end_offset': match.end(),
                     'snippet': text[match.start():match.end()], 'candidate_reasons': reasons})
    # An incomplete display cannot be considered inspected or split safely.
    covered = list(masked)
    for row in rows:
        covered[row['start_offset']:row['end_offset']] = ' ' * (row['end_offset'] - row['start_offset'])
    remainder = ''.join(covered)
    incomplete = bool(re.search(r'```math|(?<!\\)\$\$|\\[\[\]]|\\(?:begin|end)\{(?:equation\*?|align\*?|aligned|gather\*?|gathered|flalign\*?|alignat\*?|eqnarray\*?|[A-Z]{4}eqnarray|split|multline\*?|displaymath)\}', remainder))
    return {'material_id': material_id, 'draft_digest': digest(text), 'display_count': len(rows),
            'displays': rows, 'incomplete_display': incomplete, 'review_status': 'semantic_review_required'}


def chunks(text, budget):
    report = scan(text)
    if report['incomplete_display']:
        raise ReviewError('Incomplete display; resolve boundaries locally before batching')
    protected = [(r['start_offset'], r['end_offset']) for r in report['displays']]
    protected += [(m.start(), m.end()) for m in re.finditer(r'(?<!\\)\$(?!\$).*?(?<!\\)\$', text, re.S)]
    ends = [m.end() for m in re.finditer(r'\n[ \t]*\n', text)
            if not any(a < m.start() < b or a < m.end() < b for a, b in protected)]
    ends.append(len(text))
    start, buffered, result = 0, '', []
    for end in ends:
        unit = text[start:end]
        start = end
        if len(unit.encode('utf-8')) > budget:
            raise ReviewError('A complete paragraph or display exceeds the context budget; narrow the authorized section without truncating')
        if len((buffered + unit).encode('utf-8')) > budget:
            result.append(buffered)
            buffered = ''
        buffered += unit
    if buffered:
        result.append(buffered)
    return result


def batch(context):
    if type(context) is not dict or set(context)-{'task','materials','review','execution'} or not {'task','materials'}<=set(context) or type(context['task']) is not str or not context['task'].strip():
        raise ReviewError('Provide task and materials')
    materials = context['materials']
    if type(materials) is not list or not materials:
        raise ReviewError('Provide nonempty materials')
    ids = set()
    for m in materials:
        if type(m) is not dict or set(m)-{'id','role','text','region','order','replaces','artifact_id','part'} or not {'id','role','text'}<=set(m) or type(m['text']) is not str or not m['text'].strip():
            raise ReviewError('Invalid material block')
        if type(m['id']) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', m['id']) or m['id'] in ids or m['role'] not in ('source','plan','draft','registry'):
            raise ReviewError('Invalid material identity or role')
        ids.add(m['id'])
    plans = [m for m in materials if m['role'] in ('plan','registry')]
    fixed = len(context['task'].encode('utf-8')) + sum(len(m['text'].encode('utf-8')) for m in plans)
    if fixed >= MAX_BYTES or len(plans) >= 20:
        raise ReviewError('Task and relevant plans leave no material budget; narrow the plan locally')
    others = [m for m in materials if m['role'] not in ('plan','registry')]
    # When both source and draft are supplied, retain source in every draft batch.
    sources = [m for m in others if m['role'] == 'source'] if any(m['role']=='draft' for m in others) else []
    fixed += sum(len(m['text'].encode('utf-8')) for m in sources)
    repeated = plans + sources
    if fixed >= MAX_BYTES or len(repeated) >= 20:
        raise ReviewError('Select necessary bounded source and plan per draft section before batching')
    pieces = []
    for index, m in enumerate(others):
        if m in sources:
            continue
        for part, text in enumerate(chunks(m['text'], MAX_BYTES - fixed)):
            identity = f'chunk-{index}-{part}'
            while identity in ids:
                identity = 'c-' + identity
            ids.add(identity)
            pieces.append({**m,'id':identity,'text':text,'artifact_id':m.get('artifact_id',m['id']),'part':part})
    batches, current, size = [], list(repeated), fixed
    for m in pieces:
        count = len(m['text'].encode('utf-8'))
        if size + count > MAX_BYTES or len(current) >= 20:
            batches.append({**context,'materials':current})
            current, size = list(repeated), fixed
        current.append(m)
        size += count
    if current:
        batches.append({**context,'materials':current})
    return {'batches': batches, 'batch_count': len(batches), 'content_digest': digest(json.dumps(context, ensure_ascii=False, sort_keys=True)),
            'instruction': 'Check every batch and aggregate scope; a passed batch is not a whole-document pass.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('scan','batch','abbreviations','snapshot','artifacts'))
    parser.add_argument('--input', type=Path, help='Explicit authorized local UTF-8 file; otherwise stdin')
    parser.add_argument('--material-id', default='draft')
    args = parser.parse_args()
    try:
        if args.input:
            if args.input.is_symlink() or not args.input.is_file():
                raise ReviewError('Use an explicit regular local input file')
            with args.input.open(encoding='utf-8', newline='') as source:
                text = source.read()
        else:
            text = sys.stdin.buffer.read().decode('utf-8')
        if args.command=='scan':output=scan(text,args.material_id)
        elif args.command=='batch':output=batch(json.loads(text))
        elif args.command=='abbreviations':
            from abbreviation_review import inspect
            output=inspect(json.loads(text))
        else:
            from artifact_review import snapshot, check
            output=(snapshot if args.command=='snapshot' else check)(json.loads(text))
        print(json.dumps(output, ensure_ascii=False))
    except (ReviewError, OSError, UnicodeError, ValueError, TypeError, KeyError):
        parser.exit(2, 'Local context review failed; check input format, scope and complete formula boundaries.\n')


if __name__ == '__main__':
    main()
