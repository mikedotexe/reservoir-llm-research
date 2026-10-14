#!/usr/bin/env python3
"""Owned loopback-only qualification fixture. No model or external service.

Usage: python3 owned_provider.py NEW_QA_DIRECTORY
The controller may write control.json with mode normal/hold/fail/incomplete.
For hold, creating release-N permits only request N to finish.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=True)
model = 'reservoir-fixture:0.12'
lock = threading.Lock()
counter = 0

def log(value):
    with lock:
        with (root / 'requests.jsonl').open('a') as out:
            out.write(json.dumps(value, ensure_ascii=False) + '\n')
            out.flush()
            os.fsync(out.fileno())

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, value):
        body = json.dumps(value).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        log({'method': 'GET', 'path': self.path, 'at': time.time_ns() // 1_000_000})
        self.respond(200 if self.path == '/api/tags' else 404,
                     {'models': [{'name': model, 'model': model, 'digest': 'owned-synthetic-prose'}]})

    def do_POST(self):
        global counter
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 < size <= 1_048_576:
            self.respond(413, {'error': 'request bound'})
            return
        raw = self.rfile.read(size)
        body = json.loads(raw)
        with lock:
            counter += 1
            request = counter
        try:
            mode = json.loads((root / 'control.json').read_text()).get('mode', 'normal')
        except (FileNotFoundError, json.JSONDecodeError):
            mode = 'normal'
        log({'method': 'POST', 'path': self.path, 'request': request,
             'mode': mode, 'at': time.time_ns() // 1_000_000,
             'bodySha256': hashlib.sha256(raw).hexdigest(), 'body': body})
        if mode == 'hold':
            deadline = time.monotonic() + 70
            while time.monotonic() < deadline and not (root / f'release-{request}').exists():
                time.sleep(.05)
        if mode == 'fail':
            self.respond(503, {'error': 'Owned synthetic failure'})
            return
        prompt = body['messages'][0]['content']
        step = re.search(r'Global step (\d+)', prompt)
        step = step.group(1) if step else 'unknown'
        text = (f'At step {step}, I notice the signed recurrent coordinates and the separate sensory fill. '
                f'This is synthetic journal {request}. I will compare the next retained observation '
                'after this writing returns as held input. Forcing, noise and regulation also change the state.')
        assert body['model'] == model
        assert body['stream'] is False
        assert body['options']['num_predict'] == 256
        assert body['options']['temperature'] == 0
        assert 'format' not in body
        self.respond(200, {'done': mode != 'incomplete', 'model': model,
                          'done_reason': 'stop', 'eval_count': 63,
                          'message': {'role': 'assistant', 'content': text}})
        log({'response': request, 'textSha256': hashlib.sha256(text.encode()).hexdigest(),
             'at': time.time_ns() // 1_000_000, 'complete': mode != 'incomplete'})

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
(root / 'endpoint.json').write_text(json.dumps({'endpoint': f'http://127.0.0.1:{server.server_port}', 'model': model, 'pid': os.getpid()}, indent=2)+'\n')
print(json.dumps({'endpoint': f'http://127.0.0.1:{server.server_port}', 'model': model, 'pid': os.getpid()}), flush=True)
server.serve_forever()
