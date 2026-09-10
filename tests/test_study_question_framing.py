"""Question framing and counterfactual-provenance checks; no model calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "probes/study_question_framing.py"
SUPPORTED = ROOT / "probes/fixtures/study_question_framing_supported.json"
spec = importlib.util.spec_from_file_location("study_question_framing", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
QUESTION = "Which function must be the proxy?"


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def fixture(root):
    previous = root / "previous"
    (previous / "source-snapshot").mkdir(parents=True)
    source = previous / "source-snapshot/context.rs"
    source.write_text("// untouched source fixture\n")
    prefix = "YOUR CURRENT QUESTION — " + QUESTION + "\nFind this question's symbol: SELF_STUDY RELATE sense_tx\n\n"
    historical = {"origin": "historical generation", "response_sha256": "original-generation-hash", "complete": True}
    notebook = {
        "question": {**historical, "text": QUESTION},
        "note": {**historical, "text": "A proxy must exist."},
        "previous": {**historical, "text": "The earlier quoted question was: " + QUESTION},
        "recent": [{**historical, "text": f"Historical claim {i}; {QUESTION}"} for i in range(3)],
    }
    recall = "RECALLED ACCOUNT — your study notebook\n" + json.dumps(notebook) + "\nEnd of study notebook.\n"
    evidence = "ADDITIONAL EVIDENCE-ROLE RECEIPT (for this isolated comparison)\nunchanged code evidence\n\n"
    blocks = {"prefix": prefix, "evidence": evidence, "recall": recall}
    protocol = {
        "blocks": {}, "source_map": {"context.rs": {"sha256": probe.digest(source)}},
        "cases": {"evidence_then_recall": [{"role": "system", "content": "same system\n"}, {"role": "user", "content": prefix + evidence + recall}]},
        "model": "unchanged model", "runtime": "unchanged runtime",
        "settings": {"temperature": .7, "top_p": .95, "thinking": False, "max_tokens": 4096},
        "guards": {"device": "gpu", "max_rss_bytes": 18 * 1024**3, "trial_wall_seconds": 1800},
        "subject": "offline replay", "qualifications": "retained qualification",
        "boundaries": "no live writes", "resume": "retain existing outcomes",
    }
    for name, text in blocks.items():
        (previous / f"block-{name}.txt").write_text(text)
        protocol["blocks"][name] = {"bytes": len(text.encode()), "sha256": hashlib.sha256(text.encode()).hexdigest()}
    write(previous / "protocol.json", protocol)
    control = {"note": "supported note", "previous": "supported previous", "recent": ["supported first", "supported second", "supported third"], "source_basis": ["fixture source"]}
    supported = root / "supported.json"
    write(supported, control)
    return previous, supported, notebook, protocol


def freeze_fixture(root):
    previous, supported, notebook, prior = fixture(root)
    digest = probe.digest
    def fixture_digest(path):
        return probe.PREVIOUS_SHA if Path(path) == previous / "protocol.json" else digest(path)
    target = root / "new"
    with mock.patch.object(probe, "digest", side_effect=fixture_digest):
        protocol = probe.freeze(target, previous, supported)
    return target, previous, notebook, prior, protocol


class QuestionFramingTests(unittest.TestCase):
    def test_two_by_two_by_two_plan_reverses_all_four_conditions(self):
        specs = probe.trial_specs()
        self.assertEqual(len(specs), 8)
        self.assertEqual(len({row["id"] for row in specs}), 8)
        self.assertEqual({row["seed"] for row in specs}, {1009, 2027})
        self.assertEqual([row["arm"] for row in specs[4:]], list(reversed([row["arm"] for row in specs[:4]])))
        expected = {"retained_presupposing", "retained_neutral", "supported_presupposing", "supported_neutral"}
        for seed in (1009, 2027):
            self.assertEqual({row["arm"] for row in specs if row["seed"] == seed}, expected)
        for arm in expected:
            positions = [i % 4 for i, row in enumerate(specs) if row["arm"] == arm]
            self.assertEqual(sum(positions), 3)

    def test_only_both_current_question_fields_change_within_each_account(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, notebook, prior, protocol = freeze_fixture(Path(temp))
            evidence = "ADDITIONAL EVIDENCE-ROLE RECEIPT (for this isolated comparison)\nunchanged code evidence\n\n"
            for account in ("retained", "supported"):
                old = protocol["cases"][account + "_presupposing"]
                neutral = protocol["cases"][account + "_neutral"]
                self.assertEqual(old[0], neutral[0])
                self.assertEqual(old[0], prior["cases"]["evidence_then_recall"][0])
                for messages in (old, neutral):
                    self.assertTrue(messages[1]["content"].endswith(evidence))
                    self.assertIn("Find this question's symbol: SELF_STUDY RELATE sense_tx\n", messages[1]["content"])
                expected = old[1]["content"].replace("YOUR CURRENT QUESTION — " + QUESTION + "\n", "YOUR CURRENT QUESTION — " + probe.NEUTRAL + "\n", 1)
                expected = expected.replace('"question":{"text":' + json.dumps(QUESTION) + '}', '"question":{"text":' + json.dumps(probe.NEUTRAL) + '}', 1)
                self.assertEqual(neutral[1]["content"], expected)
            for framing in ("presupposing", "neutral"):
                text = protocol["cases"]["retained_" + framing][1]["content"]
                for earlier in [notebook["previous"], *notebook["recent"]]:
                    self.assertIn(json.dumps(earlier["text"])[1:-1], text)
            self.assertEqual(protocol["settings"], prior["settings"])
            self.assertEqual(protocol["guards"], prior["guards"])

    def test_both_envelopes_are_identical_text_slots_with_external_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            target, previous, notebook, _, protocol = freeze_fixture(Path(temp))
            self.assertEqual(protocol["provenance"]["retained_original"], notebook)
            self.assertEqual((target / "block-original-recall.txt").read_bytes(), (previous / "block-recall.txt").read_bytes())
            for messages in protocol["cases"].values():
                user = messages[1]["content"]
                recall = user.split(probe.WRAPPER)[1].split("\nEnd of study notebook.\n")[0]
                fields = json.loads(recall)
                self.assertEqual(set(fields), {"note", "question", "previous", "recent"})
                for field in [fields["note"], fields["question"], fields["previous"], *fields["recent"]]:
                    self.assertEqual(set(field), {"text"})
                for metadata in ("original-generation-hash", "response_sha256", "source_basis", "historical generation"):
                    self.assertNotIn(metadata, user)
                self.assertEqual(user.count(probe.WRAPPER), 1)
                self.assertIn("not source evidence or records of new live journal entries", user)

    def test_historical_data_and_freezer_source_are_retained_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            target, previous, _, prior, protocol = freeze_fixture(Path(temp))
            self.assertEqual(json.loads((previous / "protocol.json").read_text()), prior)
            self.assertEqual((target / "source-snapshot/context.rs").read_bytes(), (previous / "source-snapshot/context.rs").read_bytes())
            self.assertEqual((target / "block-freezer-source.txt").read_bytes(), MODULE.read_bytes())
            for name, row in protocol["blocks"].items():
                raw = (target / f"block-{name}.txt").read_bytes()
                self.assertEqual(row, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

    def test_real_predecessor_and_qualified_runner_are_unchanged(self):
        previous = ROOT / "research/outputs/2026-09-10-evidence-order-v1"
        if not previous.exists():
            self.skipTest("retained historical packet unavailable")
        paths = [previous / "protocol.json", *previous.glob("block-*.txt"), *sorted((previous / "source-snapshot").iterdir()), previous / "runner.py"]
        before = {path: path.read_bytes() for path in paths}
        with tempfile.TemporaryDirectory() as temp:
            protocol = probe.freeze(Path(temp) / "new", previous, SUPPORTED)
            self.assertEqual(len(protocol["trials"]), 8)
            self.assertEqual(protocol["accounts"]["supported"], probe.validate_account(json.loads(SUPPORTED.read_text())))
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        self.assertEqual(probe.digest(Path(probe.runner.__file__)), probe.digest(previous / "runner.py"))

    def test_supported_control_shape_and_source_anchors_match_supplied_snapshot(self):
        control = json.loads(SUPPORTED.read_text())
        account = probe.validate_account(control)
        self.assertEqual(set(account), {"note", "previous", "recent"})
        self.assertEqual(len(account["recent"]), 3)
        self.assertTrue(all(text.strip() for text in [account["note"], account["previous"], *account["recent"]]))
        self.assertTrue(all(isinstance(line, str) and line.strip() for line in control["source_basis"]))
        source = ROOT / "research/outputs/2026-09-10-evidence-order-v1/source-snapshot"
        if source.exists():
            modes = (source / "modes.rs").read_text().splitlines()
            self.assertIn(") -> bool {", "\n".join(modes[48:56]))
            branch = "\n".join(modes[242:252])
            self.assertLess(branch.index("conv.wants_introspect = true"), branch.rindex("true"))
            self.assertLess(branch.index("conv.introspect_target = Some"), branch.rindex("true"))
            context = (source / "context.rs").read_text().splitlines()
            self.assertIn('"pub fn dispatch(ctx: &Context)', context[16])
            self.assertIn("sensory_tx.send()", context[16])

    def test_missing_duplicate_or_malformed_boundaries_are_rejected(self):
        for prefix in ("missing", "YOUR CURRENT QUESTION — wrong\n", ("YOUR CURRENT QUESTION — " + QUESTION + "\n") * 2):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                probe.replace_question(prefix, QUESTION, probe.NEUTRAL)
        for text in ("missing", "RECALLED ACCOUNT — header\n{}\nEnd of study notebook.\n", "RECALLED ACCOUNT — header\n{}\nEnd of study notebook."):
            with self.subTest(text=text), self.assertRaises(ValueError):
                probe.extract_notebook(text)
        for control in ({}, {"note": "x", "previous": "y", "recent": []}, {"note": "x", "previous": "y", "recent": ["x", "y", 2]}):
            with self.subTest(control=control), self.assertRaises(ValueError):
                probe.validate_account(control)

    def test_wrong_identity_and_existing_output_are_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            previous, supported, _, _ = fixture(root)
            with self.assertRaisesRegex(ValueError, "protocol identity"):
                probe.freeze(root / "new", previous, supported)
            self.assertFalse((root / "new").exists())
            output = root / "existing.json"
            probe.save(output, {"outcome": "admission_unavailable"}, immutable=True)
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                probe.save(output, {"outcome": "preferred answer"}, immutable=True)
            self.assertEqual(output.read_bytes(), before)

    def test_run_mode_delegates_without_new_generation_implementation(self):
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(sys, "argv", [str(MODULE), "run", temp]), mock.patch.object(probe.runner, "run") as run:
                probe.main()
            run.assert_called_once_with(Path(temp).resolve())


if __name__ == "__main__":
    unittest.main()
