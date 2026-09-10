"""Framing-review integrity and denominator checks with invented responses."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load("study_question_framing_review", ROOT / "probes/study_question_framing_review.py")
fixtures = load("question_framing_test_fixtures", Path(__file__).with_name("test_study_question_framing.py"))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def write(path, value):
    if path.exists():
        path.chmod(0o600)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def fixture(root):
    target, previous, _, _, protocol = fixtures.freeze_fixture(root)
    # These are synthetic fixture inputs, not the pinned real predecessor.
    actual = hashlib.sha256((previous / "protocol.json").read_bytes()).hexdigest()
    protocol["previous"]["sha256"] = actual
    protocol["inputs"][str((previous / "protocol.json").resolve())] = actual
    write(target / "protocol.json", protocol)
    for index, arm in enumerate(probe.framing.ARMS):
        system, user = [row["content"].strip() for row in protocol["cases"][arm]]
        text = "<system>" + system + "<user>" + user + "<assistant>"
        tokens = list(range(index + 3))
        write(target / f"rendered-{arm}.json", {"arm": arm, "rendered_text": text,
              "rendered_sha256": digest(text), "token_ids": tokens, "token_count": len(tokens)})
    return target, protocol


def result(root, trial, *, finish="stop", text="The shown source supports pending-field assignment."):
    rendered = json.loads((root / f"rendered-{trial['arm']}.json").read_text())
    prompt = rendered["token_count"]
    tokens = [42, 106] if finish == "stop" else [42] * 4096
    value = {"text": text, "raw_text": text, "response_sha256": digest(text),
             "tokens": tokens, "completion_tokens": len(tokens), "filtered_tokens": 0,
             "terminal_tokens": int(finish == "stop"), "finish": finish,
             "termination": {"kind": "model_eos" if finish == "stop" else "allowance"},
             "prompt_tokens": prompt, "prompt_sha256": rendered["rendered_sha256"],
             "controls": {"temperature": .7, "top_p": .95}, "initial_cache_positions": [0, 0],
             "final_cache_positions": [prompt + len(tokens)] * 2, "seconds": .2, "admission_seconds": .1}
    row = {"spec": trial, "outcome": "returned", "result": value, "error": None}
    write(root / f"{trial['id']}.json", row)
    return row


class FramingReviewTests(unittest.TestCase):
    def test_within_account_pairs_are_not_confused_with_four_condition_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = fixture(Path(temp))
            for index in (0, 1, 4, 5):
                result(root, protocol["trials"][index])
            unavailable = protocol["trials"][2]
            write(root / f"{unavailable['id']}.json", {"spec": unavailable, "outcome": "admission_unavailable", "result": None})
            report = probe.review(root)
            self.assertEqual(report["schema"], "study_question_framing_review_v1")
            self.assertEqual(report["planned"], 8)
            self.assertEqual(len(report["within_account_pairs"]), 4)
            self.assertEqual(report["complete_within_account_pairs"], 2)
            self.assertEqual(report["complete_model_eos_within_account_pairs"], 2)
            self.assertEqual(report["all_four_nonempty_seeds"], [])
            self.assertEqual(report["all_four_model_eos_nonempty_seeds"], [])
            self.assertEqual(report["outcomes"], {"returned": 4, "admission_unavailable": 1, "missing": 3})
            self.assertEqual([report["renderings"][arm]["token_count"] for arm in probe.framing.ARMS], [3, 4, 5, 6])

    def test_whole_seed_block_and_annotation_fields_are_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = fixture(Path(temp))
            for trial in protocol["trials"][:4]:
                result(root, trial)
            first = protocol["trials"][0]
            annotation = {"id": first["id"], "response_sha256": digest("The shown source supports pending-field assignment."),
                          "proxy_status": "unassessed", "fixture_role": "unassessed", "shown_call_path": "partially_supported",
                          "saved_note": "omitted", "claims": [{"quote": "pending-field assignment", "verdict": "unsupported", "source_basis": "invented test text"}],
                          "summary": "No preference or correction inferred by the reviewer."}
            write(root / "annotations.json", [annotation])
            report = probe.review(root)
            self.assertEqual(report["all_four_nonempty_seeds"], [1009])
            self.assertEqual(report["all_four_model_eos_nonempty_seeds"], [1009])
            self.assertEqual(report["complete_model_eos_within_account_pairs"], 2)
            self.assertEqual(report["cells"][0]["annotation"], annotation)
            self.assertNotIn("score", report)

    def test_nonempty_allowance_pair_is_not_a_completed_model_eos_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root, protocol = fixture(Path(temp))
            result(root, protocol["trials"][0], finish="length")
            result(root, protocol["trials"][1])
            report = probe.review(root)
            self.assertEqual(report["complete_within_account_pairs"], 1)
            self.assertEqual(report["complete_model_eos_within_account_pairs"], 0)
            self.assertEqual(report["termination_kinds"], {"allowance": 1, "model_eos": 1})

    def test_questions_nav_and_provenance_cannot_change_outside_declared_factors(self):
        for kind in ("question", "navigation", "metadata", "account", "provenance"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(Path(temp))
                arm = "retained_neutral"
                user = protocol["cases"][arm][1]["content"]
                if kind == "question":
                    protocol["cases"][arm][1]["content"] = user.replace(probe.framing.NEUTRAL, "inconsistent current question", 1)
                elif kind == "navigation":
                    protocol["cases"][arm][1]["content"] = user.replace("SELF_STUDY RELATE sense_tx", "SELF_STUDY MAP")
                elif kind == "metadata":
                    protocol["cases"][arm][1]["content"] = user.replace('"note":{"text":', '"note":{"response_sha256":"forged","text":')
                elif kind == "account":
                    protocol["accounts"]["retained"]["previous"] = "silently rewritten history"
                else:
                    protocol["provenance"]["retained_original"]["note"]["response_sha256"] = "invented origin"
                write(root / "protocol.json", protocol)
                with self.assertRaises(ValueError):
                    probe.review(root)

    def test_predecessor_source_and_manifest_identities_are_checked(self):
        for kind in ("predecessor", "source", "manifest", "runtime", "plan"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(Path(temp))
                if kind == "predecessor":
                    protocol["previous"]["sha256"] = "false"
                elif kind == "source":
                    source = root / "source-snapshot/context.rs"
                    source.chmod(0o600)
                    source.write_text("altered source")
                elif kind == "manifest":
                    write(root / "manifest.json", {"protocol_sha256": "false"})
                elif kind == "runtime":
                    protocol["settings"]["temperature"] = 1.2
                else:
                    protocol["trials"].reverse()
                write(root / "protocol.json", protocol)
                with self.assertRaises(ValueError):
                    probe.review(root)

    def test_inherited_cache_render_and_exact_quote_guards_apply(self):
        for kind in ("cache", "render", "quote", "hash"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root, protocol = fixture(Path(temp))
                first = protocol["trials"][0]
                row = result(root, first)
                if kind == "cache":
                    row["result"]["initial_cache_positions"] = [1, 0]
                elif kind == "render":
                    row["result"]["prompt_sha256"] = "false"
                else:
                    write(root / "annotations.json", [{"id": first["id"],
                          "response_sha256": "false" if kind == "hash" else row["result"]["response_sha256"],
                          "claims": [{"quote": "absent phrase" if kind == "quote" else "pending-field assignment"}]}])
                write(root / f"{first['id']}.json", row)
                with self.assertRaises(ValueError):
                    probe.review(root)

    def test_actual_frozen_inputs_validate_without_opening_generated_responses(self):
        root = ROOT / "research/outputs/2026-09-10-question-framing-v1"
        if not root.exists():
            self.skipTest("retained framing protocol unavailable")
        protocol = json.loads((root / "protocol.json").read_text())
        integrity = probe.validate_inputs(root, protocol)
        self.assertTrue(integrity["exact_factor_reconstruction"])
        self.assertEqual(integrity["source_snapshots"], 4)
        # Input receipts only: never open a trial result in this qualification.
        for arm in probe.framing.ARMS:
            probe.order_review.validate_render(root, protocol, arm)


if __name__ == "__main__":
    unittest.main()
