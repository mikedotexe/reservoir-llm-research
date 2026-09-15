"""Bounded capture checks use temporary sources; no SSH or live data access."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from probes.episode_source_capture import bounded_query, capture_astrid, stamp


class EpisodeCaptureTests(unittest.TestCase):
    def test_clock_uses_zone_and_rejects_ambiguous_or_nonexistent_times(self):
        self.assertEqual(stamp('2026-09-06T09:19:00', 'America/Los_Angeles'), 1788711540)
        for value in ('2026-11-01T01:30:00', '2026-03-08T02:30:00'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Ambiguous or nonexistent'):
                stamp(value, 'America/Los_Angeles')
        first = stamp('2026-11-01T01:30:00-07:00', 'America/Los_Angeles')
        second = stamp('2026-11-01T01:30:00-08:00', 'America/Los_Angeles')
        self.assertEqual(second - first, 3600)
        for value in ('NaN', 'inf', '-inf'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'finite'):
                stamp(value)

    def test_indexed_query_limit_and_scan_refusal(self):
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute('CREATE TABLE events (id INTEGER PRIMARY KEY, body TEXT)')
            conn.executemany('INSERT INTO events VALUES (?, ?)', [(i, 'body') for i in range(5)])
            with self.assertRaisesRegex(ValueError, 'no indexed SEARCH'):
                bounded_query(conn, 'SELECT * FROM events', [], 2)
            rows, provenance = bounded_query(conn, 'SELECT * FROM events WHERE id >= ? ORDER BY id LIMIT ?', [0, 3], 2)
            self.assertEqual([r['id'] for r in rows], [0, 1])
            self.assertTrue(provenance['truncated'])
            self.assertEqual(provenance['rows_returned_before_limit'], 3)
            self.assertTrue(any('SEARCH ' in row[3] for row in provenance['query_plan']))

    def test_astrid_schema_read_failure_closes_connection_and_records_unavailability(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve() / 'astrid/capsules/spectral-bridge/workspace'
            workspace.mkdir(parents=True)
            database = workspace / 'bridge.db'
            database.write_bytes(b'This is deliberately not a SQLite database.')
            args = SimpleNamespace(remote_base=str(Path(directory).resolve()), since_epoch=100,
                                   until_epoch=200, log_bytes=100000, max_log_lines=100, max_threads=4)
            records, coverages, opened = [], [], []
            real_connect = sqlite3.connect
            def tracked_connect(*args, **kwargs):
                connection = real_connect(*args, **kwargs)
                opened.append(connection)
                self.addCleanup(connection.close)
                return connection
            with patch('probes.episode_source_capture.sqlite3.connect', side_effect=tracked_connect):
                capture_astrid(args, records, coverages)
            self.assertEqual(len(opened), 1)
            with self.assertRaisesRegex(sqlite3.ProgrammingError, 'closed database'):
                opened[0].execute('SELECT 1')
            self.assertEqual(records, [])
            self.assertTrue(all(item['status'] == 'unavailable' for item in coverages))
            self.assertTrue(all('not a database' in ' '.join(item['notes']) for item in coverages))

    def capture_fixture(self, directory, events, *, byte_cap=100000, line_cap=100):
        path = Path(directory) / 'astrid/capsules/spectral-bridge/workspace/action_threads/threads/th_test/events.jsonl'
        path.parent.mkdir(parents=True)
        source_bytes = b''.join((json.dumps(event) + '\n').encode() for event in events)
        path.write_bytes(source_bytes)
        args = SimpleNamespace(remote_base=directory, since_epoch=100, until_epoch=200,
                               log_bytes=byte_cap, max_log_lines=line_cap, max_threads=4)
        records, coverages = [], []
        before = path.stat()
        capture_astrid(args, records, coverages)
        self.assertEqual(path.read_bytes(), source_bytes)
        self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
        action_coverage = next(c for c in coverages if c['kind'] == 'action')
        return records, action_coverage, source_bytes

    def test_full_log_stream_finds_intervals_without_chronological_assumption(self):
        events = [
            {'action_id': 'later', 'started_at': 210, 'ended_at': 211},
            {'action_id': 'overlap', 'started_at': 80, 'ended_at': 120},
            {'action_id': 'inside', 'started_at': 150, 'ended_at': 155, 'pre_state': {'lambda1': 4.7}},
            {'action_id': 'earlier_unknown_end', 'started_at': 70},
        ]
        with tempfile.TemporaryDirectory() as directory:
            records, covered, raw = self.capture_fixture(directory, events)
        self.assertEqual([r['action_id'] for r in records if r['kind'] == 'action'], ['overlap', 'inside'])
        self.assertEqual(covered['status'], 'complete_captured_file')
        self.assertEqual((covered['rows_examined'], covered['rows_selected']), (4, 2))
        self.assertEqual(covered['scan_end'], len(raw))
        self.assertEqual(covered['scanned_prefix_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertFalse(covered['source_changed_during_read'])
        telemetry = next(r for r in records if r['kind'] == 'telemetry')
        self.assertEqual(telemetry['metrics']['lambda1_ambiguous'], 4.7)
        self.assertIn('not independently verified', telemetry['metrics']['measurement_note'])

    def test_line_and_byte_caps_cannot_claim_complete_source(self):
        events = [{'action_id': str(i), 'started_at': 120 + i, 'ended_at': 121 + i} for i in range(3)]
        with tempfile.TemporaryDirectory() as directory:
            _, covered, _ = self.capture_fixture(directory, events, line_cap=1)
        self.assertEqual(covered['status'], 'partial')
        self.assertEqual(covered['rows_examined'], 1)
        self.assertIn('cap', covered['stopped_reason'])
        with tempfile.TemporaryDirectory() as directory:
            _, covered, raw = self.capture_fixture(directory, events, byte_cap=20)
        self.assertEqual(covered['status'], 'partial')
        self.assertEqual(covered['scan_end'], 20)
        self.assertEqual(covered['scanned_prefix_sha256'], hashlib.sha256(raw[:20]).hexdigest())
        self.assertEqual(covered['parse_errors'], 1)


if __name__ == '__main__':
    unittest.main()
