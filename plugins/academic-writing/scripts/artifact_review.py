#!/usr/bin/env python3
"""Read-only artifact and review-evidence checks. Never executes a task or model."""
import hashlib
import json
from pathlib import Path
import re
from context_review import comments_masked, digest

MAX_FILES = 512
MAX_FILE_BYTES = 16_000_000


def _root(value):
    root=Path(value).absolute()
    if root.is_symlink() or any(p.is_symlink() for p in root.parents) or not root.is_dir():
        raise ValueError('Use an authorized regular project root')
    return root.resolve()


def _path(root, value):
    path=Path(value)
    if not path.is_absolute():path=root/path
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(root):
        raise ValueError('Artifact path is outside the authorized root or uses a link')
    return path.resolve()


def structure(text):
    text=comments_masked(text)
    stack=[];issues=[]
    for m in re.finditer(r'\\(begin|end)\{([^{}]+)\}',text):
        if m[1]=='begin':stack.append(m[2])
        elif not stack or stack.pop()!=m[2]:issues.append('environment_mismatch')
    if stack:issues.append('environment_unclosed')
    return {'headings':[list(x) for x in re.findall(r'\\((?:sub)*section\*?)\{([^{}]*)\}',text)],
        'labels':re.findall(r'\\label\{([^{}]*)\}',text),
        'references':re.findall(r'\\(?:eqref|ref|autoref)\{([^{}]*)\}',text),
        'citations':re.findall(r'\\cite\w*(?:\[[^]]*\])*\{([^{}]*)\}',text),
        'environments':re.findall(r'\\begin\{([^{}]+)\}',text),'issues':issues}


def snapshot(config):
    root=_root(config['project_root']);files={}
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root)
        if any(p.startswith('.') or p=='__pycache__' for p in relative.parts):continue
        if path.is_symlink():raise ValueError('Snapshot scope contains links')
        if not path.is_file():continue
        if len(files)>=MAX_FILES or path.stat().st_size>MAX_FILE_BYTES:raise ValueError('Snapshot scope exceeds bounded inventory; narrow the authorized project')
        raw=path.read_bytes();row={'digest':hashlib.sha256(raw).hexdigest()}
        if path.suffix in ('.tex','.md'):
            row['structure']=structure(raw.decode('utf-8'))
        files[relative.as_posix()]=row
    return {'project_root':str(root),'files':files,'complete':True}


