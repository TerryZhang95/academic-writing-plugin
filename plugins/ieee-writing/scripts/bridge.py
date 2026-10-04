#!/usr/bin/env python3
"""Public data-transfer helper. Executes no uploaded/project code and stores no credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlencode

MAX_INPUT = 256_000
OUTPUTS = {'references': {'references.json','references.md'}, 'plot': {'figure.png','figure.pdf','figure.json'}}
SENSITIVE = {'.ssh','.aws','.codex','.git','.env','.config','.gnupg','auth.json','credentials','id_rsa','id_ed25519'}


class BridgeError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def plain(path):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise BridgeError('Symlinks are not allowed')
    if any(part.lower() in SENSITIVE or part.lower().endswith(('.pem','.key','.p12')) for part in path.parts):
        raise BridgeError('Sensitive paths are not allowed')
    return path


def files(root, names, kind):
    root = plain(Path(root).expanduser().absolute()).resolve(strict=True)
    if not root.is_dir() or not 1 <= len(names) <= 5:
        raise BridgeError('Provide a task directory and 1–5 explicit files')
    result, total = [], 0
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or any(p.startswith('.') for p in relative.parts):
            raise BridgeError('Files must be explicit visible paths inside the task directory')
        path = plain(root / relative)
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise BridgeError('File is outside the task directory or unavailable')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.(?:bib|tex|csv)', path.name):
            raise BridgeError('Only ordinary .tex/.bib/.csv names are accepted')
        if path.suffix not in (('.bib','.tex') if kind == 'references' else ('.csv',)):
            raise BridgeError('File extension does not match the selected task')
        total += path.stat().st_size
        if total > MAX_INPUT:
            raise BridgeError('Selected input files exceed the size limit')
        with path.open('rb') as source:
            raw = source.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT or b'\0' in raw:
            raise BridgeError('Only bounded UTF-8 text data is accepted')
        result.append({'name':path.name,'text':raw.decode('utf-8')})
    if len({f['name'] for f in result}) != len(result):
        raise BridgeError('Selected file basenames must be unique')
    return root, result


def endpoint():
    config = Path(__file__).resolve().parents[1] / '.mcp.json'
    url = json.loads(config.read_text())['mcpServers']['ieee_guidance']['url']
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.path != '/mcp' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise BridgeError('Installed public HTTPS connection required')
    return url[:-4] + '/tasks'


def request(url, payload=None, credential=None, binary=False):
    headers = {'Accept':'application/octet-stream' if binary else 'application/json'}
    if credential:
        headers['X-Task-Secret'] = credential
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    if data is not None:
        headers['Content-Type'] = 'application/json'
    try:
        with urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url, data=data, headers=headers), timeout=12) as response:
            raw = response.read(4 * 1024**2 + 1 if binary else 300001)
            if len(raw) > (4 * 1024**2 if binary else 300000):
                raise BridgeError('Response size limit exceeded')
            return raw if binary else json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise BridgeError('Service busy/rate limited; wait and explicitly retry the task') from None
        if error.code in (400,404):
            raise BridgeError('Task/input/library unavailable or expired; check the selected files and installed service') from None
        raise BridgeError('Service refused the request; no output saved') from None


def execute(base, selected, options, pin, task, deadline=None):
    submitted = request(base, {'task':task,'files':selected,'options':options,'library_release':pin})
    if submitted['library_release'] != pin:
        raise BridgeError('Submitted library changed; task stopped')
    identity, credential = submitted['task_id'], submitted['task_secret']
    if not re.fullmatch(r'[a-f0-9]{32}', identity) or not re.fullmatch(r'[A-Za-z0-9_-]{40,64}', credential):
        raise BridgeError('Invalid task capability')
    deadline = min(time.monotonic() + 100, deadline) if deadline is not None else time.monotonic() + 100
    while time.monotonic() < deadline:
        time.sleep(2)
        status = request(base + '/' + identity, credential=credential)
        if status['library_release'] != pin:
            raise BridgeError('Task library changed; task stopped')
        if status['status'] != 'running': break
    else: raise BridgeError('Task deadline exceeded; temporary server data will expire')
    if status['status'] != 'complete' or set(status['outputs']) != OUTPUTS[task]:
        raise BridgeError('Task failed: unsupported input, dependency or resource limit; no completion claimed')
    return {name:request(base + '/' + identity + '/outputs/' + name, credential=credential, binary=True)
            for name in status['outputs']}


def reference_batches(base, selected, pin, external):
    digest=hashlib.sha256(json.dumps(selected,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    merged=None; offset=0; batches=0; stopped=None
    deadline=time.monotonic()+500
    while True:
        try:
            if time.monotonic()>deadline: raise BridgeError('Whole reference task deadline reached')
            outputs=execute(base,selected,{'external':external,'batch_start':offset},pin,'references',deadline=deadline)
            value=json.loads(outputs['references.json'])
            total=value['total_entries']; rows=value['entries']
            if type(total) is not int or not 1<=total<=100 or type(rows) is not list or any(type(row) is not dict or type(row.get('index')) is not int for row in rows):
                raise BridgeError('Invalid reference batch count/rows')
            expected=list(range(total)) if offset==0 else list(range(offset,min(offset+20,total)))
            if (value['input_digest']!=digest or value['library_release']!=pin or value['batch_start']!=offset
                or type(total) is not int or not 1<=total<=100 or [r['index'] for r in rows]!=expected
                or (merged is not None and total!=merged['total_entries'])):
                raise BridgeError('Reference batch identity/count/offset changed; results not accepted')
            next_offset=offset+20 if external and offset+20<total else None
            if value['next_start']!=next_offset:raise BridgeError('Reference batch continuation changed')
            if merged is None: merged=value
            else:
                for row in rows:
                    if row['key']!=merged['entries'][row['index']]['key']:
                        raise BridgeError('Reference identity changed; batch not accepted')
                for row in rows:merged['entries'][row['index']]['external']=row['external']
            batches+=1
            if any(r['external']['status']=='rate_limited' for r in rows):
                stopped='Crossref rate limited: later batches paused; explicitly retry later';break
            if next_offset is None:break
            offset=next_offset
            time.sleep(2)
        except (BridgeError,OSError,ValueError,KeyError,TypeError):
            if merged is None:raise BridgeError('Whole-input reference check did not finish; no verified entry report is available') from None
            stopped='Reference batch failed or service busy; unaccepted/later entries remain pending';break
    merged['batch_count']=batches;merged['status']='partial' if stopped else 'complete';merged['batch_stop_reason']=stopped
    if stopped:
        for row in merged['entries']:
            if row['external']['status']=='pending':row['external']['reason']=stopped
    states=[row['external']['status'] for row in merged['entries']]
    merged['external_summary']={'checked':sum(state not in ('pending','not_checked','unavailable','rate_limited','ambiguous') for state in states),
                                'failed':sum(state=='unavailable' for state in states),
                                'pending':sum(state in ('pending','not_checked','rate_limited','ambiguous') for state in states)} if external else {'not_requested':len(states)}
    if external and (merged['external_summary']['failed'] or merged['external_summary']['pending']):merged['status']='partial'
    lines=['# Reference check','', 'Read files: '+', '.join(merged['read_files']),
           'Task status: '+merged['status'], 'External checking: '+('requested' if external else 'not requested'),
           'Missing citation keys: '+(', '.join(merged['missing_citation_keys']) or 'none'),
           'Duplicate keys: '+(', '.join(merged['duplicate_keys']) or 'none'),
           'Duplicate DOI groups: '+json.dumps(merged['duplicate_dois'],ensure_ascii=False),
           'Similar title pairs: '+json.dumps(merged['similar_title_pairs'],ensure_ascii=False),'','## Entries']
    for row in merged['entries']:
        lines.append('- ['+str(row['index']+1)+'] '+row['key']+': '+row['external']['status'])
        for issue in row['local_issues']:lines.append('  - '+issue['severity']+': '+issue['message'])
        for key in ('reason','message','evidence_url'):
            if row['external'].get(key):lines.append('  - '+key+': '+row['external'][key])
        for mismatch in row['external'].get('mismatches',[]):lines.append('  - mismatch: '+mismatch)
    lines+=['','## Scope']+['- '+scope for scope in merged['limits']]
    if stopped:lines+=['','Paused: '+stopped]
    return {'references.json':(json.dumps(merged,ensure_ascii=False,indent=2)+'\n').encode(),
            'references.md':('\n'.join(lines)+'\n').encode()}


def run(args):
    root, selected = files(args.root, args.files, args.task)
    output = plain(root / args.output)
    if not output.absolute().is_relative_to(root) or any(part == '..' or part.startswith('.') for part in Path(args.output).parts) or output.exists():
        raise BridgeError('Choose a new visible output directory inside the task directory')
    base = endpoint()
    info = request(base)
    if info.get('task_contract') != 'ieee-execution-v1':
        raise BridgeError('Execution service is unavailable; upgrade the installed plugin')
    pin = args.library_release or info['library_release']
    if args.task=='references':
        pinned_info=request(base+'?'+urlencode({'library_release':pin}))
        if pinned_info.get('library_release')!=pin or pinned_info.get('reference_batching') is not True:
            raise BridgeError('Reference batching unavailable in this fixed library; select a supported library explicitly, never silently switch')
        downloaded=reference_batches(base,selected,pin,args.external)
    else:
        options={'kind':args.kind,'xlabel':args.xlabel,'ylabel':args.ylabel,'title':args.title,'columns':args.columns}
        downloaded=execute(base,selected,options,pin,args.task)
    if sum(map(len, downloaded.values())) > 4 * 1024**2:
        raise BridgeError('Combined output size limit exceeded')
    plain(output)
    output.mkdir(parents=False, exist_ok=False)
    for name, data in downloaded.items():
        with (output / name).open('xb') as target:
            target.write(data)
    print(json.dumps({'status':json.loads(downloaded['references.json'])['status'] if args.task=='references' else 'complete','task':args.task,'library_release':pin,
                      'output_directory':str(output),'files':sorted(downloaded)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=['references','plot'])
    parser.add_argument('--root', required=True, help='User-authorized task directory; no recursive discovery')
    parser.add_argument('--files', nargs='+', required=True)
    parser.add_argument('--output', required=True, help='New directory directly inside task root')
    parser.add_argument('--library-release')
    parser.add_argument('--external', action='store_true', help='Allow DOI-only public Crossref requests')
    parser.add_argument('--kind', choices=['line','bar'], default='line')
    parser.add_argument('--xlabel', default='')
    parser.add_argument('--ylabel', default='')
    parser.add_argument('--title', default='')
    parser.add_argument('--columns', type=int, choices=[1,2], default=1)
    args = parser.parse_args()
    try:
        run(args)
    except BridgeError as error:
        raise SystemExit(str(error)) from None
    except (OSError,ValueError,KeyError,TypeError):
        raise SystemExit('Bridge stopped: invalid input/path, unavailable service, rate limit or execution failure. No credentials or private paths are reported.')


if __name__ == '__main__':
    main()
