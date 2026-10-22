#!/usr/bin/env python3
"""Local abbreviation candidates and final-view coverage; never a semantic verdict."""
import re
from context_review import comments_masked, displays, digest

TOKEN = re.compile(r"(?<![\w])(?:[A-Z]{2,}(?:-[A-Z0-9]+)*[0-9]*s?|[0-9]+-?[A-Z][A-Z0-9]*s?|[a-z]*[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|(?:[A-Za-z]\.){2,})(?:['’]s)?(?!\w)")
USAGE = re.compile(r'\\(gls|Gls|glspl|Glspl|ac|acs|acf|acp|acrshort|acrlong|acrfull)\{([^{}]+)\}')
DECLARATION = re.compile(r'\\newacronym(?:\[[^]]*\])?\{([^{}]+)\}\{([^{}]+)\}\{([^{}]+)\}|\\acro\{([^{}]+)\}\{([^{}]+)\}')
COMMAND_ARGUMENT = re.compile(r'\\(?:label|ref|eqref|autoref|cite\w*|url|input|include|includegraphics|bibliography)(?:\[[^]]*\])*\{[^{}]*\}')
UNITS = {'Hz','kHz','MHz','GHz','THz','dB','dBm','dBW','W','mW','kW','K','KB','MB','GB','TB','bps','Mbps','Gbps'}


def _mask(chars, start, end):
    chars[start:end] = ['\n' if c=='\n' else ' ' for c in chars[start:end]]


def generic_declarations(text):
    pattern=re.compile(r'\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand)\*?\s*\{\\([A-Za-z]+)\}(?:\[[^]]*\])*\s*\{')
    for m in pattern.finditer(text):
        depth=1;end=m.end()
        while end<len(text) and depth:
            if text[end]=='{' and (end==0 or text[end-1]!='\\'):depth+=1
            if text[end]=='}' and (end==0 or text[end-1]!='\\'):depth-=1
            end+=1
        if depth==0:yield m.start(),end,m[1],text[m.end():end-1]


def prose(text, preserve_macros=False):
    chars = list(comments_masked(text))
    for m in displays(text): _mask(chars,m.start(),m.end())
    for pattern in [r'(?<!\\)\$(?!\$).*?(?<!\\)\$', r'\\\(.*?\\\)', r'```(?!math)[^\n]*\n.*?```', r'~~~[^\n]*\n.*?~~~']:
        for m in re.finditer(pattern,''.join(chars),re.S): _mask(chars,m.start(),m.end())
    for m in COMMAND_ARGUMENT.finditer(''.join(chars)): _mask(chars,m.start(),m.end())
    for m in DECLARATION.finditer(''.join(chars)): _mask(chars,m.start(),m.end())
    for start,end,_,_ in generic_declarations(''.join(chars)): _mask(chars,start,end)
    if not preserve_macros:
        for m in USAGE.finditer(''.join(chars)): _mask(chars,m.start(),m.end())
        for m in re.finditer(r'\\[A-Za-z@]+\*?', ''.join(chars)): _mask(chars,m.start(),m.end())
    return ''.join(chars)


def base_token(token):
    token = re.sub(r"['’]s$",'',token)
    if token.endswith('s') and sum(c.isupper() for c in token[:-1])>=2: token=token[:-1]
    return token


def observed_expansion(text, start, end):
    # Capture evidence only; a model must verify grammatical boundaries and meaning.
    before = text[max(0,start-240):start]
    after = text[end:end+240]
    if before.rstrip().endswith('(') and after.lstrip().startswith(')'):
        prefix = before.rstrip()[:-1].rstrip()
        prefix = re.split(r'[\n.;:!?]',prefix)[-1]
        prefix = re.split(r'\b(?:define|defines|use|uses|denote|denotes|is|are|the)\s+',prefix,flags=re.I)[-1]
        if prefix.strip():return prefix.strip()
    match = re.match(r'\s*\(([^()\n]+)\)',after)
    if match and re.search(r'[a-z]',match[1]):return match[1].strip()
    return None


def registry_rows(text):
    rows=[]
    for line in text.splitlines():
        if '&' not in line or line.lstrip().startswith('%'):continue
        cells=[c.strip() for c in line.split('&')]
        if len(cells)<4 or cells[0].lower() in ('abbrev.','abbreviation'):continue
        if not TOKEN.fullmatch(cells[0]):continue
        rows.append({'abbreviation':base_token(cells[0]),'expansion':cells[1],
                     'first_use':cells[2],'status':cells[3].replace('\\\\','').strip()})
    return rows


