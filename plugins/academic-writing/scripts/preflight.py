#!/usr/bin/env python3
"""Check cached plugin compatibility without requiring a managed installation."""
import json
import os
from pathlib import Path
import subprocess
import sys
from platform_support import safe_path, managed_installation_owned
from version_check import check


def run(plugin=None, home=None):
    plugin = safe_path(plugin or Path(__file__).absolute().parents[1])
    home = safe_path(home or Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
    manifest = json.loads((plugin / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    if manifest.get('name') != 'academic-writing':
        raise ValueError('Unexpected plugin identity')
    loaded = manifest['version']
    destination = home / 'academic-writing-distribution'
    marker = safe_path(home / 'academic-writing-install.json')
    installer = safe_path(destination / 'scripts/manage.py')
    owned = False
    if marker.is_file():
        try:
            owned = managed_installation_owned(json.loads(marker.read_text(encoding='utf-8')), destination)
        except ValueError:
            pass
    if owned:
        if not installer.is_file():
            raise ValueError('Managed installer is missing; repair the managed installation')
        result = subprocess.run([sys.executable, str(installer), 'check-update', '--home', str(home), '--current-version', loaded], timeout=30, capture_output=True, text=True)
        if result.returncode:
            raise ValueError('Managed compatibility check failed')
        report = json.loads(result.stdout)
        report['installation_mode'] = 'managed'
        print(json.dumps(report, ensure_ascii=True))
        return 0 if report.get('may_continue') is True else 1
    report = check(loaded, home)
    print(json.dumps(report, ensure_ascii=True))
    return 0 if report['may_continue'] else 1


def main():
    try:
        return run()
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        print('Plugin compatibility unknown: check Python, local paths and connectivity. No installation changed.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
