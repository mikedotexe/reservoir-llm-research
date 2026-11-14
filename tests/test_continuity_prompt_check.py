"""Evidence integrity and single-attempt diagnostics; no model calls."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from probes import continuity_prompt_check as probe
from reservoir_experiments.transport import TransportError, json_bytes


def prompt(step, *, history=True):
    before = (f"reservoir-journal-actions-v2\nCURRENT OBSERVATION at numerical step {step}\n"
              "Recurrent state RMS: 0.41200000. Separate sensory fill (%): 72.10000000. "
              "Recurrent coordinate distance since the previous observation: 1.22000000.\n"
              "ACTIVE CONTROLS\n{\"leak\":0.65,\"recurrentGain\":1.0,\"feedbackScale\":0.4}\n"
              "RECENT EXECUTION RECEIPTS (oldest first)\n"
              "Step 21: request {\"kind\":\"none\"}; immediate recurrent L2 difference 0.00000000; "
              "max coordinate difference 0.00000000.\n" + probe.OLD_COMPARISON + "\n"
              "TEXT INPUT STATE\nCurrent applied journal: null; disposition: no journal applied yet; held encoded vector L2: 0.00000000.\n\n")
    memory = (probe.MEMORY_MARKER + json.dumps("Quoted data: " + probe.OLD_RELEASE + " " + probe.OLD_COMPARISON)
              if history else "No earlier applied journal is available.")
    return before + memory + "\n\nAVAILABLE NEXT ACTIONS\n" + probe.OLD_RELEASE + "\n" + probe.OLD_EXAMPLE


def fixture(root):
    source = root / "source.jsonl"
    rows = []
    for step in (30, 1620, 2730, 3750):
        text = f"Synthetic earlier output at {step}"
        rows.append({"observedStep": step, "entryId": f"journal-{step}", "rawResponse": text,
                     "rawResponseSha256": probe.sha(text.encode()),
                     "journal": {"pending": {"entry": {"observedStep": step, "id": f"journal-{step}"},
                                              "observation": {"step": step, "previousObservationStep": step-30,
                                                              "rms": 0.412, "l2": 2.3, "changeL2": 1.22,
                                                              "sensory": {"fillPercent": 72.1}},
                                              "prompt": prompt(step, history=step != 30)}}})
    source.write_bytes(b"".join(json_bytes(row) for row in rows))
    return source, probe.sha(source.read_bytes())


class FakeTransport:
    def __init__(self, outcomes=None, changed_identity=False):
        self.calls = []
        self.identity_calls = []
        self.outcomes = outcomes or {}
        self.changed_identity = changed_identity

    def identity(self, model):
        self.identity_calls.append(model)
        changed = self.changed_identity and len(self.identity_calls) > 2
        return {"model": {"name": model, "digest": "b" * 64 if changed else probe.EXPECTED_DIGESTS[model]}, "show": {}}

    def generate(self, raw, *, timeout):
        request = json.loads(raw)
        self.calls.append((request, timeout))
        outcome = self.outcomes.get(len(self.calls))
        if isinstance(outcome, BaseException):
            raise outcome
        response = {"model": request["model"], "done": True, "done_reason": "stop",
                    "message": {"content": f"Diagnostic response {len(self.calls)}."},
                    "eval_count": 8, "prompt_eval_count": 2500}
        if outcome:
            response.update(outcome)
        return json_bytes(response)


class ContinuityPromptCheck(unittest.TestCase):
    def make_prepared(self, root, name="out", order_seed=19):
        source, digest = fixture(root)
        output = root / name
        probe.prepare(source, digest, output, order_seed=order_seed)
        return output

    def test_receipt_transformation_preserves_quoted_history_and_numeric_data(self):
        old = prompt(1620)
        new = probe.clarified_receipts(old)
        self.assertEqual(probe.scaffold_parts(old)[1], probe.scaffold_parts(new)[1])
        for value in ("1620", "0.41200000", "72.10000000", "1.22000000", "Step 21", "0.00000000"):
            self.assertEqual(old.count(value), new.count(value))
        self.assertIn("at that receipt's application step", new)
        self.assertIn("previous and current observation endpoints", new)
        self.assertIn("does not mean the reservoir stopped moving", new)
        self.assertIn(probe.NEW_RELEASE, new)

    def test_example_changes_only_terminal_example_block_and_order(self):
        old = prompt(1620)
        first = probe.withholding_example(old, "balanced_true_first")
        reverse = probe.withholding_example(old, "balanced_false_first")
        prefix = old[:-len(probe.OLD_EXAMPLE)]
        self.assertTrue(first.startswith(prefix))
        self.assertTrue(reverse.startswith(prefix))
        left, right = probe.BALANCED_LINES
        self.assertEqual(first.replace(left + "\n" + right, right + "\n" + left), reverse)
        self.assertEqual(probe.withholding_example(old, "true_example"), old)
        with self.assertRaises(ValueError):
            probe.withholding_example(old + " altered", "true_example")

    def test_prepare_balances_48_cases_and_contacts_no_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(probe, "OllamaTransport") as transport:
                output = self.make_prepared(root)
                transport.assert_not_called()
            plan = probe.validate_prepared(output)
            cases = [probe.read_json(p) for p in (output / "private/cases").glob("*/metadata.json")]
            self.assertEqual(len(cases), 48)
            self.assertEqual({model: sum(c["model"] == model for c in cases) for model in probe.MODELS},
                             {model: 24 for model in probe.MODELS})
            self.assertEqual(sum(c["study"] == "receipt" for c in cases), 24)
            self.assertEqual(sum(c["study"] == "input_example" for c in cases), 24)
            self.assertEqual(len(set(plan["executionOrder"])), 48)
            self.assertNotEqual(plan["executionOrder"], sorted(plan["executionOrder"]))
            for seed in probe.GENERATION_SEEDS:
                self.assertEqual(sum(c["seed"] == seed for c in cases), 24)

    def test_prepare_rejects_wrong_source_identity_and_nonlocal_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, digest = fixture(root)
            with self.assertRaisesRegex(ValueError, "source hash"):
                probe.prepare(source, "0" * 64, root / "bad")
            with self.assertRaisesRegex(ValueError, "127.0.0.1"):
                probe.prepare(source, digest, root / "remote", endpoint="https://example.com")
            self.assertFalse((root / "bad").exists())
            self.assertFalse((root / "remote").exists())

    def test_tampered_prepared_prompt_blocks_before_any_network(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.make_prepared(Path(directory))
            path = output / "private/cases/case-001/prompt.txt"
            path.write_text(path.read_text() + " Changed.")
            transport = FakeTransport()
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                probe.run(output, transport=transport)
            self.assertEqual(transport.identity_calls, [])
            self.assertEqual(transport.calls, [])

    def test_single_attempt_failures_are_retained_and_all_opportunities_are_sampled(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.make_prepared(Path(directory))
            transport = FakeTransport({1: TransportError("timeout", "fixture timeout", b"partial"),
                                       2: {"done_reason": "length", "eval_count": 1024},
                                       3: {"message": {"content": ""}}})
            with redirect_stdout(io.StringIO()):
                result = probe.run(output, transport=transport)
            self.assertEqual(len(transport.calls), 48)
            self.assertTrue(all(timeout == 180 for _, timeout in transport.calls))
            self.assertEqual(result["outcomes"], {"transport_failed": 1, "incomplete": 1, "empty": 1, "complete": 45})
            self.assertEqual(result["status"], "completed_with_qualifications")
            packet = (output / "blind/packet.md").read_text()
            self.assertEqual(packet.count("\n## S"), 48)
            self.assertNotIn("gemma4", packet)
            self.assertNotIn("balanced_true_first", packet)
            self.assertEqual(len(probe.read_json(output / "private/key.json")), 48)
            evidence = (output / "blind/evidence.md").read_text()
            self.assertEqual(evidence.count("\n| S"), 48)
            self.assertNotIn("gemma4", evidence)
            self.assertNotIn("balanced_true_first", evidence)
            self.assertIn("not addressed", evidence)
            self.assertIn("observedEndpointL2Difference", evidence)
            plan = probe.read_json(output / "private/plan.json")
            failed = output / "private/cases" / plan["executionOrder"][0]
            self.assertEqual((failed / "response.raw").read_bytes(), b"partial")
            with self.assertRaisesRegex(ValueError, "already dispatched"):
                probe.run(output, transport=transport)
            self.assertEqual(len(transport.calls), 48)

    def test_identity_change_and_unknown_context_are_qualified(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.make_prepared(Path(directory))
            transport = FakeTransport({1: {"prompt_eval_count": None}}, changed_identity=True)
            with redirect_stdout(io.StringIO()):
                result = probe.run(output, transport=transport)
            self.assertEqual(result["outcomes"], {"complete": 48})
            self.assertFalse(result["modelDigestsStable"])
            self.assertEqual(result["contextHeadroom"]["unknown"], 1)
            self.assertEqual(result["status"], "completed_with_qualifications")

    def test_interrupted_dispatch_cannot_be_resumed_as_a_fresh_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.make_prepared(Path(directory))
            transport = FakeTransport({1: RuntimeError("simulated process interruption")})
            with self.assertRaisesRegex(RuntimeError, "interruption"):
                probe.run(output, transport=transport)
            self.assertEqual(probe.read_json(output / "incomplete.json")["completedOpportunities"], 0)
            self.assertEqual(len(transport.calls), 1)
            with self.assertRaisesRegex(ValueError, "already dispatched"):
                probe.run(output, transport=transport)
            self.assertEqual(len(transport.calls), 1)

    def test_hosted_identity_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Hosted"):
            probe.identity_digest({"model": {"digest": "a" * 64}, "show": {"remote_host": "cloud.example"}})


if __name__ == "__main__":
    unittest.main()
