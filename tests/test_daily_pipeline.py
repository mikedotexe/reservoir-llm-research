"""Bounded offline fixtures for the maintained daily pipeline and CLI boundaries."""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from reservoir_research import cli
from reservoir_research.daily import DailyError, build_report, load_packet
from reservoir_research.daily.inputs import LEGACY_HISTORY, PACKET_NAMES, REQUIRED_NAMES, make_manifest
from reservoir_research.daily.eras import resolve_eras
from reservoir_research.study_capture import encoded, sha

def record(path, value, kind="release"):
    raw = encoded(value)
    return dict(path=path, kind=kind, text=raw.decode(), sha256=sha(raw), bytes=len(raw))

def paired_fixture():
    manifest = record("/unavailable/manifest.json", {"repository": {"head": "commit"}})
    previous = record("/unavailable/old.json", {"old": True})
    activation = record("/unavailable/activation.json", dict(status="activated_verified",
        new_process=dict(pid=21, started_at="Wed Sep 16 10:00:00 2026"),
        manifest_sha256=manifest["sha256"], old_identity=dict(manifest_sha256=previous["sha256"])))
    reload = record("/unavailable/reload.json", dict(outcome="success", new_pid=11,
        new_started_at="Wed Sep 16 10:01:00 2026"))
    rollout = record("/unavailable/rollout.json", dict(manifest_sha256=manifest["sha256"],
        bridge=dict(activation_receipt=activation["path"], activation_receipt_sha256=activation["sha256"],
                    old_pid=20, new_pid=21, started_at="Wed Sep 16 10:00:00 2026"),
        minime=dict(receipt=reload["path"], receipt_sha256=reload["sha256"],
                    old_pid=10, new_pid=11, started_at="Wed Sep 16 10:01:00 2026"),
        astrid_commit="astrid", minime_commit="minime"))
    rows = [rollout, manifest, activation, reload, previous]
    spec = dict(id="fixture-release", validator="paired-rollout-v1",
                records={key: {"path": row["path"]} for key, row in zip(
                    ["rollout", "manifest", "activation", "reload", "previous_manifest"], rows)})
    return rows, spec

def fixture(root):
    packet = root / "packet"; packet.mkdir()
    rows, spec = paired_fixture()
    initial = record("/unavailable/source-study-v1-validation/live-rollout.json",
                     {"minime": {"new_pid": 10}})
    for name in REQUIRED_NAMES:
        if name in PACKET_NAMES:
            value = dict(records=[initial, *rows] if name == "supplement.json" else [], errors=[])
            if name == "capture.json":
                value["selection"] = dict(since="2026-09-17T00:00:00+00:00", until_exclusive="2026-09-18T00:00:00+00:00")
        elif name == "tracking-before.json":
            value = {"seen_generations": []}
        elif name == "protocol.json":
            value = dict(since="2026-09-17T00:00:00+00:00", until_exclusive="2026-09-18T00:00:00+00:00",
                         ledger_sha256=sha(encoded({"seen_generations": []})))
        else:
            value = {}
        (packet / name).write_bytes(encoded(value))
    histories = []
    for name in LEGACY_HISTORY:
        folder = root / name; folder.mkdir()
        (folder / "evidence.json").write_bytes(b'{"retained":true}\n')
        (folder / "packet-manifest.json").write_bytes(encoded({"evidence.json": sha((folder / "evidence.json").read_bytes())}))
        histories.append(folder)
    manifest = make_manifest(packet, root, histories, [spec])
    path = root / "inputs.json"; path.write_bytes(encoded(manifest))
    return path, manifest

class DailyPipelineChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path, self.manifest = fixture(self.root)

    def save_manifest(self):
        self.path.write_bytes(encoded(self.manifest))

    def test_retained_paths_are_not_followed(self):
        packet = load_packet(self.path)
        self.assertEqual(len(packet.history_counts), 3)
        report = build_report(packet)
        self.assertEqual(report["generation_count"], 0)
        self.assertEqual(report["studies"], [])
        self.assertEqual(report["close_reading_ids"], [])

    def test_manifest_relocates_without_original_root(self):
        destination = self.root / "moved"
        shutil.copytree(self.root, destination, ignore=shutil.ignore_patterns("moved"))
        self.path.unlink()
        packet = load_packet(destination / "inputs.json")
        self.assertEqual(build_report(packet)["generation_count"], 0)

    def test_explicit_data_root_override(self):
        other = self.root / "nested"; other.mkdir()
        path = other / "manifest.json"; path.write_bytes(self.path.read_bytes())
        self.assertEqual(len(load_packet(path, self.root).history_counts), 3)

    def test_changed_declared_hash_rejected(self):
        (self.root / "packet/capture.json").write_text("{}")
        with self.assertRaisesRegex(DailyError, "hash differs"):
            load_packet(self.path)

    def test_changed_length_rejected(self):
        self.manifest["inputs"]["capture.json"]["bytes"] += 1
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "length differs"):
            load_packet(self.path)

    def test_parent_path_rejected(self):
        self.manifest["inputs"]["capture.json"]["path"] = "../outside.json"
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "relative path"):
            load_packet(self.path)

    def test_absolute_path_rejected(self):
        self.manifest["inputs"]["capture.json"]["path"] = "/unavailable/capture.json"
        self.save_manifest()
        with self.assertRaises(DailyError):
            load_packet(self.path)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            external = Path(elsewhere) / "capture.json"; external.write_bytes((self.root / "packet/capture.json").read_bytes())
            (self.root / "packet/capture.json").unlink()
            (self.root / "packet/capture.json").symlink_to(external)
            with self.assertRaisesRegex(DailyError, "escaping"):
                load_packet(self.path)

    def test_unknown_input_rejected(self):
        self.manifest["inputs"]["unknown.json"] = self.manifest["inputs"]["capture.json"]
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "Unknown"):
            load_packet(self.path)

    def test_missing_required_input_rejected(self):
        del self.manifest["inputs"]["interface-era.json"]
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "missing"):
            load_packet(self.path)

    def test_protocol_window_cannot_change_with_rehashed_input(self):
        path = self.root / "packet/capture.json"
        value = json.loads(path.read_bytes())
        value["selection"]["since"] = "2026-09-17T01:00:00+00:00"
        raw = encoded(value); path.write_bytes(raw)
        self.manifest["inputs"]["capture.json"].update(sha256=sha(raw), bytes=len(raw))
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "window differs"):
            load_packet(self.path)

    def test_ledger_cannot_change_with_rehashed_input(self):
        path = self.root / "packet/tracking-before.json"
        raw = encoded({"seen_generations": ["invented"]}); path.write_bytes(raw)
        self.manifest["inputs"]["tracking-before.json"].update(sha256=sha(raw), bytes=len(raw))
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "Ledger-before"):
            load_packet(self.path)

    def test_unknown_schema_rejected(self):
        self.manifest["schema"] = "execute-code-v1"
        self.save_manifest()
        with self.assertRaises(DailyError):
            load_packet(self.path)

    def test_era_definition_hash_rejected(self):
        self.manifest["era_definitions"][0]["id"] = "changed"
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "Era definition hash"):
            load_packet(self.path)

    def test_changed_history_rejected(self):
        (self.root / LEGACY_HISTORY[0] / "evidence.json").write_text("changed")
        with self.assertRaisesRegex(DailyError, "Historical evidence"):
            load_packet(self.path)

    def test_missing_history_rejected(self):
        self.manifest["history"].pop()
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "lineage"):
            load_packet(self.path)

    def test_duplicate_history_rejected(self):
        self.manifest["history"].append(self.manifest["history"][0])
        self.save_manifest()
        with self.assertRaisesRegex(DailyError, "Duplicate"):
            load_packet(self.path)

    def test_malformed_manifest_has_explicit_error(self):
        self.manifest["inputs"]["capture.json"] = {}
        self.save_manifest()
        with self.assertRaises(DailyError):
            load_packet(self.path)

    def test_memory_negative_control_preserves_original(self):
        packet = load_packet(self.path)
        original = packet.raw("supplement.json")
        value = packet.json("supplement.json")
        value["records"][0]["text"] += "changed"
        with self.assertRaises(DailyError):
            build_report(packet.replaced("supplement.json", value))
        self.assertEqual(packet.raw("supplement.json"), original)

    def test_conflicting_record_revision_rejected(self):
        packet = load_packet(self.path)
        first = packet.json("supplement.json")["records"][0]
        changed = record(first["path"], {"different": True})
        extra = packet.json("era-supplement.json"); extra["records"] = [changed]
        with self.assertRaisesRegex(DailyError, "sources changed"):
            build_report(packet.replaced("era-supplement.json", extra))

    def test_unknown_validator_rejected(self):
        rows, spec = paired_fixture()
        spec["validator"] = "import-arbitrary-code"
        with self.assertRaisesRegex(DailyError, "Unknown era"):
            resolve_eras(rows, [spec])

    def test_duplicate_era_rejected(self):
        rows, spec = paired_fixture()
        with self.assertRaisesRegex(DailyError, "duplicate"):
            resolve_eras(rows, [spec, spec])

    def test_cross_evidence_pid_rejected_after_outer_rehash(self):
        rows, spec = paired_fixture()
        changed = json.loads(rows[2]["text"]); changed["new_process"]["pid"] += 1
        rows[2] = record(rows[2]["path"], changed)
        self.assertEqual(sha(rows[2]["text"].encode()), rows[2]["sha256"])
        with self.assertRaisesRegex(DailyError, "activation identity"):
            resolve_eras(rows, [spec])

    def test_ambiguous_selector_rejected(self):
        rows, spec = paired_fixture()
        rows.append(copy.deepcopy(rows[0]))
        with self.assertRaisesRegex(DailyError, "exactly one"):
            resolve_eras(rows, [spec])

    def test_optimized_python_is_explicitly_rejected(self):
        script = "from reservoir_research.daily import load_packet; load_packet(__import__('pathlib').Path(" + repr(str(self.path)) + "))"
        result = subprocess.run([sys.executable, "-B", "-O", "-c", script], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("without -O", result.stderr)

    def test_cli_build_does_not_open_database_or_discover_sources(self):
        destination = self.root / "built"
        with patch.object(cli.store, "connect", side_effect=AssertionError("database opened")), \
             patch.object(cli, "default_sources", side_effect=AssertionError("live source discovery")), \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["study", "daily", "build", str(self.path), "--out", str(destination)])
        self.assertEqual(code, 0)
        self.assertTrue((destination / "report.json").is_file())

    def test_cli_cannot_overwrite_output(self):
        destination = self.root / "built"; destination.mkdir()
        with contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["study", "daily", "build", str(self.path), "--out", str(destination)])
        self.assertEqual(code, 2)
        self.assertEqual(list(destination.iterdir()), [])

    def test_build_only_does_not_claim_verification(self):
        destination = self.root / "built"
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = cli.main(["study", "daily", "build", str(self.path), "--out", str(destination)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stream.getvalue())["status"], "built")
        self.assertFalse((destination / "verification.json").exists())

if __name__ == "__main__":
    unittest.main()
