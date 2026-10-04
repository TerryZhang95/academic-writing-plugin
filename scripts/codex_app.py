"""Read Codex plugin state through its app-server; never start a model turn."""
import json
import queue
import subprocess
import threading
import time
from connection import CheckError
from platform_support import codex_binary, process_options, stop_process


class App:
    def __init__(self, codex, environment):
        self.process = subprocess.Popen([codex_binary(codex, environment), 'app-server', '--stdio'], env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **process_options())
        self.sequence = 0
        self.messages = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            while True:
                # Limit malformed/missing-newline responses instead of growing without bound.
                line = self.process.stdout.readline(1048577)
                if not line:
                    break
                if len(line) > 1048576 or not line.endswith(b'\n'):
                    self.messages.put(CheckError('Invalid app-server response')); return
                try:
                    message = json.loads(line)
                    if not isinstance(message, dict):
                        raise ValueError()
                except (ValueError, UnicodeError):
                    self.messages.put(CheckError('Invalid app-server JSON')); return
                self.messages.put(message)
        except OSError:
            pass
        finally:
            self.messages.put(CheckError('Codex app-server exited during inspection'))

    def request(self, method, params, timeout=30):
        self.sequence += 1
        try:
            self.process.stdin.write((json.dumps({'id': self.sequence, 'method': method, 'params': params}) + '\n').encode())
            self.process.stdin.flush()
        except OSError:
            raise CheckError('Codex app-server exited during inspection') from None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                message = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                break
            if isinstance(message, Exception):
                raise message
            if message.get('id') == self.sequence:
                if 'error' in message or 'result' not in message:
                    raise CheckError('Codex rejected the plugin inspection request; update Codex CLI.')
                return message['result']
        raise CheckError('Codex plugin inspection timed out; refresh Codex and retry.')

    def initialize(self):
        self.request('initialize', {'clientInfo': {'name': 'academic-install-check', 'version': '0.3.0'}, 'capabilities': {'experimentalApi': True}})
        self.process.stdin.write(b'{"method":"initialized"}\n')
        self.process.stdin.flush()

    def close(self):
        try:
            stop_process(self.process)
        finally:
            self.process.stdin.close()
            self.reader.join(timeout=5)
            if not self.reader.is_alive():
                self.process.stdout.close()
