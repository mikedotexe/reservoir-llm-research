"""Agent CLI boundaries; no model service or desktop data is contacted."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from reservoir_control.cli import Client, ClientError, read_descriptor, parser


class ControlTests(unittest.TestCase):
    def test_descriptor_rejects_network_redirect_targets_and_shared_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'endpoint.json'
            v = {'version': 1, 'url': 'http://127.0.0.1:54321', 'token': 'a' * 64}
            p.write_text(json.dumps(v)); p.chmod(0o600)
            self.assertEqual(read_descriptor(p)['url'], v['url'])
            for url in ['https://127.0.0.1:123', 'http://example.org:123', 'http://127.0.0.1:123@evil.test', 'http://127.0.0.1:123/x']:
                p.write_text(json.dumps({**v, 'url': url}))
                with self.assertRaises(ClientError): read_descriptor(p)
            p.write_text(json.dumps(v)); p.chmod(0o644)
            if os.name == 'posix':
                with self.assertRaises(ClientError): read_descriptor(p)
            link = Path(d) / 'link'; link.symlink_to(p)
            with self.assertRaises(ClientError): read_descriptor(link)

    def test_paths_cannot_move_credentials_to_another_host(self):
        c = Client({'url': 'http://127.0.0.1:1', 'token': 'a' * 64})
        for p in ['https://example.org', '//example.org/v1/runs', '/etc/passwd']:
            with self.assertRaises(ClientError): c.request('GET', p)

    def test_export_download_verifies_bytes_and_marks_incomplete(self):
        class Fake(Client):
            def __init__(self, content): self.content = content
            def wait(self, operation, timeout=660): return {'status':'completed', 'result':{'exportId':'op-one', 'report':{}}}
            def request(self, method, path, body=None, key=None, raw=False):
                if method == 'POST': return {'id':'op-one'}
                if path.endswith('/files'): return {'files':[{'path':'journals/test.json','bytes':2,'sha256':hashlib.sha256(b'{}').hexdigest()}]}
                return self.content
        with tempfile.TemporaryDirectory() as d:
            ok = Path(d) / 'ok'; self.assertEqual(Fake(b'{}').export('run-one', ok, None)['status'], 'completed')
            self.assertEqual((ok / 'journals/test.json').read_bytes(), b'{}')
            bad = Path(d) / 'bad'
            with self.assertRaises(ClientError): Fake(b'xx').export('run-one', bad, None)
            self.assertTrue((bad / 'INCOMPLETE.txt').exists())
            with self.assertRaises(ClientError): Fake(b'{}').export('run-one', ok, None)

    def test_interventions_are_first_class_commands(self):
        p = parser(); a = p.parse_args(['interventions', 'schedule', 'run-one', 'change.json'])
        self.assertEqual((a.command, a.action, a.file), ('interventions','schedule','change.json'))
        self.assertEqual(p.parse_args(['interventions','cancel','op-one']).operation, 'op-one')


if __name__ == '__main__': unittest.main()
