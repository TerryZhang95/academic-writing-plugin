"""Standard-library platform helpers for the public client."""
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import signal
import subprocess


def safe_path(path):
    path = Path(path).expanduser().absolute()
    for item in (path, *path.parents):
        try:
            attributes = item.lstat()
        except FileNotFoundError:
            continue
        if item.is_symlink() or getattr(attributes, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Symbolic links and Windows reparse points are not permitted')
    return path


def managed_installation_owned(state, destination):
    """Match an exact ownership record using the host's safe path semantics."""
    if (not isinstance(state, dict) or set(state) != {'selector', 'destination'}
            or state['selector'] != 'academic-writing@academic-writing-public'
            or not isinstance(state['destination'], str)
            or not Path(state['destination']).is_absolute()):
        return False
    try:
        recorded = safe_path(state['destination'])
        expected = safe_path(destination)
    except (OSError, ValueError):
        return False
    return (os.path.normcase(os.path.normpath(str(recorded)))
            == os.path.normcase(os.path.normpath(str(expected))))


def codex_binary(command='codex', environment=None):
    environment = os.environ if environment is None else environment
    command = environment.get('CODEX_CLI_PATH', command) if str(command) == 'codex' else str(command)
    located = shutil.which(command, path=environment.get('PATH'))
    if not located and Path(command).is_file():
        located = command
    if not located:
        raise ValueError('Codex CLI not found. Install the native CLI or pass --codex with its executable path.')
    path = Path(located).absolute()
    if os.name == 'nt' and path.suffix.lower() in ('.cmd', '.bat', '.ps1'):
        # npm's wrapper can be bypassed: invoke its installed native binary directly.
        roots = [path.parent / 'node_modules' / '@openai']
        if path.parent.name == '.bin' and path.parent.parent.name == 'node_modules':
            roots.append(path.parent.parent / '@openai')
        candidates = []
        for root in roots:
            for executable in ('codex/codex.exe', 'bin/codex.exe'):
                candidates += list(root.glob('codex*/vendor/*/' + executable))
                candidates += list(root.glob('codex/node_modules/@openai/codex*/vendor/*/' + executable))
        candidates = sorted(set(p for p in candidates if p.is_file()))
        if len(candidates) != 1:
            raise ValueError('Use native codex.exe via --codex or CODEX_CLI_PATH; shell wrappers are not launched.')
        path = candidates[0]
    return str(path)


def process_options():
    return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}


def stop_process(process):
    if os.name == 'nt':
        if process.poll() is None:
            subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            if process.poll() is None:
                process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            if process.poll() is None:
                process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)


@contextmanager
def exclusive_lock(path):
    with safe_path(path).open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b'\0'); handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise BlockingIOError('Another client upgrade is running') from None
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
