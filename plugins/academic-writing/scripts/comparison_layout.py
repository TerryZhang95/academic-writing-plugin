"""Width-bounded LaTeX parts; display mechanics only, no content assessment."""


def column_parts(columns, limit=6):
    if type(limit) is not int or not 1 <= limit <= 6:
        raise ValueError('columns-per-part must be an integer from 1 to 6')
    parts=[];current=[];i=0
    while i < len(columns):
        end=i+1;group=columns[i].get('group','')
        while group and end < len(columns) and columns[end].get('group','') == group:
            end+=1
        run=columns[i:end];i=end
        if current and len(current)+len(run) > limit:
            parts.append(current);current=[]
        while len(run) > limit:
            parts.append(run[:limit]);run=run[limit:]
        current.extend(run)
    if current:parts.append(current)
    return parts


def cell_note(cell):
    return '; '.join(filter(None,[cell.get('conditions',''),*cell.get('notes',[])]))


def all_notes(data):
    notes=[]
    for row in data['papers']:
        for col in data['columns']:
            note=cell_note(row['cells'][col['id']])
            if note and note not in notes:notes.append(note)
    return notes


def tables(data, title, cell_text, notes, escape, standalone=False, columns_per_part=6):
    parts=column_parts(data['columns'],columns_per_part);result=[]
    positions={col['id']:i for i,col in enumerate(data['columns'])}
    for part_index,columns in enumerate(parts,1):
        n=len(columns);caption=title+(f' (Part {part_index}/{len(parts)})' if len(parts)>1 else '')
        label=data['label']+('' if part_index==1 else f'-part-{part_index}')
        # Default outer padding: n+1 columns each contribute two tabcolsep.
        # Evaluate against the surrounding linewidth, including in a narrow float.
        out=['% Requires booktabs and the standalone ComparisonPartial macro (TikZ).',
             r'\begin{table}[htbp]',r'\centering',r'\caption{'+escape(caption)+'}',r'\label{'+label+'}',
             r'\edef\ComparisonBudget{\the\dimexpr\linewidth-'+str(2*(n+1))+r'\tabcolsep-1pt\relax}',
             r'\edef\ComparisonPaperWidth{\the\dimexpr\ComparisonBudget*3/10\relax}',
             r'\edef\ComparisonCellWidth{\the\dimexpr(\ComparisonBudget-\ComparisonPaperWidth)/'+str(n)+r'\relax}',
             r'\begin{tabular}{p{\ComparisonPaperWidth}'+r'p{\ComparisonCellWidth}'*n+'}',r'\toprule']
        if any(c.get('group') for c in columns):
            groups=[];i=0
            while i<n:
                name=columns[i].get('group','');end=i+1
                while end<n and columns[end].get('group','')==name:end+=1
                position=positions[columns[i]['id']]
                if name and position>0 and data['columns'][position-1].get('group','')==name:
                    name+=' (continued)'
                k=end-i
                # Multicolumn replaces k column paddings by its two outer ones.
                width=r'\dimexpr\ComparisonCellWidth*'+str(k)+'+'+str(2*(k-1))+r'\tabcolsep\relax'
                groups.append(r'\multicolumn{'+str(k)+'}{p{'+width+'}}{'+r'\centering '+escape(name)+r'\par}')
                i=end
            out+=[' & '+' & '.join(groups)+r' \\']
        out+=['Paper & '+' & '.join(escape(c['label']) for c in columns)+r' \\',r'\midrule']
        used=set()
        for row in data['papers']:
            name=escape(row['label'])
            if not standalone and row.get('cite_key'):name+=r'~\cite{'+row['cite_key']+'}'
            if row.get('is_ours'):name=r'\textbf{'+name+'}'
            values=[]
            for col in columns:
                cell=row['cells'][col['id']];values.append(cell_text(cell,True))
                if cell_note(cell):used.add(notes.index(cell_note(cell))+1)
            out+=[name+' & '+' & '.join(values)+r' \\']
        out+=[r'\bottomrule',r'\end{tabular}',r'\par\smallskip\footnotesize '+r'$\bullet$ full; \ensuremath{\ComparisonPartial} partial; $\circ$ absence; ? unknown; NR not reported; N/A not applicable.']
        out+=[r'\par '+str(i)+'. '+escape(notes[i-1]) for i in sorted(used)]
        result.append('\n'.join(out+[r'\end{table}','']))
    return '\n'.join(result)
