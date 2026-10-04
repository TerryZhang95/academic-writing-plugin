"""Read-only compatibility check for native Codex installations."""
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from platform_support import safe_path

GITHUB = 'https://github.com/TerryZhang95/academic-writing-plugin'
METADATA = GITHUB + '/releases/latest/download/release.json'


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'0\.1\.(0|[1-9][0-9]*)', value):
        raise ValueError('Unsupported client version')
    return tuple(map(int, value.split('.')))


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1 or data.get('client_contract') != 'ieee-client-0.1':
        raise ValueError('Unknown update contract')
    latest = data.get('latest_version'); minimum = data.get('minimum_compatible_version')
    if version(minimum) > version(latest):
        raise ValueError('Invalid version policy')
    if data.get('package_url') != GITHUB + '/releases/download/v' + latest + '/academic-writing-public-' + latest + '.zip':
        raise ValueError('Untrusted release URL')
    if not re.fullmatch(r'[0-9a-f]{64}', str(data.get('sha256', ''))) or not isinstance(data.get('summary'), str) or len(data['summary']) > 2000:
        raise ValueError('Invalid release metadata')
    return data


class ReleaseRedirect(HTTPRedirectHandler):
    max_redirections = 5
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        trusted = (parts.hostname == 'github.com' and parts.path.startswith('/TerryZhang95/academic-writing-plugin/releases/') and not parts.query) or parts.hostname in {'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}
        if not trusted or parts.scheme != 'https' or parts.username or parts.password or parts.port not in (None, 443) or parts.fragment:
            raise ValueError('Untrusted release redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_metadata():
    with build_opener(ReleaseRedirect()).open(Request(METADATA, headers={'Accept': 'application/json'}), timeout=10) as response:
        raw = response.read(16385)
    if len(raw) > 16384:
        raise ValueError('Metadata exceeds limit')
    return validate(json.loads(raw))


def check(loaded, home):
    installed = version(loaded)
    cache = safe_path(Path(home) / 'academic-writing-native-check.json')
    now = time.time(); saved = {}; data = None; status = 'checked'
    try:
        saved = json.loads(cache.read_text(encoding='utf-8'))
        if not isinstance(saved, dict) or type(saved.get('checked_at')) not in (int, float):
            saved = {}
    except (OSError, ValueError):
        pass
    age = now - saved.get('checked_at', 0)
    if saved.get('source') == METADATA and 0 <= age < 600:
        try:
            data = validate(saved.get('metadata')); status = 'cached'
        except ValueError:
            pass
    if data is None:
        try:
            data = fetch_metadata()
        except (OSError, ValueError):
            if saved.get('source') == METADATA and 0 <= age < 86400:
                try:
                    data = validate(saved.get('metadata')); status = 'offline cached compatibility; online check incomplete'
                except ValueError:
                    pass
            if data is None:
                return {'installation_mode': 'native', 'loaded_version': loaded, 'compatible': None, 'may_continue': False, 'installation_changed': False, 'status': 'offline; compatibility unknown'}
    if status == 'checked':
        # Cache failure must not turn a successful network check into a failure.
        try:
            safe_path(cache.parent).mkdir(parents=True, exist_ok=True)
            temporary = safe_path(cache.with_name(cache.name + '.' + str(os.getpid()) + '.tmp'))
            temporary.write_text(json.dumps({'source': METADATA, 'checked_at': now, 'metadata': data}), encoding='utf-8')
            temporary.replace(cache)
        except OSError:
            pass
    compatible = installed >= version(data['minimum_compatible_version'])
    return {'installation_mode': 'native', 'loaded_version': loaded, 'latest_version': data['latest_version'],
            'compatible': compatible, 'may_continue': compatible, 'update_available': installed < version(data['latest_version']),
            'installation_changed': False, 'status': status, 'summary': data['summary'],
            'message': 'Update or reinstall through the Codex surface where you installed this plugin, then start a new chat. Native installs are never taken over by the managed installer.'}
