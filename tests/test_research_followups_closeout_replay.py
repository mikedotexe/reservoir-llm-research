import copy
import json
import os
import shutil
import unittest
from unittest import mock

import test_research_followups_closeout as fixtures
from reservoir_research import followup_closeout as v1
from reservoir_research import followup_closeout_replay as replay
from reservoir_research import research_followups as frozen


class SnapshotReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CloseoutTests()
        self.fixture.setUp()
        self.data, self.manifest = self.fixture.fixture()
        self.inputs = self.fixture.put(self.fixture.root / "inputs.json", self.manifest)
        self.report = v1.build_report(self.manifest, self.data)
        self.report_path = self.fixture.put(self.fixture.root / "report.json", self.report)

    def tearDown(self):
        self.fixture.tearDown()

    def test_rewrite_originals_after_snapshot_cannot_change_calculation(self):
        original = v1.build_report
        def calculate(manifest, snapshot):
            self.assertNotEqual(snapshot, self.data)
            self.fixture.put(self.data / "daily/final-report/report.json", {"changed": "after snapshot"})
            return original(manifest, snapshot)
        with mock.patch.object(v1, "build_report", side_effect=calculate):
            _manifest, report, proof = replay.calculate(self.inputs, self.data)
        self.assertEqual(report, self.report)
        self.assertFalse(proof["original_inputs_reopened_by_v1"])

    def test_initial_mutation_rejected_even_with_internally_resealed_packet(self):
        path = self.data / "daily/final-report/report.json"
        value = json.loads(path.read_bytes())
        value["studies"][0]["id"] = "rewritten"
        self.fixture.put(path, value)
        verification_path = self.data / "daily/verification.json"
        verification = json.loads(verification_path.read_bytes())
        verification["report_sha256"] = frozen.sha(path.read_bytes())
        self.fixture.put(verification_path, verification)
        packet_path = self.data / "daily/packet-manifest.json"
        packet = json.loads(packet_path.read_bytes())
        packet["final-report/report.json"] = frozen.sha(path.read_bytes())
        packet["verification.json"] = frozen.sha(verification_path.read_bytes())
        self.fixture.put(packet_path, packet)
        with self.assertRaisesRegex(ValueError, "Snapshot input hash mismatch"):
            replay.verify(self.inputs, self.data, self.report_path)

    def test_mutation_during_read_rejected(self):
        path = self.fixture.root / "mutating.txt"
        path.write_bytes(b"before")
        actual_read = os.read
        changed = False
        def change_after_read(fd, n):
            nonlocal changed
            result = actual_read(fd, n)
            if not changed:
                changed = True
                path.write_bytes(b"changed length")
            return result
        with mock.patch.object(os, "read", side_effect=change_after_read):
            with self.assertRaisesRegex(ValueError, "changed during read"):
                replay.stable_bytes(path, 100)

    def test_original_tree_unavailable_after_snapshot_and_no_network(self):
        original = v1.build_report
        def calculate(manifest, snapshot):
            shutil.rmtree(self.data)
            return original(manifest, snapshot)
        with mock.patch.object(v1, "build_report", side_effect=calculate), \
             mock.patch("socket.socket", side_effect=AssertionError("network")), \
             mock.patch.object(frozen, "capture_runs", side_effect=AssertionError("source capture")), \
             mock.patch.object(frozen, "capture_provider", side_effect=AssertionError("source capture")):
            self.assertTrue(replay.verify(self.inputs, self.data, self.report_path)["verified"])

    def test_input_escape_and_symlink_refused(self):
        malicious = copy.deepcopy(self.manifest)
        malicious["files"]["../escape"] = "a" * 64
        self.fixture.put(self.inputs, malicious)
        with self.assertRaises(ValueError):
            replay.calculate(self.inputs, self.data)
        self.fixture.put(self.inputs, self.manifest)
        path = self.data / "anchors.json"
        saved = path.read_bytes()
        path.unlink()
        other = self.fixture.root / "same-bytes.json"
        other.write_bytes(saved)
        path.symlink_to(other)
        with self.assertRaises(ValueError):
            replay.calculate(self.inputs, self.data)

    def test_changed_report_and_snapshot_budget_rejected(self):
        self.fixture.put(self.report_path, dict(self.report, s007="invented"))
        with self.assertRaisesRegex(ValueError, "does not replay exactly"):
            replay.verify(self.inputs, self.data, self.report_path)
        with mock.patch.object(replay, "TOTAL_LIMIT", 1):
            with self.assertRaisesRegex(ValueError, "size/type cap"):
                replay.calculate(self.inputs, self.data)

    def test_build_remains_pending_independent_verification(self):
        out = self.fixture.root / "built"
        def directory(path):
            path.mkdir(exist_ok=False)
            return path
        with mock.patch.object(v1, "output_directory", side_effect=directory):
            replay.build(self.inputs, self.data, out)
        construction = json.loads((out / "construction.json").read_bytes())
        self.assertEqual(construction["status"], "constructed_verification_pending")
        self.assertNotIn("verified", construction)
        self.assertTrue(replay.verify(out / "inputs.json", self.data, out / "report.json")["verified"])


if __name__ == "__main__":
    unittest.main()