def check(config):
    root=_root(config['project_root']);plan=config['local_execution']
    if plan.get('contract')!='academic-local-execution-v1':raise ValueError('Unsupported execution contract')
    if any(t.get('action') not in ('read','generate_plan','edit_text','save','scan','review') for t in plan.get('tasks',[])):
        raise ValueError('Unknown task operation')
    if any(set(t)-{'action','material_ids','artifact_ids','purpose'} for t in plan.get('tasks',[])):
        raise ValueError('Executable or unrecognized task fields are forbidden')
    expected=plan['expected_artifacts'];bindings=config.get('bindings',[])
    if len({b['id'] for b in bindings})!=len(bindings):raise ValueError('Duplicate bindings')
    known={b['id']:b for b in bindings};issues=[];actual={};texts={};writable=set()
    for artifact in expected:
        identity=artifact['id'];binding=known.get(identity)
        if not binding:
            issues.append({'id':identity,'reason':'expected_artifact_unbound'});continue
        if artifact.get('storage','file')=='file':
            if 'path' not in binding:issues.append({'id':identity,'reason':'file_binding_required'});continue
            path=_path(root,binding['path'])
            if artifact.get('writable') and not plan.get('read_only'):writable.add(path.relative_to(root).as_posix())
            if not path.is_file():issues.append({'id':identity,'reason':'expected_file_missing'});continue
            with path.open(encoding='utf-8',newline='') as f:text=f.read()
            actual[identity]={'path':str(path),'digest':digest(text),'kind':artifact['kind']}
        else:
            if type(binding.get('text')) is not str:issues.append({'id':identity,'reason':'actual_inline_text_missing'});continue
            text=binding['text'];actual[identity]={'digest':digest(text),'kind':artifact['kind']}
        texts[identity]=text
    before=config.get('snapshot')
    after=snapshot({'project_root':str(root)})
    if not before or before.get('project_root')!=str(root) or before.get('complete') is not True:
        issues.append({'reason':'before_snapshot_missing_or_incomplete'})
    else:
        changed={name for name in set(before['files'])|set(after['files']) if before['files'].get(name)!=after['files'].get(name)}
        for name in sorted(changed-writable):issues.append({'path':name,'reason':'unauthorized_file_change'})
        if plan.get('intent')=='text':
            for artifact in expected:
                binding=known.get(artifact['id'],{})
                if 'path' not in binding or artifact['kind'] not in ('section','main'):continue
                relative=_path(root,binding['path']).relative_to(root).as_posix()
                old=before['files'].get(relative,{}).get('structure');new=after['files'].get(relative,{}).get('structure')
                if old and new and config.get('preserve_structure',False):
                    for key in ('headings','labels','references','citations','environments'):
                        if old[key]!=new[key]:issues.append({'id':artifact['id'],'reason':'preserved_structure_changed','criterion':key})
    labels={};references=[]
    for identity,text in texts.items():
        if actual[identity]['kind'] not in ('main','section'):continue
        st=structure(text)
        for reason in st['issues']:issues.append({'id':identity,'reason':reason})
        for label in st['labels']:labels.setdefault(label,[]).append(identity)
        references += [(identity,label) for label in st['references']]
        binding=known[identity]
        if 'path' in binding:
            parent=_path(root,binding['path']).parent
            for m in re.finditer(r'\\(?:input|include)\{([^{}]+)\}',comments_masked(text)):
                target=m[1]
                if any(c in target for c in ('\\','#','$')):
                    issues.append({'id':identity,'reason':'dynamic_include_unverified'});continue
                path=_path(root,str(parent/target))
                if not path.suffix:path=path.with_suffix('.tex')
                if not path.is_file():issues.append({'id':identity,'reason':'included_file_missing','target':target})
                elif str(path) not in {a.get('path') for a in actual.values()}:
                    issues.append({'id':identity,'reason':'included_file_outside_inspected_bindings','target':target})
    for label,owners in labels.items():
        if len(owners)>1:issues.append({'label':label,'reason':'duplicate_label','ids':owners})
    for identity,label in references:
        if label not in labels:issues.append({'id':identity,'label':label,'reason':'reference_target_unverified'})
    record=config.get('record',{})
    contexts=config.get('check_contexts',[config.get('check_context',{})])
    if not contexts or type(contexts) is not list:raise ValueError('Provide final check contexts')
    ctx=contexts[-1]
    if any(c.get('stage')!='check' for c in contexts):issues.append({'reason':'non_check_context_supplied'})
    if len(contexts)>1 and set(record.get('checked_rules_versions',[]))!={c.get('rules_version') for c in contexts}:
        issues.append({'reason':'batch_check_versions_unverified'})
    if ctx.get('stage')!='check' or record.get('rules_version')!=ctx.get('rules_version') or not re.fullmatch(r'[0-9a-f]{64}',str(record.get('rules_version',''))):
        issues.append({'reason':'matching_check_rules_missing'})
    if record.get('status')!='passed' or record.get('unresolved') or not record.get('scope'):
        issues.append({'reason':'semantic_review_not_complete'})
    if record.get('registry_status') not in ('not_required','verified','pending'):
        issues.append({'reason':'registry_state_unrecorded'})
    if type(record.get('repair_count')) is not int or not 0<=record['repair_count']<=2:
        issues.append({'reason':'repair_count_unverified'})
    checked={}
    groups={}
    for c in contexts:
        for m in c.get('materials',[]):groups.setdefault(m.get('artifact_id',m['id']),[]).append(m)
    for identity,group in groups.items():
        unique={}
        conflict=False
        for m in group:
            part=m.get('part',0)
            if part in unique and (unique[part]['text']!=m['text'] or unique[part]['role']!=m['role']):conflict=True
            unique[part]=m
        if conflict or sorted(unique)!=list(range(len(unique))):
            issues.append({'id':identity,'reason':'checked_fragments_incomplete_or_conflicting'});continue
        first=unique[0]
        if any(m['role']!=first['role'] for m in unique.values()):
            issues.append({'id':identity,'reason':'checked_fragment_role_conflict'});continue
        checked[identity]={**first,'text':''.join(unique[i]['text'] for i in range(len(unique)))}
    for identity,artifact in actual.items():
        if artifact['kind']=='report':continue
        binding=known[identity];material=checked.get(binding.get('material_id',identity))
        required_role='registry' if artifact['kind']=='registry' else 'draft' if any(a['id']==identity and a.get('writable') for a in expected) else None
        if not material or digest(material.get('text',''))!=artifact['digest'] or required_role and material.get('role')!=required_role:
            issues.append({'id':identity,'reason':'delivered_text_not_in_last_check'})
        if record.get('reviewed_digests',{}).get(identity)!=artifact['digest']:
            issues.append({'id':identity,'reason':'review_digest_mismatch'})
    scans=config.get('formula_scans',[])
    if not isinstance(scans,list):raise ValueError('Provide actual formula scan reports')
    scanned={s.get('material_id'):s for s in scans}
    for identity,artifact in actual.items():
        if artifact['kind']=='report':continue
        scan=scanned.get(identity)
        if not scan or scan.get('draft_digest')!=artifact['digest'] or scan.get('incomplete_display'):
            issues.append({'id':identity,'reason':'matching_formula_scan_missing'})
    abbreviations=config.get('abbreviation_scan',{})
    if not abbreviations or not record.get('abbreviation_index_digest') or record['abbreviation_index_digest']!=abbreviations.get('final_view_digest'):
        issues.append({'reason':'matching_abbreviation_index_missing'})
    for identity,artifact in actual.items():
        if artifact['kind']!='report' and abbreviations.get('material_digests',{}).get(known[identity].get('material_id',identity))!=artifact['digest']:
            issues.append({'id':identity,'reason':'abbreviation_scan_stale_or_missing'})
    if any(s.get('reason') in ('unresolved_abbreviation_macro','replacement_source_unavailable') for s in abbreviations.get('scope_issues',[])):
        issues.append({'reason':'abbreviation_source_evidence_missing'})
    if plan.get('review',{}).get('mode')=='strict':
        if plan['review'].get('coverage')!='complete' or abbreviations.get('scope_issues'):
            issues.append({'reason':'strict_scope_or_registry_pending'})
        if not any(a['kind']=='registry' for a in actual.values()):issues.append({'reason':'strict_registry_unverified'})
        if record.get('registry_status')!='verified':issues.append({'reason':'strict_registry_state_pending'})
    decisions=record.get('candidate_decisions',{})
    candidates=[c['id'] for c in abbreviations.get('candidates',[]) if 'id' in c]
    candidates += [d['display_id'] for s in scans for d in s.get('displays',[]) if d.get('candidate_reasons')]
    for identity in candidates:
        decision=decisions.get(identity,{})
        if decision.get('status') not in ('valid','exception') or not decision.get('reason'):
            issues.append({'candidate_id':identity,'reason':'candidate_semantics_unresolved'})
    return {'artifacts':actual,'issues':issues,'status':'pending' if issues else 'evidence_consistent',
            'semantic_correctness':'determined_by_recorded_local_review_not_this_program','compiled_pdf_verified':False}
