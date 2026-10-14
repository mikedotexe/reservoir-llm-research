#!/usr/bin/env python3
"""Bounded, owned loopback fixture for a real wall-time reliability run.

No language model or external service. The output directory must be new.
Control file modes: normal, hold, fail, incomplete. Holds require release-N
or expire after 70 seconds. The server expires after four hours by default.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('root', type=Path)
parser.add_argument('--lifetime-seconds', type=int, default=14400)
parser.add_argument('--latency-ms', type=int, default=200)
parser.add_argument('--maximum-requests', type=int, default=500)
args = parser.parse_args()
if not 1 <= args.lifetime_seconds <= 14400 or not 0 <= args.latency_ms <= 5000 or not 1 <= args.maximum_requests <= 1000:
    parser.error('bounded lifetime, latency and request count required')
root = args.root.resolve()
root.mkdir(parents=True, exist_ok=False)
model = 'reservoir-fixture:reliability-0.12'
lock = threading.Lock()
counter = 0
started = time.monotonic()

def log(value):
    value = {'at': time.time_ns() // 1_000_000, 'monotonicNs': time.monotonic_ns(), **value}
    with lock:
        with (root / 'requests.jsonl').open('a') as out:
            out.write(json.dumps(value, ensure_ascii=False) + '\n')
            out.flush()
            os.fsync(out.fileno())

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, value):
        data = json.dumps(value).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False

    def do_GET(self):
        log({'method': 'GET', 'path': self.path})
        self.respond(200 if self.path == '/api/tags' else 404,
                     {'models': [{'name': model, 'model': model, 'digest': 'owned-synthetic-prose'}]})

    def do_POST(self):
        global counter
        if self.path != '/api/chat':
            self.respond(404, {'error': 'owned fixture only supports /api/chat'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 1_048_576:
                raise ValueError('request bound')
            raw = self.rfile.read(size)
            body = json.loads(raw)
            if body['model'] != model or body['stream'] is not False or body['options']['num_predict'] != 256 or body['options']['temperature'] != 0 or 'format' in body:
                raise ValueError('unexpected generation configuration')
            prompt = body['messages'][0]['content']
            if not isinstance(prompt, str):
                raise ValueError('prompt must be text')
        except (ValueError, KeyError, IndexError, TypeError) as error:
            log({'rejected': str(error)})
            self.respond(400, {'error': str(error)})
            return
        with lock:
            counter += 1
            request = counter
        if request > args.maximum_requests:
            log({'requestLimitReached': request})
            self.respond(503, {'error': 'owned fixture request limit'})
            return
        try:
            mode = json.loads((root / 'control.json').read_text()).get('mode', 'normal')
        except (FileNotFoundError, json.JSONDecodeError):
            mode = 'normal'
        log({'method': 'POST', 'path': self.path, 'request': request,
             'mode': mode, 'bodySha256': hashlib.sha256(raw).hexdigest(), 'body': body})
        time.sleep(args.latency_ms / 1000)
        if mode == 'hold':
            deadline = time.monotonic() + 70
            while time.monotonic() < deadline and not (root / f'release-{request}').exists():
                time.sleep(.05)
        if mode == 'fail':
            self.respond(503, {'error': 'Owned synthetic failure'})
            return
        step = re.search(r'Global step (\d+)', prompt)
        step = step.group(1) if step else 'unknown'
        prose = (f'At step {step}, I notice the signed recurrent coordinates and the separate sensory fill. '
                 f'This is synthetic journal {request}. I will compare the next retained observation '
                 'after this writing returns as held input. Forcing, noise and regulation also change the state.')
        sent = self.respond(200, {'done': mode != 'incomplete', 'model': model,
                                 'done_reason': 'stop', 'eval_count': 63,
                                 'message': {'role': 'assistant', 'content': prose}})
        log({'response': request, 'textSha256': hashlib.sha256(prose.encode()).hexdigest(),
             'complete': mode != 'incomplete', 'socketWriteCompleted': sent})

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
server.daemon_threads = True
identity = {'endpoint': f'http://127.0.0.1:{server.server_port}', 'model': model,
            'pid': os.getpid(), 'startedAtMs': time.time_ns() // 1_000_000,
            'lifetimeSeconds': args.lifetime_seconds, 'latencyMs': args.latency_ms,
            'maximumRequests': args.maximum_requests, 'synthetic': True}
(root / 'endpoint.json').write_text(json.dumps(identity, indent=2) + '\n')
log({'lifecycle': 'started', **identity})
print(json.dumps(identity), flush=True)

def request_stop(signum=None, _frame=None):
    log({'lifecycle': 'stopRequested', 'signal': signum})
    threading.Thread(target=server.shutdown, daemon=True).start()

signal.signal(signal.SIGTERM, request_stop)
signal.signal(signal.SIGINT, request_stop)
deadline = threading.Timer(args.lifetime_seconds, request_stop)
deadline.daemon = True
deadline.start()
try:
    server.serve_forever(poll_interval=.5)
finally:
    deadline.cancel()
    server.server_close()
    log({'lifecycle': 'stopped', 'elapsedSeconds': time.monotonic() - started, 'requests': counter})
