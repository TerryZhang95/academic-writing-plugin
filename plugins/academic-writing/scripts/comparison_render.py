"""Deterministic comparison exports from validated v2 data; standard library only."""
import argparse
import html
import json
from pathlib import Path
import tempfile
from comparison_io import load, validate, require

SYMBOLS = {'full':'●', 'yes':'●', 'partial':'◐', 'none':'○', 'no':'○', 'unknown':'?', 'nr':'NR', 'na':'N/A'}
TEX_SYMBOLS = {'●':r'$\bullet$', '◐':r'\ensuremath{\ComparisonPartial}', '○':r'$\circ$'}


def md(value):
    return html.escape(str(value)).replace('|', '&#124;').replace('\n', '<br>').replace('[', '&#91;').replace(']', '&#93;').replace('`', '&#96;').replace('*', '&#42;').replace('_', '&#95;')


def tex(value):
    chars = {'\\':r'\textbackslash{}', '&':r'\&', '%':r'\%', '$':r'\$', '#':r'\#', '_':r'\_', '{':r'\{', '}':r'\}', '~':r'\textasciitilde{}', '^':r'\textasciicircum{}'}
    return ''.join(chars.get(c, c) for c in str(value)).replace('\n', ' ')


def exports(data, criteria):
    report = validate(data)
    columns = data['columns']; footnotes = []
    def cell_text(cell, latex=False):
        value = SYMBOLS.get(cell['status'], cell.get('value', ''))
        if cell['status'] == 'value' and cell.get('unit'): value += ' ' + cell['unit']
        value = (TEX_SYMBOLS.get(value, tex(value)) if latex else md(value))
        note = '; '.join([cell['conditions']] if cell.get('conditions') else [])
        if cell.get('notes'): note = '; '.join(filter(None, [note, *cell['notes']]))
        if note:
            if note not in footnotes: footnotes.append(note)
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
    def table(standalone):
        out = ['% Requires booktabs and the standalone ComparisonPartial macro (TikZ).', r'\begin{table}[htbp]', r'\centering', r'\caption{' + tex(title) + '}', r'\label{' + data['label'] + '}', r'\begin{tabular}{p{0.27\linewidth}' + ('p{' + format(0.56 / len(columns), '.4f') + r'\linewidth}') * len(columns) + '}', r'\toprule']
        if any(c.get('group') for c in columns):
            groups = []; index = 0
            while index < len(columns):
                group = columns[index].get('group', ''); stop = index + 1
                while stop < len(columns) and columns[stop].get('group', '') == group: stop += 1
                groups.append(r'\multicolumn{' + str(stop-index) + '}{c}{' + tex(group) + '}'); index = stop
            out += [' & ' + ' & '.join(groups) + r' \\']
        out += ['Paper & ' + ' & '.join(tex(c['label']) for c in columns) + r' \\', r'\midrule']
        for row in data['papers']:
            name = tex(row['label'])
            if not standalone and row.get('cite_key'): name += r'~\cite{' + row['cite_key'] + '}'
            if row.get('is_ours'): name = r'\textbf{' + name + '}'
            out += [name + ' & ' + ' & '.join(cell_text(row['cells'][c['id']], True) for c in columns) + r' \\']
        out += [r'\bottomrule', r'\end{tabular}', r'\par\smallskip\footnotesize ' + r'$\bullet$ full; \ensuremath{\ComparisonPartial} partial; $\circ$ absence; ? unknown; NR not reported; N/A not applicable.']
        out += [r'\par ' + str(i) + '. ' + tex(note) for i, note in enumerate(footnotes, 1)]
        return '\n'.join(out + [r'\end{table}', ''])
    fragment = table(False); standalone = table(True)
    preamble = '\n'.join([r'\documentclass{article}', r'\usepackage[margin=15mm]{geometry}', r'\usepackage{booktabs,tikz}', r'\usepackage{iftex}', r'\ifPDFTeX\else\usepackage{fontspec}\setmainfont{Latin Modern Roman}\fi', r'\newcommand{\ComparisonPartial}{\tikz[baseline=-0.5ex]{\draw (0,0) circle (0.65ex);\fill (0,0.65ex) arc (90:270:0.65ex)--cycle;}}', r'\begin{document}', ''])
    return {'comparison.md':'\n'.join(rows)+'\n', 'evidence.md':'\n'.join(evidence)+'\n', 'comparison.tex':fragment, 'comparison-standalone.tex':preamble+standalone+'\\end{document}\n'}


def render(input_path, criteria_path, output):
    data = load(input_path); criteria = Path(criteria_path).read_text(encoding='utf-8')
    require(bool(criteria.strip()) and len(criteria.encode()) <= 24000, 'Invalid criteria file')
    # The criteria file is shareable project data; no private source map belongs here.
    require(not __import__('re').search(r'/(?:Users|home)/|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://', criteria), 'Criteria contains local paths')
    out = Path(output).absolute()
    require(not out.exists() and not out.is_symlink() and not any(p.is_symlink() for p in out.parents), 'Choose a new version directory without symlinks')
    files = exports(data, criteria)
    files.update({'comparison.json':json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'criteria.md':criteria})
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.comparison-', dir=out.parent) as temp:
        stage = Path(temp) / 'export'; stage.mkdir()
        for name, content in files.items(): (stage/name).write_text(content, encoding='utf-8')
        require(not out.exists(), 'Output appeared during rendering')
        stage.rename(out)
    return validate(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('--criteria', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try: print(json.dumps(render(args.input, args.criteria, args.out), sort_keys=True))
    except (ValueError, OSError, TypeError, KeyError): parser.exit(2, 'Comparison export failed; check contract and choose a new output directory.\n')
