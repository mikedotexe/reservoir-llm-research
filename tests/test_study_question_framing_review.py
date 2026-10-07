"""Framing-review integrity and denominator checks with invented responses."""
import hashlib
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


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


@contextmanager
def retained_input_paths(root, protocol, paths):
    """Adapt only declared, hash-checked paths; never rewrite frozen evidence."""
    expected = dict(protocol["inputs"])
    previous = protocol["previous"]
    if expected.get(previous["path"]) != previous["sha256"]:
        raise ValueError("predecessor is not an identically hashed declared input")
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for section in ("frozen_files", "source_snapshots"):
            for path, identity in manifest[section].items():
                if path in expected and expected[path] != identity:
                    raise ValueError("conflicting retained input identity")
                expected[path] = identity
    paths = {Path(old): Path(new) for old, new in paths.items()}
    if set(paths) != {Path(path) for path in expected}:
        raise ValueError("relocation must name exactly the declared retained inputs")
    for old, identity in expected.items():
        if hashlib.sha256(paths[Path(old)].read_bytes()).hexdigest() != identity:
            raise ValueError("relocated retained input identity differs: " + old)
    freezer = Path(probe.framing.__file__)

    def retained_path(value):
        path = Path(value)
        if path in paths:
            return paths[path]
        # The unchanged verifier also checks its imported freezer's actual source.
        if path == freezer and freezer in paths.values():
            return freezer
        raise ValueError("undeclared retained input path: " + str(path))

    with mock.patch.object(probe, "Path", side_effect=retained_path):
        yield


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
        # These exact retained files, not a prefix rewrite or host-path fallback,
        # are the relocation contract for this historical packet. Their original
        # paths and hashes remain unchanged in the protocol and manifest.
        historical_repository = Path(protocol["previous"]["path"]).parents[3]
        relative_inputs = [
            "research/outputs/2026-09-10-evidence-order-v1/protocol.json",
            "probes/fixtures/study_question_framing_supported.json",
            "probes/study_question_framing.py",
        ]
        packet_files = ["protocol.json", "criteria.json", "baseline-user.txt", "system.txt",
                        *(f"input-{arm}.json" for arm in probe.framing.ARMS),
                        *(f"block-{name}.txt" for name in ("original-prefix", "evidence", "original-recall",
                                                          "supported-account", "freezer-source")),
                        *(f"source-snapshot/{name}.rs" for name in ("context", "dispatch", "mod", "modes"))]
        if (root / "manifest.json").exists():
            relative_inputs.extend(str(root.relative_to(ROOT) / name) for name in packet_files)
        paths = {historical_repository / name: ROOT / name for name in relative_inputs}
        with retained_input_paths(root, protocol, paths):
            integrity = probe.validate_inputs(root, protocol)
        self.assertTrue(integrity["exact_factor_reconstruction"])
        self.assertEqual(integrity["source_snapshots"], 4)
        # Input receipts only: never open a trial result in this qualification.
        for arm in probe.framing.ARMS:
            probe.order_review.validate_render(root, protocol, arm)

    def test_relocated_inputs_validate_with_historical_file_reads_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            historical = Path(temp) / "historical"
            historical.mkdir()
            root, protocol = fixture(historical)
            manifest = {"protocol_sha256": hashlib.sha256((root / "protocol.json").read_bytes()).hexdigest(),
                        "frozen_files": {str(root / "protocol.json"): hashlib.sha256((root / "protocol.json").read_bytes()).hexdigest()},
                        "source_snapshots": {str(root / "source-snapshot/context.rs"): hashlib.sha256((root / "source-snapshot/context.rs").read_bytes()).hexdigest()}}
            write(root / "manifest.json", manifest)
            restored = Path(temp) / "restored"
            shutil.copytree(historical, restored)
            relocated = restored / root.relative_to(historical)
            declared = {**protocol["inputs"], **manifest["frozen_files"], **manifest["source_snapshots"]}
            paths = {Path(path): restored / Path(path).relative_to(historical)
                     if Path(path).is_relative_to(historical) else Path(path) for path in declared}
            originals = {name: (relocated / name).read_bytes() for name in ("protocol.json", "manifest.json")}
            original_open = Path.open

            def deny_historical(path, *args, **kwargs):
                if path.is_relative_to(historical):
                    raise PermissionError("historical fixture reads denied")
                return original_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", deny_historical):
                with self.assertRaises(PermissionError):
                    (root / "protocol.json").read_bytes()
                with retained_input_paths(relocated, protocol, paths):
                    self.assertTrue(probe.validate_inputs(relocated, protocol)["exact_factor_reconstruction"])
                    with self.assertRaisesRegex(ValueError, "undeclared retained input"):
                        probe.Path(historical / "unlisted.json")
                for arm in probe.framing.ARMS:
                    probe.order_review.validate_render(relocated, protocol, arm)
            self.assertEqual(originals, {name: (relocated / name).read_bytes() for name in originals})

            # A good historical copy must not rescue a missing or altered restore.
            previous = Path(protocol["previous"]["path"])
            with self.assertRaisesRegex(ValueError, "exactly the declared"):
                with retained_input_paths(relocated, protocol, {k: v for k, v in paths.items() if k != previous}):
                    self.fail("an undeclared mapping was accepted")
            paths[previous].unlink()
            with self.assertRaises(FileNotFoundError):
                with retained_input_paths(relocated, protocol, paths):
                    self.fail("a missing retained input was accepted")
            paths[previous].write_text("changed predecessor")
            with self.assertRaisesRegex(ValueError, "identity differs"):
                with retained_input_paths(relocated, protocol, paths):
                    self.fail("a changed retained input was accepted")


if __name__ == "__main__":
    unittest.main()
