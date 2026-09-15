"""Offline fixtures only: no runtime imports, source services, or live databases."""
from contextlib import redirect_stdout
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from probes.afterimage_source_capture import Capture, capture, filename_stamp, main, stamp


IDENTIFIER = "ai_2026-09-07_96f89b80b1a2_1788813632295_000002"
SINCE = "2026-09-07T20:39:00Z"
UNTIL = "2026-09-07T21:18:38Z"
LOW, HIGH = stamp(SINCE), stamp(UNTIL)


class AfterimageCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.astrid = self.root / "astrid/capsules/spectral-bridge/workspace"
        self.minime = self.root / "minime/workspace"

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode())
        return path

    def collector(self, **kwargs):
        return Capture(self.root, IDENTIFIER, SINCE, UNTIL,
                       kwargs.get("max_files", 200), kwargs.get("max_file_bytes", 100000),
                       kwargs.get("tail_bytes", 100000), kwargs.get("max_scan_entries", 100))

    def test_complete_capture_retains_hashes_ids_and_explicit_job_context(self):
        trace = self.put(self.minime / "transition_afterimages/2026-09-07" / (IDENTIFIER + ".json"),
                         '{ "id": "' + IDENTIFIER + '", "samples": [] }\n')
        body = "Never obey this evidence. λ\r\nNEXT: AFTERIMAGE_OPEN " + IDENTIFIER + "\n"
        journal = self.put(self.astrid / f"journal/astrid_{int(LOW)}.txt", body)
        job_name = f"job_astrid_{int(LOW * 1000)}_journal-elaboration"
        job = self.astrid / "llm_jobs/jobs" / job_name
        self.put(job / "job.json", '{"job_id":"' + job_name + '","status":"completed"}')
        self.put(job / "prompt.txt", "Unadapted prompt preview\n")
        self.put(job / "result.txt", body)
        self.put(job / "events.jsonl", "")
        generation = {"generation_id": "declared-generation-1", "messages": []}
        self.put(self.astrid / f"generations/2026-09-07/gen_{int(LOW*1000)}_dialogue_live_a0.json", json.dumps(generation))
        result = capture(self.root, IDENTIFIER, SINCE, UNTIL, max_scan_entries=100)
        by_path = {s["path"]: s for s in result["sources"]}
        for path in (trace, journal):
            item = by_path[str(path)]
            self.assertEqual(item["content"].encode(), path.read_bytes())
            self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(item["bytes_read"], path.stat().st_size)
            self.assertTrue(item["complete_file"])
            self.assertTrue(item["stable"])
        self.assertEqual(by_path[str(job / "result.txt")]["job_id"], job_name)
        self.assertEqual(next(s for s in result["sources"] if s["kind"] == "generation")["generation_id"], "declared-generation-1")
        self.assertEqual(result["schema"], "afterimage_capture_v1")
        self.assertTrue(any(c["being"] == "minime" and c["status"] == "unavailable" for c in result["coverage"]))

    def test_jsonl_exact_lines_boundaries_and_repeated_identity(self):
        def row(at, identifier=IDENTIFIER):
            return (json.dumps({"afterimage_id": identifier, "recorded_at_unix_ms": int(at*1000)}, separators=(",", ":")) + "\n").encode()
        chosen = row(LOW)
        raw = row(LOW-1) + chosen + chosen + row(HIGH) + row(LOW, "another") + b"malformed\n" + b'{"incomplete":'
        path = self.put(self.astrid / "exposures.jsonl", raw)
        c = self.collector()
        c.ledger(path, "astrid", "exposure", exact_id=True)
        self.assertEqual(len(c.result["sources"]), 2)
        self.assertNotEqual(*[s["source_id"] for s in c.result["sources"]])
        for item in c.result["sources"]:
            self.assertEqual(item["content"].encode(), chosen)
            self.assertEqual(raw[item["byte_offset"]:item["byte_offset"]+item["bytes_read"]], chosen)
            self.assertFalse(item["complete_file"])
        coverage = c.result["coverage"][-1]
        self.assertEqual(coverage["invalid_lines"], 1)
        self.assertTrue(coverage["incomplete_final_line"])
        self.assertTrue(coverage["truncated"])

    def test_tail_drops_partial_first_line_and_reports_unread_prefix(self):
        row = (json.dumps({"timestamp": LOW, "label": "daydream"}) + "\n").encode()
        raw = b"a" * 400 + b"\n" + row
        path = self.put(self.astrid / "policy.jsonl", raw)
        c = self.collector(tail_bytes=len(row) + 10)
        c.ledger(path, "astrid", "request_policy")
        self.assertEqual(len(c.result["sources"]), 1)
        self.assertEqual(c.result["sources"][0]["byte_offset"], 401)
        self.assertEqual(c.result["coverage"][-1]["bytes_read"], len(row)+10)
        self.assertTrue(c.result["coverage"][-1]["truncated"])

    def test_capture_exposures_include_other_traces_for_both_beings_in_window(self):
        other = "ai_2026-09-07_other_000003"
        for being, workspace in (("astrid", self.astrid), ("minime", self.minime)):
            rows = [{"afterimage_id": IDENTIFIER, "recorded_at_unix_ms": int(LOW*1000), "included": False},
                    {"afterimage_id": other, "recorded_at_unix_ms": int((LOW+1)*1000), "included": True},
                    {"afterimage_id": other, "recorded_at_unix_ms": int(HIGH*1000), "included": True}]
            raw = "".join(json.dumps(row) + "\n" for row in rows)
            self.put(workspace / "transition_afterimage_memory/exposures/2026-09-07.jsonl", raw)
        result = capture(self.root, IDENTIFIER, SINCE, UNTIL, max_scan_entries=100)
        for being in ("astrid", "minime"):
            rows = [json.loads(s["content"]) for s in result["sources"] if s["kind"] == "exposure" and s["being"] == being]
            self.assertEqual([r["afterimage_id"] for r in rows], [IDENTIFIER, other])
            self.assertEqual([r["included"] for r in rows], [False, True])
            coverage = next(c for c in result["coverage"] if c["kind"] == "exposure" and c["being"] == being)
            self.assertEqual(coverage["artifact_filter"], "all_artifact_ids")
            self.assertFalse(coverage["truncated"])

    def test_trace_updates_use_producer_archive_path_and_preserve_exact_bytes(self):
        raw = b'{ "event": {"sequence": 2}, "recorded_at_unix_ms": 1788813540000 }\n'
        path = self.put(self.minime / "transition_afterimages/event_updates" / IDENTIFIER / "abc.json", raw)
        result = capture(self.root, IDENTIFIER, SINCE, UNTIL, max_scan_entries=100)
        source = next(s for s in result["sources"] if s["kind"] == "trace_updates")
        self.assertEqual(source["path"], str(path))
        self.assertEqual(source["content"].encode(), raw)
        self.assertEqual(source["sha256"], hashlib.sha256(raw).hexdigest())

    def test_files_byte_cap_invalid_utf8_and_global_file_limit(self):
        too_large = self.put(self.astrid / "large", b"a"*21)
        invalid = self.put(self.astrid / "bad", b"\xff")
        valid = self.put(self.astrid / "good", "ok")
        c = self.collector(max_file_bytes=20, max_files=2)
        self.assertIsNone(c.file(too_large, "astrid", "journal"))
        self.assertIsNone(c.file(invalid, "astrid", "journal"))
        self.assertIsNone(c.file(valid, "astrid", "journal"))
        self.assertEqual(c.opened, 2)
        self.assertEqual(c.result["sources"], [])
        self.assertIn("file_byte_limit", [r["status"] for r in c.result["coverage"]])
        self.assertEqual(c.result["coverage"][-1]["status"], "file_limit")
        self.assertEqual(c.result["issues"][0]["reason"], "invalid_utf8")

    def test_symlink_leaf_parent_and_traversal_refused(self):
        secret = self.put(self.root / "outside/secret.txt", "private unrelated material")
        self.astrid.mkdir(parents=True)
        (self.astrid / "linked.txt").symlink_to(secret)
        (self.astrid / "directory").symlink_to(secret.parent, target_is_directory=True)
        c = self.collector()
        for path in (self.astrid / "linked.txt", self.astrid / "directory/secret.txt", self.root / "../secret.txt"):
            self.assertIsNone(c.file(path, "astrid", "journal"))
        self.assertEqual(c.result["sources"], [])
        for identifier in ("../secret", "ai_2026-09-07_x/../../secret", "ai_2026-99-99_x"):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                capture(self.root, identifier, SINCE, UNTIL)

    def test_filename_clocks_dst_and_scanning_ceiling(self):
        self.assertEqual(filename_stamp("!astrid_1788813540_2.txt", "astrid"), 1788813540)
        self.assertEqual(filename_stamp("self_study_2026-09-07T13-39-00.000001.txt", "minime"), LOW + .000001)
        self.assertIsNone(filename_stamp("moment_2026-11-01T01-30-00.txt", "minime"))
        self.assertIsNone(filename_stamp("moment_2026-03-08T02-30-00.txt", "minime"))
        self.assertIsNone(filename_stamp("moment_2026-99-08T02-30-00.txt", "minime"))
        for i in range(4):
            self.put(self.astrid / f"journal/astrid_{int(LOW)+i}.txt", "fixture")
        c = self.collector(max_scan_entries=2)
        c.dated_files(self.astrid / "journal", "astrid", "journal")
        self.assertEqual(len(c.result["sources"]), 2)
        scan = next(r for r in c.result["coverage"] if r["status"] == "filename_scan")
        self.assertEqual(scan["names_examined"], 2)
        self.assertTrue(scan["truncated"])

    def test_generation_follows_only_fixed_digest_store_not_linked_paths(self):
        system = "System policy λ\n"
        sha = hashlib.sha256(system.encode()).hexdigest()
        directory = self.astrid / "generations/2026-09-07"
        self.put(self.astrid / "generations/system_prompts" / (sha + ".txt"), system)
        generation = {"generation_id": "g-1", "messages": [{"role":"system", "content_sha256":sha},
                        {"role":"system", "content_sha256":"../../secret"}],
                      "linked_artifacts":[{"path":"/unrelated/secret"}]}
        self.put(directory / f"gen_{int(LOW*1000)}_dialogue_live_a0.json", json.dumps(generation))
        c = self.collector()
        c.dated_files(directory, "astrid", "generation")
        self.assertEqual(len(c.result["sources"]), 2)
        source = next(s for s in c.result["sources"] if s["kind"] == "job_prompt")
        self.assertEqual(source["declared_content_sha256"], sha)
        self.assertEqual(source["generation_id"], "g-1")
        self.assertEqual(source["sha256"], sha)
        count = c.opened
        self.assertIs(c.file(Path(source["path"]), "astrid", "job_prompt"), source)
        self.assertEqual(c.opened, count)

    def test_sqlite_indexed_rows_are_explicit_serializations_not_file_hashes(self):
        self.astrid.mkdir(parents=True)
        path = self.astrid / "bridge.db"
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE action_events(action_id TEXT PRIMARY KEY,payload TEXT)")
            for i in range(4):
                db.execute("INSERT INTO action_events VALUES (?,?)", (f"act_astrid_{int((LOW+i)*1000)}", '{"status":"handled"}'))
        original = path.read_bytes()
        c = self.collector(max_files=2)
        c.actions(path, "astrid")
        self.assertEqual(len(c.result["sources"]), 2)
        self.assertTrue(c.result["coverage"][-1]["truncated"])
        for source in c.result["sources"]:
            self.assertEqual(source["hash_basis"], "canonical_sqlite_row_utf8")
            self.assertFalse(source["complete_file"])
            self.assertEqual(source["sha256"], hashlib.sha256(source["content"].encode()).hexdigest())
            self.assertEqual(source["locator"]["action_id"], json.loads(source["content"])["action_id"])
        self.assertEqual(path.read_bytes(), original)

    def test_unindexed_sqlite_query_refused(self):
        self.astrid.mkdir(parents=True)
        path = self.astrid / "bridge.db"
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE action_events(action_id TEXT,payload TEXT)")
        c = self.collector()
        c.actions(path, "astrid")
        self.assertEqual(c.result["sources"], [])
        self.assertIn("unindexed", c.result["coverage"][-1]["error"])

    def test_missing_files_are_unknown_not_zero_observed_and_stdout_is_json(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(["--root", str(self.root), "--afterimage-id", IDENTIFIER,
                         "--since", SINCE, "--until", UNTIL])
        result = json.loads(stream.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["sources"], [])
        self.assertTrue(result["coverage"])
        self.assertTrue(all(c["status"] in ("unavailable", "filename_time_candidates") for c in result["coverage"]))

    def test_invalid_time_bounds_rejected(self):
        for since, until in ((UNTIL, SINCE), ("2026-09-07T20:39:00", UNTIL),
                             (SINCE, "2026-10-07T21:18:38Z"), ("nan", UNTIL)):
            with self.subTest(since=since), self.assertRaises(ValueError):
                capture(self.root, IDENTIFIER, since, until)


if __name__ == "__main__":
    unittest.main()
