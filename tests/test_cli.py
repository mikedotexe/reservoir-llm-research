"""CLI end-to-end checks with isolated journals, jobs, cache, and export paths."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from reservoir_research.cli import main, around_window
from reservoir_research.store import connect


class CliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.source = self.base / "journal"
        self.source.mkdir()
        self.db = self.base / "cache/index.sqlite3"
        self.body = "Could a lantern help this question return?"
        self.entry = self.source / "moment_2026-09-06T16-00-00.txt"
        self.raw = "=== MOMENT CAPTURE ===\nTimestamp: 2026-09-06T23:00:00Z\nFill %: 68.0%\n\n" + self.body
        self.entry.write_text(self.raw, encoding="utf-8")

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--db", str(self.db), *map(str, arguments)])
        value = json.loads(stdout.getvalue()) if stdout.getvalue().strip() else None
        return status, value, stderr.getvalue()

    def index(self):
        status, value, error = self.invoke("index", "--source", f"minime={self.source}")
        self.assertEqual(status, 0, error)
        self.assertEqual(value["counts"]["included_files"], 1)

    def test_query_commands_have_usable_shapes_without_mutating_cache(self):
        self.index()
        before = self.db.read_bytes()
        status, matches, error = self.invoke("search", "lantern", "--being", "minime")
        self.assertEqual(status, 0, error)
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertIn("snippet", match)
        self.assertNotIn("raw_text", match)
        self.assertNotIn("body_text", match)
        status, questions, error = self.invoke("questions")
        self.assertEqual(status, 0, error)
        self.assertEqual(questions["candidates"][0]["text"], self.body)
        status, shown, error = self.invoke("show", match["id"][:12])
        self.assertEqual(status, 0, error)
        self.assertEqual(shown["body_text"], self.body)
        self.assertIsInstance(shown["metadata"], dict)
        self.assertNotIn("raw_text", shown)
        self.assertIsNone(shown["backend"])
        self.assertEqual(shown["prompt_available"], 0)
        status, full, error = self.invoke("show", match["id"], "--raw")
        self.assertEqual(status, 0, error)
        self.assertEqual(full["raw_text"], self.raw)
        status, recurrent, error = self.invoke("recurrence", "lantern")
        self.assertEqual(status, 0, error)
        self.assertEqual(recurrent["occurrences"], 1)
        self.assertEqual(self.db.read_bytes(), before)

    def test_around_clock_requires_zone_and_resolves_daylight_saving_explicitly(self):
        since, until, zone = around_window('2026-09-06T09:19:00', 'America/Los_Angeles')
        self.assertEqual((since, until, zone), (1788710940, 1788712140, 'America/Los_Angeles'))
        for at, zone in [('2026-09-06T09:19:00', None),
                         ('2026-09-06', 'UTC'),
                         ('2026-11-01T01:30:00', 'America/Los_Angeles'),
                         ('2026-03-08T02:30:00', 'America/Los_Angeles'),
                         ('2026-09-06T09:19:00', 'Unknown/Timezone')]:
            with self.subTest(at=at, zone=zone), self.assertRaises(ValueError):
                around_window(at, zone)
        first = around_window('2026-11-01T01:30:00-07:00', 'America/Los_Angeles')
        second = around_window('2026-11-01T01:30:00-08:00', 'America/Los_Angeles')
        self.assertEqual(second[0] - first[0], 3600)
        self.assertEqual(around_window('2026-09-06T16:19:00Z', None)[:2], (1788710940, 1788712140))
        with self.assertRaises(ValueError):
            around_window('2026-09-06T09:19:00', 'UTC', 0, 0)

    def test_around_invalid_clock_fails_before_cache_creation(self):
        for extra in ((), ('--timezone', 'America/Los_Angeles', '--before-minutes', '0', '--after-minutes', '0')):
            status, _, error = self.invoke('around', '--at', '2026-09-06T09:19:00',
                                          '--out', self.base / 'unused', *extra)
            self.assertEqual(status, 2, error)
            self.assertFalse(self.db.exists())
            self.assertFalse((self.base / 'unused').exists())

    def test_evidence_then_around_reconstructs_both_beings_and_overlapping_action(self):
        self.index()
        astrid = self.base / 'astrid-journals'
        astrid.mkdir()
        astrid_entry = astrid / 'astrid_1788735600.txt'
        astrid_entry.write_text('=== ASTRID JOURNAL ===\nMode: dialogue_live\nTimestamp: 1788735600\n\nA second perspective.\nNEXT: REMEMBER', encoding='utf-8')
        status, _, error = self.invoke('index', '--source', f'astrid={astrid}')
        self.assertEqual(status, 0, error)
        payload = {'status': 'blocked', 'reason': 'fixture guard'}
        action_source = self.base / 'captured-source-tree'
        action_source.mkdir()
        evidence_path = self.base / 'captured-evidence.json'
        evidence_path.write_text(json.dumps({
            'schema_version': 1, 'kind': 'reservoir_episode_evidence',
            'capture': {'method': 'synthetic fixture'},
            'coverage': [{'being': 'minime', 'kind': 'action', 'source_path': str(action_source),
                          'since': 1788735600, 'until': 1788735660, 'status': 'bounded_fixture',
                          'rows_examined': 1, 'rows_selected': 1}],
            'records': [{'being': 'minime', 'kind': 'action', 'source_record_id': 'fixture-action',
                         'action_id': 'fixture-action', 'occurred_at': 1788735580, 'ended_at': 1788735630,
                         'raw_next': 'RUN_PYTHON fixture.py', 'effective_action': 'run_python',
                         'status': 'blocked', 'route': 'fixture_guard', 'payload': payload,
                         'source': {'path': '/unmounted/actions.jsonl', 'locator': {'line': 1},
                                    'sha256': hashlib.sha256(json.dumps(payload).encode()).hexdigest(),
                                    'hash_basis': 'fixture json.dumps(payload) UTF-8'}}]
        }), encoding='utf-8')
        status, imported, error = self.invoke('evidence', evidence_path)
        self.assertEqual(status, 0, error)
        self.assertEqual(imported['counts']['observations_added'], 1)
        status, coverage, error = self.invoke('coverage')
        self.assertEqual(status, 0, error)
        self.assertTrue(coverage['captured_evidence']['available'])
        self.assertEqual(coverage['captured_evidence']['records_by_being_kind'][0]['records'], 1)
        self.entry.unlink()
        astrid_entry.unlink()
        before = self.db.read_bytes()
        out = self.base / 'around-report'
        args = ('around', '--at', '2026-09-06T23:00:00Z', '--before-minutes', '0', '--after-minutes', '1')
        status, exported, error = self.invoke(*args, '--out', out)
        self.assertEqual(status, 0, error)
        result = json.loads(Path(exported['json']).read_text())
        self.assertEqual({r['being'] for r in result['records'] if r['record_type'] == 'journal'}, {'astrid', 'minime'})
        action = next(r for r in result['records'] if r['kind'] == 'action')
        self.assertEqual((action['start_at'], action['end_at']), (1788735580, 1788735630))
        self.assertIn('fixture guard', Path(exported['json']).read_text())
        saved = Path(exported['markdown']).read_bytes()
        for destination in (out, self.source / 'report', action_source / 'report'):
            status, _, error = self.invoke(*args, '--out', destination)
            self.assertEqual(status, 2, error)
        self.assertEqual(Path(exported['markdown']).read_bytes(), saved)
        self.assertFalse((action_source / 'report').exists())
        self.assertEqual(self.db.read_bytes(), before)

    def test_coverage_refuses_database_or_existing_notes_as_destination(self):
        self.index()
        notes = self.base / "reader-notes.json"
        notes.write_text("Reader's work must survive.", encoding="utf-8")
        for destination in (notes, self.db):
            with self.subTest(destination=destination):
                before = destination.read_bytes()
                status, _, error = self.invoke("coverage", "--output", destination)
                self.assertEqual(status, 2, error)
                self.assertEqual(destination.read_bytes(), before)
        destination = self.base / "reports/coverage.json"
        status, report, error = self.invoke("coverage", "--output", destination)
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(destination.read_text()), report)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

    def test_registered_source_and_symlink_output_destinations_are_protected(self):
        self.index()
        before = self.entry.read_bytes()
        alias = self.base / "source-alias"
        alias.symlink_to(self.source, target_is_directory=True)
        for destination in (self.source / "report.json", alias / "report.json"):
            status, _, error = self.invoke("coverage", "--output", destination)
            self.assertEqual(status, 2, error)
            self.assertIn("source tree", error)
            self.assertFalse(destination.exists())
        status, _, error = self.invoke("sample", "--out", alias / "pack")
        self.assertEqual(status, 2, error)
        self.assertFalse((self.source / "pack").exists())
        self.assertEqual(self.entry.read_bytes(), before)

    def test_empty_coverage_uses_zero_counts_and_unknown_time_bounds(self):
        connection = connect(self.db, writable=True)
        connection.close()
        status, report, error = self.invoke("coverage")
        self.assertEqual(status, 0, error)
        counts = report["counts"]
        for field in ("entries", "prose_entries", "flagged_entries", "unknown_time", "unknown_backend",
                      "exact_prompt_entries", "question_candidates", "question_bearing_entries",
                      "generation_records", "generation_links", "exact_body_duplicate_groups", "source_aliases"):
            self.assertEqual(counts[field], 0, field)
        self.assertIsNone(counts["first_time"])
        self.assertIsNone(counts["last_time"])
        self.assertEqual(report["groups"], [])

    def test_multiple_matching_records_do_not_establish_attributed_backend_or_prompt(self):
        self.index()
        sources = self.base / "generations/2026-09-06"
        sources.mkdir(parents=True)
        for number, (backend, source) in enumerate((("recorded-backend", "adapted"), (None, None))):
            record = {"schema_version": 1, "generation_id": f"g{number}", "attempt_index": 0,
                      "created_at_unix_ms": 1788735600000, "being": "minime", "lane": "moment", "status": "ok",
                      "backend": backend, "messages_source": source,
                      "messages": [{"role": "user", "content": "What changed?"}], "response_text": self.body}
            (sources / f"gen_{number}.json").write_text(json.dumps(record), encoding="utf-8")
        status, imported, error = self.invoke("generations", "--source", f"minime={sources}")
        self.assertEqual(status, 0, error)
        self.assertEqual(imported["counts"]["records"], 2)
        status, report, error = self.invoke("coverage")
        self.assertEqual(status, 0, error)
        self.assertEqual(report["counts"]["generation_records"], 2)
        self.assertEqual(report["counts"]["unknown_backend"], 1)
        self.assertEqual(report["counts"]["exact_prompt_entries"], 0)
        status, questions, error = self.invoke("questions")
        self.assertEqual(status, 0, error)
        status, shown, error = self.invoke("show", questions["candidates"][0]["id"])
        self.assertEqual(status, 0, error)
        self.assertEqual(len(shown["generation_records"]), 2)
        self.assertIsNone(shown["backend"])
        self.assertEqual(shown["prompt_available"], 0)

    def test_sample_and_export_preserve_manifest_and_refuse_existing_pack(self):
        self.index()
        first, second = self.base / "first-pack", self.base / "second-pack"
        status, result, error = self.invoke("sample", "--per-being", "1", "--context", "0", "--out", first)
        self.assertEqual(status, 0, error)
        manifest = Path(result["files"]["manifest"])
        self.assertTrue(Path(result["files"]["reading_pack"]).is_file())
        status, exported, error = self.invoke("export", manifest, "--out", second)
        self.assertEqual(status, 0, error)
        self.assertEqual(manifest.read_bytes(), Path(exported["files"]["manifest"]).read_bytes())
        before = (second / "reading-pack.md").read_bytes()
        status, _, error = self.invoke("export", manifest, "--out", second)
        self.assertEqual(status, 2, error)
        self.assertEqual((second / "reading-pack.md").read_bytes(), before)

    def test_trail_finds_action_tail_from_cache_and_protects_destinations(self):
        self.entry.write_text(self.raw + "\n\nNEXT: RUN_PYTHON literal_probe.py", encoding="utf-8")
        self.index()
        status, matches, error = self.invoke("search", "literal_probe.py")
        self.assertEqual(status, 0, error)
        self.assertEqual(matches, [])
        self.entry.unlink()  # A trail must work from retained originals alone.
        before = self.db.read_bytes()
        arguments = ("trail", "--term", "literal_probe.py", "--being", "minime",
                     "--since", "2026-09-06T23:00:00Z", "--until", "2026-09-06T23:01:00Z")
        out = self.base / "trail"
        status, exported, error = self.invoke(*arguments, "--out", out)
        self.assertEqual(status, 0, error)
        self.assertEqual(exported["records"], 1)
        saved = Path(exported["json"]).read_bytes()
        result = json.loads(saved)
        self.assertEqual(result["records"][0]["next_raw"], "RUN_PYTHON literal_probe.py")
        self.assertEqual(result["records"][0]["matched_spans"][0]["field"], "raw_text")
        self.assertTrue(Path(exported["markdown"]).is_file())
        for destination in (out, self.source / "trail"):
            status, _, error = self.invoke(*arguments, "--out", destination)
            self.assertEqual(status, 2, error)
        self.assertEqual(Path(exported["json"]).read_bytes(), saved)
        self.assertFalse((self.source / "trail").exists())
        self.assertEqual(self.db.read_bytes(), before)

    def test_wrong_shape_manifest_reports_error_without_traceback(self):
        self.index()
        manifest = self.base / "bad-manifest.json"
        manifest.write_text("[]", encoding="utf-8")
        status, _, error = self.invoke("export", manifest, "--out", self.base / "bad-pack")
        self.assertEqual(status, 2, error)
        self.assertTrue(error.startswith("Error:"))
        self.assertFalse((self.base / "bad-pack").exists())

    def test_reparse_uses_cache_and_exposes_resonance_question_channels(self):
        body = "Could this opening question return?\n\nINBOX_REPLY literal_target\n\nCould this addressed question develop?"
        raw = "=== RESERVOIR RESONANCE ===\nTimestamp: 2026-09-06T19:29:13\nFill %: 69.1%\n\nMinime <-> Astrid resonance:\n  divergence: 1.1\n  correlation: -0.8\n  trajectory RMSD: 2.5\n\n" + body
        self.entry.write_text(raw, encoding="utf-8")
        self.index()
        connection = connect(self.db, writable=True, source_roots=[self.source])
        try:
            # Legacy cache fixture: raw wrapper was previously classified unknown.
            connection.execute("UPDATE entries SET parser_version=1,content_kind='unknown',header_text='',body_text=?", (raw,))
            connection.execute("DELETE FROM candidates")
            connection.execute("UPDATE entry_fts SET body_text=?", (raw,))
            connection.commit()
        finally:
            connection.close()
        self.entry.unlink()
        status, reparsed, error = self.invoke("reparse")
        self.assertEqual(status, 0, error)
        self.assertEqual(reparsed["parser_version"], 2)
        self.assertEqual(reparsed["counts"]["reparsed"], 1)
        status, questions, error = self.invoke("questions")
        self.assertEqual(status, 0, error)
        candidates = questions["candidates"]
        self.assertEqual([item["channel"] for item in candidates], ["pre_reply_context", "inbox_reply"])
        self.assertEqual([item["reply_target"] for item in candidates], [None, "literal_target"])
        status, shown, error = self.invoke("show", candidates[0]["id"], "--raw")
        self.assertEqual(status, 0, error)
        self.assertEqual(shown["raw_text"], raw)
        self.assertEqual(shown["body_text"], body)
        self.assertEqual(shown["lane"], "reservoir_resonance")
        self.assertEqual(shown["metadata"]["resonance_block"]["model_exposure"], "unknown")
        self.assertEqual("".join(segment["text"] for segment in shown["segments"]), body)


if __name__ == "__main__":
    unittest.main()
