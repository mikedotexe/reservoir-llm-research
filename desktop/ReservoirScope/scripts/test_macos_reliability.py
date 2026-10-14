"""Bounded passive sampler tests; synthetic fixtures and this test process only."""
import ctypes
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import macos_reliability as m


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scope-reliability-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.session = self.root / "owned-session"
        self.session.mkdir()
        self.manifest = {"format": "reservoir-sustained-bundle-v1", "sessionId": self.session.name, "generation": "1", "revision": "3", "step": 30, "durableStep": 30, "journalCount": 1, "segmentCount": 2, "phase": "running", "config": {"private": "excluded"}, "diagnostics": ["not collected"]}
        (self.session / "manifest.json").write_text(json.dumps(self.manifest))

    def test_manifest_collects_only_allowlisted_scalars(self):
        result = m.manifest_snapshot(self.session)
        self.assertEqual(result["durableStep"], 30)
        self.assertEqual(result["sha256"], m.sha((self.session / "manifest.json").read_bytes()))
        self.assertNotIn("config", result)
        self.assertNotIn("diagnostics", result)

    def test_manifest_wrong_identity_and_oversize_are_rejected(self):
        self.manifest["sessionId"] = "different"
        path = self.session / "manifest.json"
        path.write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError):
            m.manifest_snapshot(self.session)
        path.write_bytes(b"x" * (m.MANIFEST_LIMIT + 1))
        with self.assertRaises(ValueError):
            m.manifest_snapshot(self.session)

    @unittest.skipUnless(os.name == "posix", "POSIX O_NOFOLLOW symlink-read guarantee")
    def test_manifest_symlink_cannot_read_external_content(self):
        outside = self.root / "outside"
        outside.write_text("private contents")
        path = self.session / "manifest.json"
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises(OSError):
            m.manifest_snapshot(self.session)

    @unittest.skipUnless(os.name == "posix", "POSIX directory descriptors and allocated-block accounting")
    def test_disk_counts_metadata_without_opening_journals(self):
        directory = self.session / "journals"
        directory.mkdir()
        (directory / "one.json").write_bytes(b"secret" * 10)
        with patch.object(m, "read_regular", side_effect=AssertionError("No content reads")):
            result = m.disk_snapshot(self.session)
        self.assertTrue(result["complete"])
        self.assertEqual(result["fileCount"], 2)
        self.assertEqual(result["logicalBytes"], 60 + (self.session / "manifest.json").stat().st_size)
        self.assertGreater(result["allocatedBytes"], 0)

    @unittest.skipUnless(os.name == "posix", "POSIX no-follow directory-descriptor traversal")
    def test_disk_symlink_and_nested_directory_fail_coverage(self):
        outside = self.root / "external"
        outside.mkdir()
        (outside / "unrelated").write_bytes(b"x" * 10000)
        (self.session / "journals").symlink_to(outside)
        (self.session / "unexpected").mkdir()
        result = m.disk_snapshot(self.session)
        self.assertFalse(result["complete"])
        self.assertEqual(result["fileCount"], 1)

    @unittest.skipUnless(os.name == "posix", "POSIX directory-descriptor traversal")
    def test_disk_count_bound_is_explicit(self):
        (self.session / "extra").write_text("one")
        result = m.disk_snapshot(self.session, max_entries=1)
        self.assertFalse(result["complete"])
        self.assertIn("bound", result["errors"][0])

    def fixture(self, complete=True):
        rows = [{"type": "header", "schema": m.SCHEMA, "monotonicNs": "1000000000", "intervalSeconds": 15, "process": {"pid": 42}}]
        for i in range(4):
            rows.append({"type": "sample", "sequence": i, "elapsedSeconds": i * 15, "monotonicNs": str((1 + i * 15) * 10**9), "wallEpochNs": str((100 + i * 15) * 10**9), "process": {"rssBytes": 100 + i * 10, "cpuIntervalPercent": i, "fdCount": 3, "threadCount": 2}, "manifest": {**self.manifest, "durableStep": i * 30}, "disk": {"complete": i != 0, "logicalBytes": i * 100}, "errors": []})
        if complete:
            rows.append({"type": "footer", "sampleCount": 4, "status": "completed"})
        path = self.root / "samples.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return path, rows

    def test_analysis_slope_window_and_incomplete_disk(self):
        path, _ = self.fixture()
        result = m.analyze_file(path, 15, 30)
        self.assertEqual(result["coverage"]["selectedSampleCount"], 2)
        self.assertEqual(result["metrics"]["rssBytes"]["leastSquaresChangePerHour"], 2400)
        self.assertEqual(result["manifestProgress"]["last"]["durableStep"], 60)
        self.assertTrue(result["measurementOnly"])
        all_result = m.analyze_file(path)
        self.assertEqual(all_result["metrics"]["logicalBytes"]["count"], 3)
        self.assertEqual(all_result["coverage"]["incompleteDiskScans"], 1)

    def test_numeric_window_excludes_crossing_cpu_intervals_only(self):
        path, rows = self.fixture()
        for row in rows:
            if row.get("type") == "sample":
                row["process"]["cpuTotalNanoseconds"] = str(row["sequence"] * 1000000)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        result = m.analyze_file(path, 10, 45)
        self.assertEqual(result["coverage"]["selectedSampleCount"], 3)
        self.assertEqual(result["metrics"]["rssBytes"]["count"], 3)
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["count"], 2)
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["first"], 2)
        self.assertIsNone(m.analyze_file(path, 10, 29)["metrics"]["cpuIntervalPercent"])
        # A phase summary inside the numeric window must obey both boundaries.
        markers = self.root / "markers.jsonl"
        markers.write_text(json.dumps({"phase": "visible", "monotonicNs": "1000000000"}) + "\n")
        phase = m.analyze_file(path, 10, 45, markers)["operatorPhases"]["intervals"][0]
        self.assertEqual(phase["metrics"]["cpuIntervalPercent"]["count"], 2)
        # A missing metric read makes the next CPU interval span the gap. Do not
        # substitute the nominal interval when the actual prior sample is known.
        rows[2]["process"] = None
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        result = m.analyze_file(path, 10, 45)
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["count"], 1)
        self.assertEqual(result["metrics"]["cpuIntervalPercent"]["first"], 3)

    def test_missing_footer_and_truncated_line_remain_incomplete(self):
        path, _ = self.fixture(False)
        with path.open("a") as output:
            output.write('{"type":')
        result = m.analyze_file(path)
        self.assertEqual(len(result["coverage"]["parseErrors"]), 1)
        self.assertIsNone(result["coverage"]["footer"])
        self.assertEqual(len(result["coverage"]["issues"]), 2)

    def test_gaps_clock_jumps_and_regressions_are_visible(self):
        path, rows = self.fixture()
        rows[3]["monotonicNs"] = str(100 * 10**9)
        rows[3]["manifest"]["durableStep"] = 0
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        result = m.analyze_file(path)
        self.assertTrue(result["coverage"]["gaps"])
        self.assertTrue(result["coverage"]["wallClockJumps"])
        self.assertIn("durableStep decreased", result["manifestProgress"]["regressions"])

    def test_operator_phases_not_inferred_and_boundary_cpu_excluded(self):
        path, _ = self.fixture()
        markers = self.root / "markers.jsonl"
        markers.write_text(json.dumps({"phase": "minimized", "monotonicNs": "11000000000"}) + "\n")
        interval = m.analyze_file(path, markers=markers)["operatorPhases"]["intervals"][0]
        self.assertEqual(interval["sampleCount"], 3)
        self.assertEqual(interval["metrics"]["cpuIntervalPercent"]["count"], 2)
        self.assertIn("operator-declared", interval["source"])

    @unittest.skipUnless(sys.platform == "darwin", "macOS passive capture smoke")
    def test_end_to_end_capture_own_process_only(self):
        process = m.MacProcess(os.getpid())
        executable = Path(process.identity()["executablePath"])
        output = self.root / "capture.jsonl"
        args = SimpleNamespace(pid=os.getpid(), executable=executable, expected_sha256=m.hash_file(executable), session=self.session, output=output, duration_seconds=.21, interval_seconds=.1, disk_every=2, max_output_bytes=65536)
        self.assertEqual(m.sample(args), 0)
        result = m.analyze_file(output)
        self.assertEqual(result["coverage"]["footer"]["status"], "completed")
        self.assertGreaterEqual(result["coverage"]["allSampleCount"], 3)
        self.assertEqual(result["coverage"]["sampleErrorCount"], 0)
        self.assertEqual(result["coverage"]["issues"], [])
        self.assertEqual(result["processIdentity"]["pid"], os.getpid())

    @unittest.skipUnless(sys.platform == "darwin", "macOS identity admission")
    def test_pid_start_change_during_admission_rejected(self):
        process = m.MacProcess(os.getpid())
        identity = process.identity()
        executable = Path(identity["executablePath"])
        args = SimpleNamespace(pid=os.getpid(), executable=executable, expected_sha256=m.hash_file(executable), session=self.session, output=self.root / "must-not-exist")
        changed = {**identity, "startMicroseconds": str(int(identity["startMicroseconds"]) + 1)}
        with patch.object(m.MacProcess, "identity", side_effect=[identity, changed]):
            with self.assertRaisesRegex(ValueError, "Identity changed"):
                m.sample(args)
        self.assertFalse(args.output.exists())

    @unittest.skipUnless(sys.platform == "darwin", "macOS libproc ABI")
    def test_current_process_identity_metrics_and_cpu_timebase(self):
        process = m.MacProcess(os.getpid())
        before = process.identity()
        self.assertEqual(ctypes.sizeof(m.BSDInfo), 136)
        self.assertEqual(ctypes.sizeof(m.TaskInfo), 96)
        first = process.metrics()
        cpu = time.process_time_ns()
        while time.process_time_ns() - cpu < 100_000_000:
            pass
        expected = time.process_time_ns() - cpu
        after = process.metrics()
        observed = int(after["cpuTotalNanoseconds"]) - int(first["cpuTotalNanoseconds"])
        self.assertGreater(observed / expected, .75)
        self.assertLess(observed / expected, 1.5)
        self.assertEqual(before, process.identity())
        self.assertGreater(after["rssBytes"], 0)
        self.assertGreaterEqual(after["fdCount"], 3)


if __name__ == "__main__":
    unittest.main()