def inspect(view):
    if type(view) is not dict or type(view.get('materials')) is not list:
        raise ValueError('Provide an ordered final-view materials list')
    materials=view['materials'];ids=set()
    for m in materials:
        if type(m) is not dict or type(m.get('id')) is not str or type(m.get('text')) is not str or m['id'] in ids:
            raise ValueError('Invalid or duplicate final-view material')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',m['id']):raise ValueError('Logical IDs required')
        if m.get('region','unknown') not in ('body','abstract','reference','unknown'):raise ValueError('Unsupported region')
        if 'order' in m and (type(m['order']) is not int or m['order']<0):raise ValueError('Invalid reading order')
        ids.add(m['id'])
    replaced={m['replaces'] for m in materials if m.get('role')=='draft' and 'replaces' in m}
    scope_issues=[]
    for identity in replaced:
        if identity not in ids:scope_issues.append({'reason':'replacement_source_unavailable','material_id':identity})
    selected=[m for m in materials if m['id'] not in replaced and m.get('role') not in ('plan','registry') and m.get('region','unknown')!='reference']
    separated=[]
    for m in selected:
        abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',m['text'],re.S)
        if abstract and m.get('region') in ('body','unknown'):
            body=list(m['text']);_mask(body,abstract.start(),abstract.end())
            abstract_text=list(m['text']);_mask(abstract_text,0,abstract.start(1));_mask(abstract_text,abstract.end(1),len(abstract_text))
            separated += [{**m,'region':'abstract','text':''.join(abstract_text)}, {**m,'region':'body','text':''.join(body)}]
        else:separated.append(m)
    selected=separated
    selected=sorted(enumerate(selected),key=lambda p:(p[1].get('order',p[0]),p[0]))
    selected=[m for _,m in selected]
    if any(m.get('region','unknown')=='unknown' for m in selected):scope_issues.append({'reason':'abstract_body_region_unconfirmed'})
    for region in ('body','abstract'):
        ordered=[m.get('order') for m in selected if m.get('region')==region]
        if any(o is None for o in ordered) or len(set(ordered))!=len(ordered):
            if ordered:scope_issues.append({'reason':'reading_order_unconfirmed','region':region})
    review=view.get('review',{})
    strict=review.get('mode','light')=='strict'
    if strict and (review.get('coverage','partial')!='complete' or not any(m.get('region')=='body' for m in selected)):
        scope_issues.append({'reason':'strict_coverage_incomplete'})
    registries=[m for m in materials if m.get('role')=='registry']
    rows=[r for m in registries for r in registry_rows(m['text'])]
    if strict and not registries:scope_issues.append({'reason':'strict_registry_missing'})
    macros={}
    for m in materials:
        if m.get('role')=='plan' or m['id'] in replaced:continue
        for decl in DECLARATION.finditer(comments_masked(m['text'])):
            key=decl[1] or decl[4];abbr=decl[2] or decl[4];expansion=decl[3] or decl[5]
            macros[key]=(abbr,expansion)
    generic={}
    for m in materials:
        if m['id'] not in replaced and m.get('role')!='plan':
            generic.update({name:body for _,_,name,body in generic_declarations(comments_masked(m['text']))})
    exceptions=view.get('exceptions',[])
    documented={x.get('abbreviation'):x.get('reason') for x in exceptions if type(x) is dict and x.get('reason')}
    uses=[]
    for material in selected:
        text=material['text'];clean=prose(text)
        candidates=[(m.start(),m.end(),m[0],None) for m in TOKEN.finditer(clean)]
        # Explicit registry terms supplement token shape detection.
        for term in {r['abbreviation'] for r in rows}:
            if TOKEN.fullmatch(term):continue
            candidates.extend((m.start(),m.end(),m[0],None) for m in re.finditer(r'(?<!\w)'+re.escape(term)+r'(?!\w)',clean))
        for usage in USAGE.finditer(prose(text,preserve_macros=True)):
            if material.get('region')=='reference':continue
            if usage[2] not in macros:
                scope_issues.append({'reason':'unresolved_abbreviation_macro','material_id':material['id'],'line':text.count('\n',0,usage.start())+1,'key':usage[2]})
            else:
                candidates.append((usage.start(),usage.end(),macros[usage[2]][0],usage[1]))
        for usage in re.finditer(r'\\([A-Z]{2,})(?![A-Za-z])',prose(text,preserve_macros=True)):
            if usage[1] in generic:
                candidates.append((usage.start(),usage.end(),usage[1],'custom_macro'))
            elif usage[1] in {r['abbreviation'] for r in rows} or any(t[2]==usage[1] for t in candidates):
                scope_issues.append({'reason':'unresolved_abbreviation_macro','material_id':material['id'],'line':text.count('\n',0,usage.start())+1,'key':usage[1]})
        unique=set()
        for start,end,token,macro in sorted(candidates):
            if (start,token) in unique:continue
            unique.add((start,token))
            base=base_token(token)
            if base in UNITS:continue
            expansion=observed_expansion(text,start,end) if not macro else None
            uses.append({'abbreviation':base,'token':token,'material_id':material['id'],
                'region':material.get('region','unknown'),'order':material.get('order'),
                'line':text.count('\n',0,start)+1,'offset':start,'expansion_evidence':expansion,
                'macro':macro,'candidate_reasons':(['macro_expansion_requires_review'] if macro else [])+
                    (['plural_or_possessive_requires_review'] if token!=base else [])})
    groups={}
    for use in uses: groups.setdefault((use['region'],use['abbreviation']),[]).append(use)
    findings=[]
    for (region,abbr),group in groups.items():
        first=group[0]
        definitions=[u for u in group if u['expansion_evidence']]
        if not first['expansion_evidence'] and not first['macro'] and abbr not in documented:
            findings.append({'abbreviation':abbr,'region':region,'reason':'first_visible_use_without_expansion','location':first})
        if len(definitions)>1:
            findings.append({'abbreviation':abbr,'region':region,'reason':'repeated_or_conflicting_expansion','locations':definitions})
        matching=[r for r in rows if r['abbreviation']==abbr]
        if strict and not matching and abbr not in documented:
            findings.append({'abbreviation':abbr,'region':region,'reason':'registry_row_missing'})
        for row in matching:
            if row['status']=='pending':findings.append({'abbreviation':abbr,'reason':'registry_definition_pending'})
            if region=='body' and f"{first['material_id']}:{first['line']}"!=row['first_use']:
                findings.append({'abbreviation':abbr,'reason':'registry_first_use_requires_review','observed':f"{first['material_id']}:{first['line']}",'registered':row['first_use']})
    for use in uses:
        for reason in use['candidate_reasons']:
            findings.append({'abbreviation':use['abbreviation'],'reason':reason,'location':use})
    body_terms={u['abbreviation'] for u in uses if u['region']=='body'}
    for row in rows:
        if strict and review.get('coverage')=='complete' and row['abbreviation'] not in body_terms:
            findings.append({'abbreviation':row['abbreviation'],'reason':'registry_entry_without_body_use'})
        for use in uses:
            evidence=use['expansion_evidence']
            if use['abbreviation']==row['abbreviation'] and evidence and evidence.casefold()!=row['expansion'].casefold():
                findings.append({'abbreviation':row['abbreviation'],'reason':'registry_expansion_requires_review','registered':row['expansion'],'location':use})
    expansions={}
    for use in uses:
        if use['expansion_evidence']:expansions.setdefault(use['abbreviation'],set()).add(use['expansion_evidence'])
    for abbr,terms in expansions.items():
        if len(terms)>1:findings.append({'abbreviation':abbr,'reason':'cross_region_expansion_requires_review','expansions':sorted(terms)})
    for finding in findings:
        import json
        finding['id']='abbr-'+digest(json.dumps(finding,sort_keys=True,ensure_ascii=False))[:16]
    final_view=[{k:m[k] for k in ('id','region','order','text') if k in m} for m in selected]
    import json
    return {'final_view_digest':digest(json.dumps(final_view,sort_keys=True,ensure_ascii=False,separators=(',',':'))),
        'registry_digest':digest(json.dumps([m['text'] for m in registries],ensure_ascii=False)),
        'material_digests':{m['id']:digest(m['text']) for m in materials},
        'uses':uses,'candidates':findings,'scope_issues':scope_issues,'registry_rows':rows,
        'exceptions':exceptions,'review_status':'semantic_review_required','strict':strict}
