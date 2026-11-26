"""Owned helper process, structured events and bounded pause/stop control."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time


class HelperSession:
    def __init__(self, notify, language='ru', vortex_path='', check_only=False):
        self.notify = notify
        self.language = language
        self.vortex_path = vortex_path
        self.check_only = check_only
        self.process = None
        self.lock = threading.Lock()
        self.control_lock = threading.Lock()
        self.stop_requested = threading.Event()
        self.temp = None
        self.sequence = 0
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            raise RuntimeError('Session is already running')
        self.thread = threading.Thread(target=self._run, name='vortex-helper-session', daemon=True)
        self.thread.start()

    def _run(self):
        try:
            with tempfile.TemporaryDirectory(prefix='vortex-helper-') as folder:
                self.temp = Path(folder)
                powershell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
                command = [str(powershell), '-NoProfile', '-STA', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                           '-File', str(Path(__file__).with_name('Vortex-download-helper.ps1')),
                           '-Language', self.language, '-JsonEvents', '-ControlPath', str(self.temp / 'control.txt')]
                if self.vortex_path:
                    command += ['-VortexPath', self.vortex_path]
                if self.check_only:
                    command += ['-CheckOnly']
                with self.lock:
                    self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                    creationflags=subprocess.CREATE_NO_WINDOW)
                    process = self.process
                if self.stop_requested.is_set():
                    process.terminate()
                diagnostics = []
                for raw in process.stdout:
                    line = raw.decode('utf-8-sig', errors='replace').strip()
                    try:
                        value = json.loads(line)
                        if isinstance(value, dict) and 'type' in value:
                            self.notify(value)
                            continue
                    except ValueError:
                        pass
                    diagnostics.append(line)
                    diagnostics = diagnostics[-12:]
                code = process.wait()
                process.stdout.close()
                if code and not self.stop_requested.is_set():
                    self.notify(dict(type='error', data={'message': '\n'.join(diagnostics)[-2000:]}))
        except Exception as error:
            self.notify(dict(type='error', data={'message': str(error)}))
        finally:
            with self.lock:
                if self.process and self.process.poll() is None:
                    self.process.terminate()
                self.process = None
            self.temp = None
            self.notify(dict(type='ended', data={}))

    def control(self, action):
        if action not in {'pause', 'resume', 'stop'}:
            raise ValueError('Invalid helper action')
        if action == 'stop':
            self.stop_requested.set()
        with self.control_lock:
            if self.temp and self.temp.is_dir():
                self.sequence += 1
                pending = self.temp / 'control.tmp'
                try:
                    pending.write_text(f'{self.sequence}|{action}', encoding='utf-8')
                    pending.replace(self.temp / 'control.txt')
                except FileNotFoundError:
                    pass  # The session ended between the directory check and this write.

    def stop(self, wait=False):
        self.control('stop')
        def finish():
            if self.thread:
                self.thread.join(4)
            with self.lock:
                if self.process and self.process.poll() is None:
                    self.process.terminate()
        if wait:
            finish()
        else:
            threading.Thread(target=finish, name='stop-owned-helper', daemon=True).start()
