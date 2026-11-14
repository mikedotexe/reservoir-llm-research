#!/usr/bin/env python3
"""Owned loopback-only fixture for native inquiry/probe recovery qualification.

No model is invoked. The first reply opens an inquiry and sends a custom input
probe while withholding text. The second continues the inquiry and sends text;
its first encoding deliberately fails. The third closes the inquiry. All exact
requests and responses are retained in a newly created private output directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import signal

WRITER = 'inquiry-fixture:local'
ENCODER = 'inquiry-embedding:local'
VECTOR = [0.5] + [0.0] * 47
REPLIES = [
    'I will retain a question about the response to a small, specifically chosen input.\n\n'
    'INQUIRY: OPEN both "How does the recorded state change after this input probe while journal input is withheld?"\n'
    'WITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE ' + json.dumps(VECTOR, separators=(',', ':')),
    'I am returning to the retained question with its baseline and identified earlier writing.\n\n'
    'INQUIRY: CONTINUE\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE',
    'This scripted qualification has supplied the next evidence packet. I am closing the question explicitly.\n\n'
    'INQUIRY: CLOSE\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE',
]


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    counts = {'writing': 0, 'embedding': 0, 'inventory': 0}

    def publish(name, value):
        (output / name).write_text(json.dumps(value, indent=2) + '\n')

    def record(value):
        with (output / 'requests.jsonl').open('a') as stream:
            stream.write(json.dumps({'observedAtUtc': now(), **value}) + '\n')
        publish('counts.json', counts)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_json(self, status, payload, request=None):
            raw = json.dumps(payload).encode()
            record({'method': self.command, 'path': self.path, 'status': status,
                    'request': request, 'response': payload})
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path != '/api/tags':
                self.send_json(404, {'error': 'Unknown fixture route'})
                return
            counts['inventory'] += 1
            models = []
            for name, capability in ((WRITER, 'completion'), (ENCODER, 'embedding')):
                models.append({'name': name, 'model': name, 'digest': hashlib.sha256(name.encode()).hexdigest(),
                               'size': 1, 'modified_at': '2026-11-14T00:00:00Z',
                               'details': {'format': 'fixture', 'family': 'fixture', 'parameter_size': '0', 'quantization_level': 'fixture'},
                               'capabilities': [capability]})
            self.send_json(200, {'models': models})

        def do_POST(self):
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 1_048_576:
                self.send_json(413, {'error': 'Bounded fixture request required'})
                return
            try:
                request = json.loads(self.rfile.read(size))
            except (ValueError, UnicodeError):
                self.send_json(400, {'error': 'Expected JSON'})
                return
            if self.path == '/api/chat' and request.get('model') == WRITER:
                counts['writing'] += 1
                ordinal = counts['writing']
                if ordinal > len(REPLIES):
                    self.send_json(409, {'error': 'All three planned fixture replies have been used'}, request)
                    return
                self.send_json(200, {'model': WRITER, 'done': True, 'done_reason': 'stop',
                    'eval_count': len(REPLIES[ordinal - 1].split()),
                    'message': {'role': 'assistant', 'content': REPLIES[ordinal - 1]}}, request)
            elif self.path == '/api/embed' and request.get('model') == ENCODER:
                counts['embedding'] += 1
                if counts['embedding'] == 1:
                    self.send_json(503, {'error': 'Deliberate first encoding failure; retry must reuse the same saved writing'}, request)
                else:
                    self.send_json(200, {'model': ENCODER, 'embeddings': [[(i + 1) / 768 for i in range(768)]]}, request)
            else:
                self.send_json(404, {'error': 'Unknown fixture route or exact model name'}, request)

    server = HTTPServer(('127.0.0.1', 0), Handler)
    ready = {'createdAtUtc': now(), 'pid': os.getpid(), 'endpoint': f'http://127.0.0.1:{server.server_port}',
             'writer': WRITER, 'encoder': ENCODER, 'modelsContacted': False, 'scriptedReplies': 3}
    publish('ready.json', ready)
    publish('planned-replies.json', REPLIES)
    print(json.dumps(ready), flush=True)
    def stop_signal(*_):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop_signal)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        publish('stopped.json', {'stoppedAtUtc': now(), 'counts': counts})


if __name__ == '__main__':
    main()
