"""Deterministic comparison exports from validated v2 data; standard library only."""
import argparse
import html
import json
from pathlib import Path
import tempfile
from comparison_io import load, validate, require
from comparison_layout import all_notes, cell_note, column_parts, tables

SYMBOLS = {'full':'●', 'yes':'●', 'partial':'◐', 'none':'○', 'no':'○', 'unknown':'?', 'nr':'NR', 'na':'N/A'}
TEX_SYMBOLS = {'●':r'$\bullet$', '◐':r'\ensuremath{\ComparisonPartial}', '○':r'$\circ$'}


def md(value):
    return html.escape(str(value)).replace('|', '&#124;').replace('\n', '<br>').replace('[', '&#91;').replace(']', '&#93;').replace('`', '&#96;').replace('*', '&#42;').replace('_', '&#95;')


def tex(value):
    chars = {'\\':r'\textbackslash{}', '&':r'\&', '%':r'\%', '$':r'\$', '#':r'\#', '_':r'\_', '{':r'\{', '}':r'\}', '~':r'\textasciitilde{}', '^':r'\textasciicircum{}'}
    return ''.join(chars.get(c, c) for c in str(value)).replace('\n', ' ')


def exports(data, criteria, columns_per_part=6):
    report = validate(data)
    column_parts(data['columns'], columns_per_part)
    columns = data['columns']; footnotes = all_notes(data)
    def cell_text(cell, latex=False):
        value = SYMBOLS.get(cell['status'], cell.get('value', ''))
        if cell['status'] == 'value' and cell.get('unit'): value += ' ' + cell['unit']
        value = (TEX_SYMBOLS.get(value, tex(value)) if latex else md(value))
        note = cell_note(cell)
        if note:
            n = footnotes.index(note) + 1
            value += r'\textsuperscript{' + str(n) + '}' if latex else f'<sup>{n}</sup>'
        return value
    title = ('SYNTHETIC — ' if data.get('synthetic') else '') + data['title']
    evidence = ['# ' + md(title), '', criteria, '', '## Sources', '']
    for s in data['sources']:
        evidence += [f"### {s['id']}", md(json.dumps(s, ensure_ascii=False, sort_keys=True)), '']
    evidence += ['## Cell evidence', '']
    rows = ['# ' + md(title), '', '| Paper | ' + ' | '.join(md((c.get('group', '') + ': ' if c.get('group') else '') + c['label']) for c in columns) + ' |', '|---|' + '---|' * len(columns)]
    for row in data['papers']:
        cells = []
        for col in columns:
            cell = row['cells'][col['id']]; anchor = 'r' + str(len(row['id'])) + '-' + row['id'] + '-c' + col['id']
            cells.append(f'[{cell_text(cell)}](evidence.md#{anchor})')
            evidence += [f'<a id="{anchor}"></a>', f"### {md(row['label'])} / {md(col['label'])}", md(json.dumps(cell, ensure_ascii=False, sort_keys=True)), '']
        rows.append('| ' + md(row['label']) + ' | ' + ' | '.join(cells) + ' |')
    legend = '● full support/coverage; ◐ partial; ○ assessed absence; ? unknown; NR not reported; N/A not applicable.'
    rows += ['', legend, ''] + [f'{i}. {md(n)}' for i, n in enumerate(footnotes, 1)]
    evidence += ['## Mechanical check', md(json.dumps(report, sort_keys=True)), 'Source authenticity, quotation accuracy and semantic entailment require local review.']
    fragment = tables(data, title, cell_text, footnotes, tex, columns_per_part=columns_per_part)
    standalone = tables(data, title, cell_text, footnotes, tex, standalone=True, columns_per_part=columns_per_part)
    preamble = '\n'.join([r'\documentclass{article}', r'\usepackage[margin=15mm]{geometry}', r'\usepackage{booktabs,tikz}', r'\usepackage{iftex}', r'\ifPDFTeX\else\usepackage{fontspec}\setmainfont{Latin Modern Roman}\fi', r'\newcommand{\ComparisonPartial}{\tikz[baseline=-0.5ex]{\draw (0,0) circle (0.65ex);\fill (0,0.65ex) arc (90:270:0.65ex)--cycle;}}', r'\begin{document}', ''])
    return {'comparison.md':'\n'.join(rows)+'\n', 'evidence.md':'\n'.join(evidence)+'\n', 'comparison.tex':fragment, 'comparison-standalone.tex':preamble+standalone+'\\end{document}\n'}


def render(input_path, criteria_path, output, columns_per_part=6):
    data = load(input_path); criteria = Path(criteria_path).read_text(encoding='utf-8')
    require(bool(criteria.strip()) and len(criteria.encode()) <= 24000, 'Invalid criteria file')
    # The criteria file is shareable project data; no private source map belongs here.
    require(not __import__('re').search(r'/(?:Users|home)/|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://', criteria), 'Criteria contains local paths')
    out = Path(output).absolute()
    require(not out.exists() and not out.is_symlink() and not any(p.is_symlink() for p in out.parents), 'Choose a new version directory without symlinks')
    files = exports(data, criteria, columns_per_part)
    files.update({'comparison.json':json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'criteria.md':criteria})
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.comparison-', dir=out.parent) as temp:
        stage = Path(temp) / 'export'; stage.mkdir()
        for name, content in files.items(): (stage/name).write_text(content, encoding='utf-8')
        require(not out.exists(), 'Output appeared during rendering')
        stage.rename(out)
    return dict(validate(data), pdf_layout="not-checked", latex_parts=len(column_parts(data["columns"], columns_per_part)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('--criteria', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--columns-per-part', type=int, choices=range(1, 7), default=6, help='Maximum comparison columns per LaTeX part (default: 6)')
    args = parser.parse_args()
    try: print(json.dumps(render(args.input, args.criteria, args.out, args.columns_per_part), sort_keys=True))
    except (ValueError, OSError, TypeError, KeyError): parser.exit(2, 'Comparison export failed; check contract and choose a new output directory.\n')
