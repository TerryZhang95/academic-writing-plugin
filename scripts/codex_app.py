"""Read Codex plugin state through its app-server; never start a model turn."""
import json
import os
import selectors
import signal
import subprocess
import time
from connection import CheckError


class App:
    def __init__(self, codex, environment):
        self.process = subprocess.Popen([codex, 'app-server', '--stdio'], env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
        self.sequence = 0
        self.pending = b''

    def request(self, method, params):
        self.sequence += 1
        self.process.stdin.write((json.dumps({'id': self.sequence, 'method': method, 'params': params}) + '\n').encode())
        self.process.stdin.flush()
        deadline = time.monotonic() + 30
        with selectors.DefaultSelector() as reader:
            reader.register(self.process.stdout, selectors.EVENT_READ)
            while time.monotonic() < deadline:
                while b'\n' in self.pending:
                    line, self.pending = self.pending.split(b'\n', 1)
                    message = json.loads(line)
                    if message.get('id') == self.sequence:
                        if 'error' in message:
                            raise CheckError('Codex rejected the plugin inspection request; update Codex CLI.')
                        return message['result']
                if reader.select(timeout=.2):
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                    if not chunk:
                        raise CheckError('Codex app-server exited during inspection')
                    self.pending += chunk
        raise CheckError('Codex plugin inspection timed out; refresh Codex and retry.')

    def initialize(self):
        self.request('initialize', {'clientInfo': {'name': 'ieee-install-check', 'version': '0.2.0'}, 'capabilities': {'experimentalApi': True}})
        self.process.stdin.write(b'{"method":"initialized"}\n')
        self.process.stdin.flush()

    def close(self):
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
