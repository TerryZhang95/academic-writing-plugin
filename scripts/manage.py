#!/usr/bin/env python3
"""Install/check/uninstall Academic Writing with Codex's existing plugin mechanism."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from platform_support import safe_path, codex_binary, managed_installation_owned
from codex_app import App
from connection import CheckError, Connection

PACKAGE = Path(__file__).resolve().parents[1]
SELECTOR = 'academic-writing@academic-writing-public'
MARKET = 'academic-writing-public'
SKILL = 'academic-writing:academic-introduction-mcp'
SKILLS = (SKILL, 'academic-writing:academic-related-work-mcp', 'academic-writing:academic-system-model-mcp', 'academic-writing:academic-algorithm-mcp', 'academic-writing:academic-results-mcp', 'academic-writing:academic-whole-paper-mcp', 'academic-writing:academic-execution-mcp', 'academic-writing:academic-language-polish-mcp', 'academic-writing:academic-figure-prompt-mcp')


def run(codex, args, env):
    try:
        result = subprocess.run([codex_binary(codex, env), *args, '--json'], env=env, capture_output=True, text=True, timeout=40)
    except (OSError, subprocess.TimeoutExpired):
        raise CheckError('Codex CLI unavailable or timed out. Install/update Codex CLI and retry.') from None
    if result.returncode:
        raise CheckError('Codex plugin command failed; inspect Codex version and marketplace configuration.')
    return json.loads(result.stdout)


def check(destination, codex, env, inventory_only=False):
    app = App(codex, env)
    try:
        app.initialize()
        state = app.request('plugin/read', {'pluginName': 'academic-writing', 'marketplacePath': str(destination / '.agents/plugins/marketplace.json')})['plugin']
        if not state['summary']['installed'] or not state['summary']['enabled']:
            raise CheckError('Plugin is not installed/enabled. Run install, then refresh Codex.')
        listing = app.request('skills/list', {'cwds': [str(destination / 'examples')], 'forceReload': True})
        skills = [s['name'] for entry in listing['data'] for s in entry['skills'] if s['name'] in SKILLS and s['enabled']]
        if sorted(skills) != sorted(SKILLS):
            raise CheckError('Thin skill was not discovered. Refresh or restart Codex.')
        installed_version = json.loads((destination / 'plugins/academic-writing/.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version']
        if state['summary'].get('localVersion') != installed_version:
            raise CheckError('Codex installed version does not match the managed package')
        cached = Path(env['CODEX_HOME']) / 'plugins/cache/academic-writing-public/academic-writing' / installed_version / '.codex-plugin/plugin.json'
        if cached.is_symlink() or not cached.is_file() or json.loads(cached.read_text(encoding='utf-8')).get('version') != installed_version:
            raise CheckError('Codex cached plugin version was not refreshed')
        report = {'installed': True, 'client_version': installed_version, 'entrypoint': SKILL, 'entrypoints': list(SKILLS), 'model_calls': 0}
        if not inventory_only:
            status = app.request('mcpServerStatus/list', {'limit': 100})
            servers = [s for s in status['data'] if s.get('pluginId') == SELECTOR]
            if len(servers) != 1 or set(servers[0]['tools']) != {'get_writing_guidance'}:
                raise CheckError('Codex did not connect to the plugin MCP. Check public access and refresh Codex.')
            config = json.loads((destination / 'plugins/academic-writing/.mcp.json').read_text(encoding='utf-8'))
            report.update(Connection(config['mcpServers']['academic_guidance']['url']).check())
        else:
            report['connection'] = 'not tested (inventory-only developer check)'
        return report
    finally:
        app.close()


def manage(action, *, package=PACKAGE, codex='codex', home=None, inventory_only=False, confirm=False, expected_version=None, current_version=None, defer=False):
    home = safe_path(Path(home or os.environ.get('CODEX_HOME', Path.home() / '.codex')))
    home.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CODEX_HOME=str(home))
    for key in (set(os.environ) & {'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'CODEX_API_KEY'}) | {key for key in os.environ if key.endswith('_MCP_ACCESS_TOKEN')}:
        env.pop(key, None)
    marker = home / 'academic-writing-install.json'
    destination = home / 'academic-writing-distribution'
    safe_path(destination); safe_path(marker)
    if destination.is_symlink() or marker.is_symlink():
        raise CheckError('Managed installation paths must not be symbolic links')
    legacy_markers = [path for path in home.glob('*-writing-install.json') if path.name != 'academic-writing-install.json']
    if legacy_markers:
        raise CheckError('Previous writing plugin installation detected. Uninstall with the old installer, then install this Academic Writing bundle.')
    if action == 'install':
        known = run(codex, ['plugin', 'marketplace', 'list'], env)['marketplaces']
        for item in known:
            registered = Path(item.get('root', item.get('path', item.get('marketplaceSource', {}).get('source', '')))).resolve()
            if registered.name == 'marketplace.json':
                registered = registered.parents[2]
            if item.get('name') == MARKET and registered != destination:
                raise CheckError('Marketplace name already belongs to another source; refusing to replace it')
        if not destination.exists():
            if any(path.is_symlink() for path in package.rglob('*')):
                raise CheckError('Distribution symlinks are not permitted')
            from updates import ALLOWED, safe
            for relative in sorted(ALLOWED):
                source=safe(package/relative)
                if not source.is_file():
                    raise CheckError('Installation bundle is incomplete')
            destination.mkdir()
            for relative in sorted(ALLOWED):
                target=destination/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(package/relative,target)
            marker.write_text(json.dumps({'selector': SELECTOR, 'destination': str(destination)}) + '\n')
        elif not marker.exists() or not managed_installation_owned(json.loads(marker.read_text(encoding='utf-8')), destination):
            raise CheckError('Installation destination is not owned by this tool')
        run(codex, ['plugin', 'marketplace', 'add', str(destination)], env)
        run(codex, ['plugin', 'add', SELECTOR], env)
        return check(destination, codex, env, inventory_only)
    if not marker.exists():
        raise CheckError('No installation owned by this tool. Nothing was removed.')
    state = json.loads(marker.read_text(encoding='utf-8'))
    if not managed_installation_owned(state, destination):
        raise CheckError('Installation ownership metadata is invalid')
    if action in ('check-update', 'update'):
        from updates import check_update, update
        if action == 'check-update':
            return check_update(home, loaded_version=current_version, defer=defer)
        known = run(codex, ['plugin', 'marketplace', 'list'], env)['marketplaces']
        matched = [item for item in known if item.get('name') == MARKET]
        if len(matched) != 1:
            raise CheckError('Managed marketplace registration is missing')
        registered = Path(matched[0].get('root', matched[0].get('path', matched[0].get('marketplaceSource', {}).get('source', '')))).resolve()
        if registered.name == 'marketplace.json': registered = registered.parents[2]
        if registered != destination:
            raise CheckError('Marketplace belongs to another source; update refused')
        def install_check(target):
            try: run(codex, ['plugin', 'remove', SELECTOR], env)
            except CheckError: pass
            run(codex, ['plugin', 'add', SELECTOR], env)
            check(target, codex, env, inventory_only)
        return update(home, confirm=confirm, expected_version=expected_version, install_check=install_check)
    if action == 'check':
        return check(destination, codex, env, inventory_only)
    known = run(codex, ['plugin', 'marketplace', 'list'], env)['marketplaces']
    for item in known:
        if item.get('name') == MARKET:
            registered = Path(item.get('root', item.get('path', item.get('marketplaceSource', {}).get('source', '')))).resolve()
            if registered.name == 'marketplace.json':
                registered = registered.parents[2]
            if registered != destination:
                raise CheckError('Marketplace source changed; refusing to remove another installation')
    run(codex, ['plugin', 'remove', SELECTOR], env)
    run(codex, ['plugin', 'marketplace', 'remove', MARKET], env)
    shutil.rmtree(destination)
    marker.unlink()
    return {'uninstalled': True, 'model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'check', 'uninstall', 'check-update', 'update'))
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--home', type=Path, help='Developer test home; defaults to existing Codex home')
    parser.add_argument('--inventory-only', action='store_true', help='Developer-only: skip remote connection validation')
    parser.add_argument('--confirm', action='store_true', help='Explicit approval of this upgrade')
    parser.add_argument('--expected-version', help='Version explicitly approved by the user')
    parser.add_argument('--current-version', help='Loaded cached plugin version for read-only preflight')
    parser.add_argument('--defer', action='store_true', help='Defer reminders for the current latest version')
    args = parser.parse_args()
    try:
        report = manage(args.action, codex=args.codex, home=args.home, inventory_only=args.inventory_only, confirm=args.confirm, expected_version=args.expected_version, current_version=args.current_version, defer=args.defer)
    except (CheckError, OSError, ValueError) as error:
        parser.exit(1, str(error) if isinstance(error, CheckError) else 'Installation/check failed; verify local permissions.\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.action == 'install':
        print('Connection self-check passed.' if not args.inventory_only else 'Inventory check passed; connection was not tested.')
        print('Refresh or restart the desktop app, then open a new chat. Writing quality is not verified by this check.')


if __name__ == '__main__':
    main()
