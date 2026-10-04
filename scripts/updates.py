"""Public client updates: fixed GitHub release metadata, explicit consent and rollback."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import zipfile
from connection import CheckError
from platform_support import safe_path, exclusive_lock, managed_installation_owned

ALLOWED = frozenset(['.agents/plugins/marketplace.json', 'README.md', 'compatibility.json', 'examples/context.md', 'examples/introduction.tex', 'examples/related-work-context.md', 'examples/related-work.tex', 'plugins/academic-writing/.codex-plugin/plugin.json', 'plugins/academic-writing/.mcp.json', 'plugins/academic-writing/README.md', 'plugins/academic-writing/scripts/bridge.py', 'plugins/academic-writing/skills/academic-execution-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-execution-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-figure-prompt-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-figure-prompt-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-introduction-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-introduction-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-language-polish-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-language-polish-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-related-work-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-related-work-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-results-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-results-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-system-model-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-system-model-mcp/agents/openai.yaml', 'plugins/academic-writing/skills/academic-whole-paper-mcp/SKILL.md', 'plugins/academic-writing/skills/academic-whole-paper-mcp/agents/openai.yaml', 'scripts/codex_app.py', 'scripts/connection.py', 'scripts/manage.py', 'scripts/run_writing_acceptance.py', 'scripts/updates.py', 'scripts/platform_support.py', 'scripts/version_check.py', 'plugins/academic-writing/scripts/platform_support.py', 'plugins/academic-writing/scripts/version_check.py', 'plugins/academic-writing/scripts/preflight.py'])
MAX_PACKAGE = 1048576
MAX_EXPANDED = 2097152
GITHUB = 'https://github.com/TerryZhang95/academic-writing-plugin'
RELEASE_METADATA = GITHUB + '/releases/latest/download/academic-release.json'
CACHE_SECONDS = 600
OFFLINE_SECONDS = 86400

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise CheckError('Update redirects are forbidden')

def safe(path):
    try:
        return safe_path(path)
    except ValueError:
        raise CheckError('Update paths must not contain links or reparse points') from None

def owned(home):
    safe(home)
    dest=safe(home/'academic-writing-distribution')
    marker=safe(home/'academic-writing-install.json')
    if not marker.is_file() or not managed_installation_owned(json.loads(marker.read_text(encoding='utf-8')), dest):
        raise CheckError('Install with the public managed installer before checking updates')
    state=safe(home/'academic-writing-updates')
    state.mkdir(mode=0o700, exist_ok=True)
    return dest,state

def origin(dest):
    url=json.loads((dest/'plugins/academic-writing/.mcp.json').read_text(encoding='utf-8'))['mcpServers']['academic_guidance']['url']
    parts=urlsplit(url)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or parts.path!='/mcp' or parts.query or parts.fragment:
        raise CheckError('Updates require the trusted HTTPS MCP installation')
    return 'https://'+parts.netloc

def trusted_download(url):
    parts=urlsplit(url)
    if parts.scheme!='https' or parts.username or parts.password or parts.port not in (None,443) or parts.fragment:
        return False
    if parts.hostname=='github.com':
        return parts.path.startswith('/TerryZhang95/academic-writing-plugin/releases/') and not parts.query
    return parts.hostname in {'release-assets.githubusercontent.com','objects.githubusercontent.com'}

class GitHubRedirect(HTTPRedirectHandler):
    max_redirections=5
    max_repeats=2
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted_download(newurl):
            raise CheckError('GitHub download redirected outside the trusted release hosts')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url, limit):
    github=url.startswith(GITHUB+'/releases/')
    try:
        opener=build_opener(GitHubRedirect() if github else NoRedirect())
        with opener.open(Request(url,headers={'Accept':'application/json, application/zip'}), timeout=10) as response:
            if (github and not trusted_download(response.geturl())) or (not github and response.geturl()!=url):
                raise CheckError('Update source changed')
            data=response.read(limit+1)
    except CheckError:
        raise
    except Exception:
        raise CheckError('Update server unavailable; no installation changed') from None
    if len(data)>limit:
        raise CheckError('Update response exceeds the size limit')
    return data

def version(value):
    if not isinstance(value,str) or not re.fullmatch(r'0\.1\.(0|[1-9][0-9]*)',value):
        return None
    return tuple(map(int,value.split('.')))

def validate_metadata(data, base):
    if not isinstance(data,dict) or data.get('schema_version')!=1 or data.get('client_contract')!='academic-client-0.1':
        raise CheckError('Unknown client update contract')
    latest=data.get('latest_version'); minimum=data.get('minimum_compatible_version')
    if version(latest) is None or version(minimum) is None or version(minimum)>version(latest):
        raise CheckError('Invalid client version policy')
    expected=(GITHUB+'/releases/download/v'+latest+'/academic-writing-public-'+latest+'.zip' if base==GITHUB else base+'/client/academic-writing-public-'+latest+'.zip')
    if data.get('package_url')!=expected or not re.fullmatch('[0-9a-f]{64}',str(data.get('sha256',''))):
        raise CheckError('Package must use the fixed trusted service path')
    if not isinstance(data.get('summary'),str) or len(data['summary'])>2000:
        raise CheckError('Invalid update summary')
    return data

def current(dest):
    return json.loads((dest/'plugins/academic-writing/.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version']

def check_update(home, *, loaded_version=None, defer=False, force=False):
    dest,state=owned(home); origin(dest); base=GITHUB; cache=safe(state/'check.json')
    saved={}
    if cache.exists():
        try: saved=json.loads(cache.read_text(encoding='utf-8'))
        except (ValueError,OSError): pass
    if not isinstance(saved,dict) or not isinstance(saved.get('checked_at',0),(int,float)):
        saved={}
    now=time.time(); age=now-saved.get('checked_at',0)
    metadata=None; status='checked'
    if not force and 0<=age<CACHE_SECONDS and saved.get('origin')==base:
        try:
            metadata=validate_metadata(saved.get('metadata'),base); status='cached'
        except CheckError:
            saved={}
    if metadata is None:
        try: metadata=validate_metadata(json.loads(fetch(RELEASE_METADATA,16384)),base)
        except CheckError:
            if saved.get('origin')==base and 0<=age<OFFLINE_SECONDS:
                try:
                    metadata=validate_metadata(saved.get('metadata'),base); status='offline cached compatibility; online check incomplete'
                except CheckError:
                    metadata=None
            if metadata is None:
                return {'status':'offline; compatibility unknown','installed_version':loaded_version or current(dest),'compatible':None,'may_continue':False,'installation_changed':False}
    managed_version=current(dest)
    installed=loaded_version or managed_version
    restart_required=installed!=managed_version
    compatible=version(installed) is not None and version(installed)>=version(metadata['minimum_compatible_version'])
    deferred=saved.get('deferred_version')
    if defer: deferred=metadata['latest_version']
    encoded=json.dumps({'origin':base,'metadata':metadata,'checked_at':now if status=='checked' else saved.get('checked_at',now),'deferred_version':deferred})+'\n'
    temporary=safe(state/('cache-'+str(os.getpid())+'.json'))
    temporary.write_text(encoded); temporary.replace(cache)
    return {'status':status,'installed_version':managed_version,'loaded_version':installed,'restart_required':restart_required,'message':('The installed client changed. Refresh/restart Codex and open a new chat.' + (' No repeated installation is needed.' if managed_version==metadata['latest_version'] else ' The managed installation also has an available update.')) if restart_required else '', 'latest_version':metadata['latest_version'],'minimum_compatible_version':metadata['minimum_compatible_version'],'compatible':compatible,'may_continue':compatible,'update_available':version(managed_version) is not None and version(managed_version)<version(metadata['latest_version']),'remind':deferred!=metadata['latest_version'],'summary':metadata['summary'],'installation_changed':False}

def extract(data, stage, expected, base):
    with zipfile.ZipFile(__import__('io').BytesIO(data)) as archive:
        members=archive.infolist()
        if len(members)!=len(ALLOWED) or len(members)>64 or sum(i.file_size for i in members)>MAX_EXPANDED:
            raise CheckError('Unexpected package inventory or expanded size')
        found=set()
        for item in members:
            name=item.filename
            if not name.startswith('academic-writing/'):
                raise CheckError('Unexpected archive root')
            relative=name[len('academic-writing/'):]
            mode=item.external_attr>>16
            if relative not in ALLOWED or relative in found or item.is_dir() or item.flag_bits&1 or stat.S_IFMT(mode) not in (0,stat.S_IFREG) or item.file_size>150000:
                raise CheckError('Forbidden package member')
            found.add(relative)
            target=stage/relative; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.read(item))
        if found!=ALLOWED or current(stage)!=expected:
            raise CheckError('Package version/inventory mismatch')
        if origin(stage)!=base:
            raise CheckError('Package changes the trusted MCP service')
        catalog=json.loads((stage/'.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
        if catalog.get('name')!='academic-writing-public' or len(catalog.get('plugins',[]))!=1 or catalog['plugins'][0].get('name')!='academic-writing' or json.loads((stage/'plugins/academic-writing/.codex-plugin/plugin.json').read_text(encoding='utf-8')).get('name')!='academic-writing' or catalog['plugins'][0].get('source')!={'source':'local','path':'./plugins/academic-writing'}:
            raise CheckError('Package changes marketplace ownership')

def _update(home, *, confirm, expected_version, install_check):
    if not confirm or version(expected_version) is None:
        raise CheckError('Upgrade requires explicit --confirm and --expected-version after user approval')
    dest,state=owned(home); base=origin(dest)
    metadata=validate_metadata(json.loads(fetch(RELEASE_METADATA,16384)),GITHUB)
    if metadata['latest_version']!=expected_version:
        raise CheckError('Available version changed; show the new summary and request confirmation again')
    installed=version(current(dest))
    if installed is None or version(expected_version)<=installed:
        raise CheckError('This updater only installs a newer version in the supported client series')
    data=fetch(metadata['package_url'],MAX_PACKAGE)
    if hashlib.sha256(data).hexdigest()!=metadata['sha256']:
        raise CheckError('Package integrity check failed; installation unchanged')
    with tempfile.TemporaryDirectory(prefix='upgrade-',dir=state) as temporary:
        folder=Path(temporary); stage=folder/'candidate'; stage.mkdir()
        extract(data,stage,expected_version,base)
        backup=safe(state/('backup-'+str(time.time_ns())))
        try:
            dest.rename(backup)
            stage.rename(dest)
            install_check(dest)
        except Exception:
            if backup.exists():
                if dest.exists(): shutil.rmtree(dest)
                backup.rename(dest)
                try: install_check(dest)
                except Exception:
                    raise CheckError('Old files restored; Codex registration recovery needs the installer check command') from None
            raise CheckError('Upgrade failed; previous files and Codex registration restored') from None
    shutil.rmtree(backup)
    return {'updated':True,'version':expected_version,'restart_required':True,'message':'Refresh/restart Codex and open a new chat before using the new version. Existing tasks keep their selected rules version.'}


def update(home, **options):
    _,state=owned(home)
    lock=safe(state/'update.lock')
    try:
        with exclusive_lock(lock):
            return _update(home,**options)
    except BlockingIOError:
        raise CheckError('Another client upgrade is running') from None
