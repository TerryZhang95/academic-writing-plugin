#!/usr/bin/env python3
"""Read-only update preflight from the cached public plugin."""
import json
import os
from pathlib import Path
import subprocess
import sys

home=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))).expanduser().absolute()
destination=home/'ieee-writing-distribution'
marker=home/'ieee-writing-install.json'
installer=destination/'scripts/manage.py'
for path in (home,destination,marker,installer):
    if any(parent.is_symlink() for parent in (path,*path.parents)):
        sys.exit('Unsafe managed installer path; update check was not run')
try:
    if json.loads(marker.read_text())!={'selector':'ieee-writing@ieee-writing-public','destination':str(destination)}:
        raise ValueError()
    manifest=Path(__file__).resolve().parents[1]/'.codex-plugin/plugin.json'
    loaded=json.loads(manifest.read_text())['version']
except (OSError,ValueError,KeyError):
    sys.exit('Managed updater unavailable. Install the public client bundle first; compatibility is unknown.')
try:
    result=subprocess.run([sys.executable,str(installer),'check-update','--home',str(home),'--current-version',loaded],timeout=30)
except (OSError,subprocess.TimeoutExpired):
    sys.exit('Update check unavailable or timed out; compatibility could not be checked.')
sys.exit(result.returncode)
