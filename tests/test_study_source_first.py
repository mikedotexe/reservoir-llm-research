"""Frozen source-first factors and dependency integrity; no model/runtime calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "probes/study_source_first.py"
spec = importlib.util.spec_from_file_location("study_source_first", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
FIRST_TEXT = "An independent, possibly mistaken first reading Ω.\nNEXT: SELF_STUDY CONTINUE\nSTUDY_NOTE: A fallible proposal.\n"


def synthetic_protocol():
    return {
        "trials": probe.trial_specs(), "system": probe.SYSTEM, "question": probe.QUESTION,
        "first_invitation": probe.FIRST, "final_invitation": probe.FINAL,
        "first_wrapper": probe.FIRST_WRAPPER, "account_wrapper": probe.ACCOUNT_WRAPPER,
        "evidence": "Frozen evidence only.\n```rust\n1: example();\n```\n",
        "accounts": {
            account: {"note": f"{account.upper()}_NOTE", "previous": f"{account.upper()}_PREVIOUS: original proxy question?",
                      "recent": [f"{account.upper()}_HISTORY_{i}: original proxy question?" for i in range(3)]}
            for account in ("retained", "supported")
        },
    }


def first_row(trial, text=FIRST_TEXT):
    return {"spec": trial, "outcome": "returned", "error": None,
            "result": {"text": text, "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                       "finish": "stop", "termination": {"kind": "model_eos", "model_eos_reached": True}}}


def rewrite_fixture(path, value):
    """Simulate external corruption of temporary fixtures, never real evidence."""
    if path.exists():
        path.chmod(0o600)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


class SourceFirstTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.protocol = synthetic_protocol()

    def trial(self, arm, block=1103):
        return next(row for row in self.protocol["trials"] if row["arm"] == arm and row["block"] == block)

    def retain_first(self, row=None, block=1103):
        trial = self.trial("first_read", block)
        path = self.root / f"{trial['id']}.json"
        probe.save(path, row or first_row(trial), immutable=True)
        return path

    def test_ten_generations_have_distinct_stage_seeds_and_balanced_final_factors(self):
        trials = probe.trial_specs()
        self.assertEqual(len(trials), 10)
        self.assertEqual(len({row["id"] for row in trials}), 10)
        self.assertEqual(sum(row["phase"] == "first" for row in trials), 2)
        self.assertEqual(sum(row["phase"] == "final" for row in trials), 8)
        for block, first_seed in ((1103, 3109), (2207, 4201)):
            rows = [row for row in trials if row["block"] == block]
            self.assertEqual(rows[0], {"id": f"source-first-{block}-first_read", "seed": first_seed,
                                     "block": block, "arm": "first_read", "phase": "first", "dependency": None})
            self.assertEqual({row["arm"] for row in rows[1:]}, set(probe.ARMS))
            for row in rows[1:]:
                self.assertEqual(row["seed"], block)
                self.assertEqual(row["phase"], "final")
                self.assertEqual(row["dependency"], rows[0]["id"] if row["arm"].endswith("_carried") else None)
        self.assertEqual([row["arm"] for row in trials[1:5]], list(reversed([row["arm"] for row in trials[6:10]])))

    def test_first_read_has_only_new_question_and_evidence_without_account_leakage(self):
        for block in (1103, 2207):
            messages = probe.build_messages(self.protocol, self.trial("first_read", block))
            expected = probe.FIRST + "\n\nQUESTION — " + probe.QUESTION + "\n\n" + self.protocol["evidence"]
            self.assertEqual(messages, [{"role": "system", "content": probe.SYSTEM}, {"role": "user", "content": expected}])
            for account in self.protocol["accounts"].values():
                for text in [account["note"], account["previous"], *account["recent"]]:
                    self.assertNotIn(text, messages[1]["content"])
            self.assertNotIn(probe.ACCOUNT_WRAPPER, messages[1]["content"])
            self.assertNotIn(probe.FIRST_WRAPPER, messages[1]["content"])

    def test_carried_treatment_adds_only_exact_full_first_read_before_same_account(self):
        addition = probe.FIRST_WRAPPER + FIRST_TEXT + "\nEND ISOLATED FIRST-READ RESPONSE\n\n"
        shared_prefix = probe.FINAL + "\n\nQUESTION — " + probe.QUESTION + "\n\n"
        for account in ("retained", "supported"):
            direct = probe.build_messages(self.protocol, self.trial(account + "_direct"))
            carried = probe.build_messages(self.protocol, self.trial(account + "_carried"), FIRST_TEXT)
            self.assertEqual(direct[0], carried[0])
            self.assertEqual(carried[1]["content"], shared_prefix + addition + direct[1]["content"][len(shared_prefix):])
            self.assertEqual(carried[1]["content"].count(FIRST_TEXT), 1)
            self.assertNotIn(FIRST_TEXT, direct[1]["content"])
            self.assertTrue(carried[1]["content"].endswith(self.protocol["evidence"]))
            self.assertEqual(carried[1]["content"].count(probe.QUESTION), 2)
            encoded = carried[1]["content"].split(probe.ACCOUNT_WRAPPER)[1].split("\nEND COMPARISON ACCOUNT\n")[0]
            notebook = json.loads(encoded)
            self.assertEqual(notebook["question"], {"text": probe.QUESTION})
            self.assertEqual(notebook["note"], {"text": self.protocol["accounts"][account]["note"]})
            self.assertEqual(notebook["previous"], {"text": self.protocol["accounts"][account]["previous"]})
            self.assertEqual(notebook["recent"], [{"text": row} for row in self.protocol["accounts"][account]["recent"]])
            self.assertNotIn("response_sha256", encoded)
            self.assertNotIn('"origin":', encoded)

    def test_two_carried_accounts_share_one_exact_dependency_and_are_idempotent(self):
        source = self.retain_first()
        receipts = []
        for account in ("retained", "supported"):
            trial = self.trial(account + "_carried")
            prepared = probe.prepare_trial(self.root, self.protocol, trial)
            receipts.append(prepared["dependency"])
            target = self.root / f"input-{trial['id']}.json"
            before = target.read_bytes()
            self.assertEqual(probe.prepare_trial(self.root, self.protocol, trial), prepared)
            self.assertEqual(target.read_bytes(), before)
            self.assertFalse(target.stat().st_mode & 0o222)
            self.assertIn(FIRST_TEXT, prepared["messages"][1]["content"])
            self.assertNotIn(prepared["dependency"]["response_sha256"], prepared["messages"][1]["content"])
        self.assertEqual(receipts[0], receipts[1])
        self.assertEqual(receipts[0]["result_file_sha256"], probe.digest(source))
        self.assertEqual(receipts[0]["response_sha256"], hashlib.sha256(FIRST_TEXT.encode()).hexdigest())

    def test_eligibility_requires_nonempty_model_eos_without_screening_answer_quality(self):
        trial = self.trial("first_read")
        for text in ("A mistaken claim.", "NEXT: SELF_STUDY CONTINUE", "I choose to stop.", FIRST_TEXT):
            self.assertTrue(probe.eligible_first(first_row(trial, text)))
        for change in ("length", "empty", "whitespace", "channel", "eos_flag", "error", "admission", "resource", "missing_result"):
            row = first_row(trial)
            if change == "length":
                row["result"]["finish"] = "length"
            elif change in ("empty", "whitespace"):
                row["result"]["text"] = "" if change == "empty" else " \n\t"
            elif change == "channel":
                row["result"]["termination"]["kind"] = "channel_boundary"
            elif change == "eos_flag":
                row["result"]["termination"]["model_eos_reached"] = False
            elif change == "error":
                row["error"] = "provider failed"
            elif change in ("admission", "resource"):
                row["outcome"] = "admission_unavailable" if change == "admission" else "cell_wall_resource_limit"
            else:
                row["result"] = None
            with self.subTest(change=change):
                self.assertFalse(probe.eligible_first(row))

    def test_definitive_failure_blocks_only_dependents_and_can_be_retained_immutably(self):
        first = first_row(self.trial("first_read"))
        first["result"]["finish"] = "length"
        source = self.retain_first(first)
        for account in ("retained", "supported"):
            trial = self.trial(account + "_carried")
            result = probe.prepare_trial(self.root, self.protocol, trial)
            self.assertEqual(result["outcome"], "dependency_unavailable")
            self.assertIsNone(result["result"])
            self.assertEqual(result["dependency"]["finish"], "length")
            self.assertEqual(result["dependency"]["result_file_sha256"], probe.digest(source))
            self.assertFalse((self.root / f"input-{trial['id']}.json").exists())
            output = self.root / f"{trial['id']}.json"
            probe.save(output, {"spec": trial, **result}, immutable=True)
            with self.assertRaises(FileExistsError):
                probe.save(output, {"outcome": "preferred answer"})
            direct = probe.prepare_trial(self.root, self.protocol, self.trial(account + "_direct"))
            self.assertIsNone(direct["dependency"])
            self.assertNotIn(probe.FIRST_WRAPPER, direct["messages"][1]["content"])

    def test_missing_prerequisite_is_not_recorded_as_permanent_failure(self):
        carried = self.trial("retained_carried")
        with self.assertRaisesRegex(ValueError, "not yet recorded"):
            probe.prepare_trial(self.root, self.protocol, carried)
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertIn("messages", probe.prepare_trial(self.root, self.protocol, self.trial("retained_direct")))

    def test_changed_dependency_receipt_or_eligibility_cannot_replace_prepared_lineage(self):
        trial = self.trial("retained_carried")
        for mutation in ("text", "receipt", "ineligible"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = first_row(self.trial("first_read"))
                path = root / f"{first['spec']['id']}.json"
                probe.save(path, first, immutable=True)
                probe.prepare_trial(root, self.protocol, trial)
                if mutation == "text":
                    first["result"]["text"] = "Changed first read"
                    first["result"]["response_sha256"] = hashlib.sha256(first["result"]["text"].encode()).hexdigest()
                elif mutation == "receipt":
                    first["receipt_note"] = "different receipt with identical text"
                else:
                    first["result"]["finish"] = "length"
                rewrite_fixture(path, first)
                with self.assertRaises(ValueError):
                    probe.prepare_trial(root, self.protocol, trial)

    def test_bad_dependency_spec_hash_and_changed_derived_input_are_rejected(self):
        for mutation in ("spec", "hash", "derived"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = first_row(self.trial("first_read"))
                path = root / f"{first['spec']['id']}.json"
                if mutation == "spec":
                    first["spec"] = {**first["spec"], "seed": 9999}
                elif mutation == "hash":
                    first["result"]["response_sha256"] = "false"
                probe.save(path, first, immutable=True)
                carried = self.trial("retained_carried")
                if mutation == "derived":
                    prepared = probe.prepare_trial(root, self.protocol, carried)
                    prepared["messages"][1]["content"] += "changed prompt"
                    rewrite_fixture(root / f"input-{carried['id']}.json", prepared)
                with self.assertRaises(ValueError):
                    probe.prepare_trial(root, self.protocol, carried)

    def test_no_undeclared_trial_or_first_read_injection_is_accepted(self):
        for arm, text in (("first_read", FIRST_TEXT), ("retained_direct", FIRST_TEXT), ("retained_carried", None), ("supported_carried", " \n")):
            with self.subTest(arm=arm), self.assertRaises(ValueError):
                probe.build_messages(self.protocol, self.trial(arm), text)
        altered = {**self.trial("retained_direct"), "seed": 9999}
        with self.assertRaises(ValueError):
            probe.build_messages(self.protocol, altered)
        with self.assertRaises(ValueError):
            probe.prepare_trial(self.root, self.protocol, altered)

    def test_actual_predecessor_source_accounts_provenance_and_code_bytes_survive_freeze(self):
        previous = ROOT / "research/outputs/2026-09-10-question-framing-v1"
        if not previous.exists():
            self.skipTest("retained predecessor unavailable")
        paths = [previous / "protocol.json", previous / "block-evidence.txt", *sorted((previous / "source-snapshot").iterdir())]
        before = {path: path.read_bytes() for path in paths}
        prior = json.loads((previous / "protocol.json").read_text())
        target = self.root / "frozen"
        protocol = probe.freeze(target, previous)
        self.assertEqual(protocol["accounts"], prior["accounts"])
        self.assertEqual(protocol["original_provenance"], prior["provenance"])
        self.assertEqual(protocol["settings"], prior["settings"])
        self.assertEqual(protocol["guards"], prior["guards"])
        old = (previous / "block-evidence.txt").read_text()
        self.assertEqual(protocol["evidence"], probe.adapt_evidence(old))
        numbered = lambda text: re.findall(r"```rust\n(.*?)\n```", text, re.S)
        self.assertEqual(len(numbered(old)), 7)
        self.assertEqual(numbered(protocol["evidence"]), numbered(old))
        for name, row in prior["source_map"].items():
            self.assertEqual(probe.digest(target / "source-snapshot" / name), row["sha256"])
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        for account in ("retained", "supported"):
            trial = next(t for t in protocol["trials"] if t["arm"] == account + "_direct")
            rendered = probe.build_messages(protocol, trial)[1]["content"]
            for historical in [prior["accounts"][account]["previous"], *prior["accounts"][account]["recent"]]:
                self.assertIn(json.dumps(historical, ensure_ascii=False)[1:-1], rendered)

    def test_ambiguous_wrapper_or_wrong_predecessor_identity_fails(self):
        with self.assertRaises(ValueError):
            probe.adapt_evidence("missing historical wrapper")
        previous = self.root / "wrong"
        previous.mkdir()
        (previous / "protocol.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "protocol differs"):
            probe.freeze(self.root / "new", previous)
        self.assertFalse((self.root / "new").exists())


if __name__ == "__main__":
    unittest.main()
