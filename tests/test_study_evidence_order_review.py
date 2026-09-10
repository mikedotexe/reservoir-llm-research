"""Retained-evidence reviewer checks using invented text only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "probes/study_evidence_order_review.py"
spec = importlib.util.spec_from_file_location("study_evidence_order_review", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def fixture(root):
    prefix = "THIS TURN — navigation\nYOUR CURRENT QUESTION — Why?\n\n"
    evidence = "ADDITIONAL EVIDENCE-ROLE RECEIPT (for this isolated comparison)\nExact evidence λ.\n\n"
    recall = 'RECALLED ACCOUNT — your study notebook\n{"question":"Why?"}\nEnd of study notebook.\n'
    system = "Same system.\n"
    arms = ("evidence_then_recall", "recall_then_evidence")
    cases = {arm: [{"role": "system", "content": system}, {"role": "user", "content": text}]
             for arm, text in zip(arms, (prefix + evidence + recall, prefix + recall + evidence))}
    trials = [{"id": f"order-{seed}-{arm}", "seed": seed, "arm": arm}
              for index, seed in enumerate((307, 419, 631, 887))
              for arm in (arms if index % 2 == 0 else tuple(reversed(arms)))]
    protocol = {"schema": "study_evidence_order_v1", "cases": cases, "trials": trials,
                "settings": {"temperature": .7, "top_p": .95, "max_tokens": 4096},
                "blocks": {}, "source_map": {}, "criteria": {}}
    for name, text in (("prefix", prefix), ("evidence", evidence), ("recall", recall)):
        (root / f"block-{name}.txt").write_text(text)
        protocol["blocks"][name] = {"bytes": len(text.encode()), "sha256": digest(text)}
    (root / "system.txt").write_text(system)
    (root / "baseline-user.txt").write_text(prefix + evidence + recall)
    (root / "source-snapshot").mkdir()
    (root / "source-snapshot/context.rs").write_text("fixture source\n")
    protocol["source_map"]["context.rs"] = {"sha256": digest("fixture source\n")}
    write(root / "protocol.json", protocol)
    write(root / "criteria.json", {})
    for index, arm in enumerate(arms):
        write(root / f"input-{arm}.json", cases[arm])
        # Match the pinned template's trim operation without claiming this is a
        # real tokenizer or model replay. Counts deliberately differ by arm.
        text = "<system>" + system.strip() + "<user>" + cases[arm][1]["content"].strip() + "<assistant>"
        tokens = [1, 2, 3] + ([4] if index else [])
        write(root / f"rendered-{arm}.json", {"arm": arm, "rendered_text": text,
              "rendered_sha256": digest(text), "token_ids": tokens, "token_count": len(tokens)})
    return protocol


def result(root, spec, *, text="A source-grounded observation.\nNEXT: SELF_STUDY CONTINUE", finish="stop"):
    rendered = json.loads((root / f"rendered-{spec['arm']}.json").read_text())
    prompt = rendered["token_count"]
    tokens = [9, 42, 0] if finish == "stop" else [7] * 4096
    value = {"text": text, "raw_text": text, "response_sha256": digest(text),
             "tokens": tokens, "completion_tokens": len(tokens), "filtered_tokens": int(finish == "stop"),
             "terminal_tokens": int(finish == "stop"), "finish": finish,
             "termination": {"kind": "model_eos" if finish == "stop" else "allowance"},
             "prompt_tokens": prompt, "prompt_sha256": rendered["rendered_sha256"],
             "controls": {"temperature": .7, "top_p": .95},
             "initial_cache_positions": [0, 0], "final_cache_positions": [prompt + len(tokens)] * 2,
             "seconds": .25, "admission_seconds": .1}
    row = {"spec": spec, "outcome": "returned", "result": value, "error": None}
    write(root / f"{spec['id']}.json", row)
    return row


class EvidenceOrderReviewTests(unittest.TestCase):
    def test_reports_four_pairs_missingness_and_unequal_token_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol = fixture(root)
            result(root, protocol["trials"][0])
            missing = protocol["trials"][1]
            write(root / f"{missing['id']}.json", {"spec": missing, "outcome": "admission_unavailable", "result": None})
            report = probe.review(root)
            self.assertEqual(report["schema"], "study_evidence_order_review_v1")
            self.assertEqual(report["planned"], 8)
            self.assertEqual(len(report["pairs"]), 4)
            self.assertEqual(report["outcomes"], {"returned": 1, "admission_unavailable": 1, "missing": 6})
            self.assertEqual(report["matched_nonempty_seeds"], [])
            self.assertEqual([report["renderings"][arm]["token_count"] for arm in probe.ARMS], [3, 4])
            self.assertIn("Four paired seeds", report["limits"])

    def test_finished_pairs_annotations_and_choices_preserve_exact_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol = fixture(root)
            for trial in protocol["trials"]:
                result(root, trial)
            first = protocol["trials"][0]
            annotations = [{"id": first["id"], "response_sha256": digest("A source-grounded observation.\nNEXT: SELF_STUDY CONTINUE"),
                            "proxy_necessity": "unassessed", "claims": [{"quote": "A source-grounded observation.", "verdict": "unsupported", "source": "invented test phrase"}]}]
            write(root / "annotations.json", annotations)
            report = probe.review(root)
            self.assertEqual(report["matched_nonempty_seeds"], [307, 419, 631, 887])
            self.assertEqual(report["annotated"], 1)
            self.assertEqual(report["cells"][0]["annotation"], annotations[0])
            self.assertEqual(report["cells"][0]["authored"]["NEXT"], "SELF_STUDY CONTINUE")

    def test_length_and_empty_stops_are_accounted_without_claiming_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol = fixture(root)
            result(root, protocol["trials"][0], finish="length")
            result(root, protocol["trials"][1], text="")
            report = probe.review(root)
            self.assertEqual(report["nonempty"], 1)
            self.assertEqual(report["outcomes"]["returned"], 2)
            self.assertEqual(report["matched_nonempty_seeds"], [])
            self.assertEqual(report["termination_kinds"], {"allowance": 1, "model_eos": 1})

    def test_partial_error_cache_is_distinct_from_completed_lookahead(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol = fixture(root)
            trial = protocol["trials"][0]
            row = result(root, trial, text="")
            row["outcome"] = "generation_error"
            row["error"] = "fixture prefill error"
            row["result"].update(finish="error", termination=None, tokens=[], completion_tokens=0,
                                 filtered_tokens=0, terminal_tokens=0, final_cache_positions=[1, 2])
            write(root / f"{trial['id']}.json", row)
            report = probe.review(root)
            self.assertEqual(report["cache_progression"][trial["id"]]["status"], "partial_generation_error_not_full_parity")
            row["result"]["final_cache_positions"] = [5, 5]
            write(root / f"{trial['id']}.json", row)
            with self.assertRaisesRegex(ValueError, "error cache"):
                probe.review(root)

    def test_rejects_nonfresh_or_impossible_completed_cache_and_false_length(self):
        for change, expected in (({"initial_cache_positions": [1, 0]}, "not fresh"),
                                 ({"final_cache_positions": [5, 5]}, "lookahead"),
                                 ({"finish": "length", "terminal_tokens": 0}, "exhaustion")):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                protocol = fixture(root)
                trial = protocol["trials"][0]
                row = result(root, trial)
                row["result"].update(change)
                write(root / f"{trial['id']}.json", row)
                with self.assertRaisesRegex(ValueError, expected):
                    probe.review(root)

    def test_rejects_modified_blocks_sources_rendering_and_pair_plan(self):
        mutations = (lambda root: (root / "block-recall.txt").write_text("changed"),
                     lambda root: (root / "source-snapshot/context.rs").write_text("changed"),
                     lambda root: (root / "input-recall_then_evidence.json").write_text("[]"))
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                fixture(root)
                mutation(root)
                with self.assertRaises(ValueError):
                    probe.review(root)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol = fixture(root)
            protocol["trials"].reverse()
            write(root / "protocol.json", protocol)
            with self.assertRaisesRegex(ValueError, "balanced seed pairs"):
                probe.review(root)

    def test_rejects_absent_or_corrupt_render_receipts_and_annotations(self):
        for corruption in ("missing", "token_count", "prompt_hash", "quote", "annotation_hash"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                protocol = fixture(root)
                trial = protocol["trials"][0]
                row = result(root, trial)
                rendered_path = root / f"rendered-{trial['arm']}.json"
                if corruption == "missing":
                    rendered_path.unlink()
                elif corruption == "token_count":
                    rendered = json.loads(rendered_path.read_text())
                    rendered["token_count"] += 1
                    write(rendered_path, rendered)
                elif corruption == "prompt_hash":
                    row["result"]["prompt_sha256"] = "false"
                    write(root / f"{trial['id']}.json", row)
                else:
                    write(root / "annotations.json", [{"id": trial["id"],
                          "response_sha256": "false" if corruption == "annotation_hash" else row["result"]["response_sha256"],
                          "claims": [{"quote": "absent quote"}]}])
                with self.assertRaises(ValueError):
                    probe.review(root)


if __name__ == "__main__":
    unittest.main()
