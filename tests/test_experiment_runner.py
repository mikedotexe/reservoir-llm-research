"""Fixture-backed qualification of isolation, persistence, and local transport."""
from __future__ import annotations

from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from reservoir_experiments import runner
from reservoir_experiments.transport import (OllamaTransport, TransportError,
                                            decode_response, endpoint_parts, json_bytes)


def node(nid, *, kind="target", inputs=(), after=(), content="Read the supplied evidence."):
    return {"id": nid, "episode": "episode-01", "condition": nid, "kind": kind, "seed": 7,
            "messages": [{"role": "system", "content": "An offline research task."},
                         {"role": "user", "content": content}],
            "inputs": list(inputs), "after": list(after), "max_tokens": 1024}


def protocol(*nodes):
    return {"schema_version": 1, "id": "test-protocol", "study": "S-test", "split": "fixture",
            "model": "fixture:1", "endpoint": "http://127.0.0.1:11434",
            "options": {"temperature": .7, "num_ctx": 16384}, "think": False,
            "nodes": list(nodes or [node("a")]), "truth": {"private": "EVALUATOR_ONLY_SECRET"}}


def response(text="A complete answer.", **extra):
    value = {"model": "fixture:1", "done": True, "done_reason": "stop", "eval_count": 4,
             "message": {"content": text}, "prompt_eval_count": 30}
    value.update(extra)
    return json_bytes(value)


class FixtureTransport:
    def __init__(self, responses=None, identity=None):
        self.responses = list(responses or [])
        self.requests = []
        self.identity_value = identity or {"model": "fixture:1", "digest": "fixed"}
        self.identity_calls = 0

    def identity(self, model):
        self.identity_calls += 1
        return deepcopy(self.identity_value)

    def generate(self, request, *, timeout):
        self.requests.append(json.loads(request))
        value = self.responses.pop(0) if self.responses else response()
        if isinstance(value, BaseException):
            raise value
        return value


class SimulatedKill(BaseException):
    pass


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input = self.root / "input.json"
        self.run = self.root / "research" / "outputs" / "run"

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, value=None):
        self.input.write_bytes(json_bytes(value or protocol()))
        return runner.prepare(self.input, self.run, repository=self.root)

    def test_prepare_freezes_inputs_and_never_reads_truth_into_requests(self):
        p = protocol()
        source = self.root / "source.txt"
        source.write_text("known source")
        p["sources"] = [{"path": str(source), "sha256": runner.sha(source.read_bytes())}]
        self.prepare(p)
        source.write_text("later modification")
        transport = FixtureTransport()
        runner.run_protocol(self.run, transport=transport)
        self.assertNotIn("EVALUATOR_ONLY_SECRET", json.dumps(transport.requests))
        self.assertEqual((self.run / "sources/0000.bin").read_text(), "known source")
        self.assertTrue(runner.verify(self.run)["valid"])

    def test_exact_body_has_explicit_sampling_and_no_truth_metadata(self):
        p = protocol(node("a"))
        p["nodes"][0]["format"] = "json"
        request = json.loads(runner.render_request(p, p["nodes"][0], {}))
        self.assertEqual(request, {"model": "fixture:1", "stream": False,
                                  "messages": p["nodes"][0]["messages"],
                                  "options": {"temperature": .7, "num_ctx": 16384,
                                              "seed": 7, "num_predict": 1024},
                                  "think": False, "format": "json"})

    def qualify(self, p, *, count=10000, transport=None):
        self.input.write_bytes(json_bytes(p))
        output = self.root / "research" / "outputs" / "qualification"
        client = transport or FixtureTransport([response("x", prompt_eval_count=count, eval_count=1, done_reason="length")])
        record = runner.qualify(self.input, p["nodes"][0]["id"], output, repository=self.root, transport=client)
        return output, record, client

    def test_exact_large_prompt_qualification_preserves_planned_context(self):
        p = protocol(node("a", content="A lengthy prompt. " * 2000))
        qualification, record, client = self.qualify(p)
        self.assertEqual(client.requests[0]["options"]["num_ctx"], 32768)
        self.assertEqual(client.requests[0]["options"]["num_predict"], 1)
        self.assertEqual(record["planned_num_ctx"], 16384)
        p["context_qualifications"] = [str(qualification)]
        self.prepare(p)
        # A qualification is reusable only for the same prompt; seeds are not text.
        transport = FixtureTransport([response(prompt_eval_count=10000)])
        runner.run_protocol(self.run, transport=transport)
        self.assertEqual(transport.requests[0]["options"]["num_ctx"], 16384)
        self.assertEqual(transport.requests[0]["options"]["num_predict"], 1024)
        self.assertTrue(runner.verify(self.run)["valid"])

    def test_qualification_token_mismatch_stops_batch_and_is_verifiable(self):
        p = protocol(node("a", content="Long text " * 2000), node("b"))
        qualification, _, _ = self.qualify(p)
        p["context_qualifications"] = [str(qualification)]
        self.prepare(p)
        client = FixtureTransport([response(prompt_eval_count=9999)])
        with self.assertRaisesRegex(runner.ExperimentError, "count differs"):
            runner.run_protocol(self.run, transport=client)
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(runner.read_results(self.run)["a"]["error_code"], "context-count-mismatch")
        self.assertTrue(runner.verify(self.run)["valid"])

    def test_qualification_rejects_headroom_or_changed_prompt(self):
        p = protocol(node("a", content="Long text " * 2000))
        with self.assertRaisesRegex(runner.ExperimentError, "qualification failed"):
            self.qualify(p, count=16000)
        self.assertTrue((self.root / "research/outputs/qualification/failure.json").exists())

    def test_qualification_bound_to_prompt_identity_and_original_evidence(self):
        p = protocol(node("a", content="Long text " * 2000))
        qualification, record, _ = self.qualify(p)
        changed = deepcopy(p)
        changed["nodes"][0]["messages"][1]["content"] += "changed"
        with self.assertRaisesRegex(runner.ExperimentError, "exact empirical qualification"):
            runner.render_request(changed, changed["nodes"][0], {},
                                  qualifications={record["prompt_sha256"]: record})
        changed = deepcopy(p)
        changed["nodes"][0]["seed"] = 20
        runner.render_request(changed, changed["nodes"][0], {},
                              qualifications={record["prompt_sha256"]: record})
        p["context_qualifications"] = [str(qualification)]
        self.prepare(p)
        with self.assertRaisesRegex(runner.ExperimentError, "qualification provider/model identity"):
            runner.run_protocol(self.run, transport=FixtureTransport(identity={"digest": "changed"}))
        (qualification / "response.raw").write_bytes(response("tampered"))
        with self.assertRaisesRegex(runner.ExperimentError, "qualification hash"):
            runner.read_qualification(qualification)
        # Prepared evidence survives later alterations to the source qualification.
        runner.run_protocol(self.run, transport=FixtureTransport([response(prompt_eval_count=10000)]))

    def test_qualification_never_reuses_attempt_directory(self):
        p = protocol(node("a"))
        _, _, client = self.qualify(p, count=30)
        with self.assertRaisesRegex(runner.ExperimentError, "never retried"):
            self.qualify(p, transport=client)
        self.assertEqual(len(client.requests), 1)

    def test_materialized_parent_is_exact_and_siblings_are_isolated(self):
        p = protocol(node("parent"), node("one", inputs=["parent"], content="Earlier: {{output:parent}}"),
                     node("two", inputs=["parent"], content="Same earlier: {{output:parent}}"))
        self.prepare(p)
        transport = FixtureTransport([response("original {{output:one}}"), response("sibling secret"), response("last")])
        runner.run_protocol(self.run, transport=transport)
        self.assertIn("original {{output:one}}", transport.requests[1]["messages"][1]["content"])
        self.assertNotIn("sibling secret", json.dumps(transport.requests[2]))

    def test_forecast_inputs_prohibited_but_ordering_allowed(self):
        p = protocol(node("forecast", kind="forecast"),
                     node("target", after=["forecast"]))
        self.prepare(p)
        transport = FixtureTransport([response("Forecast secret"), response("target")])
        runner.run_protocol(self.run, transport=transport)
        self.assertNotIn("Forecast secret", json.dumps(transport.requests[1]))
        bad = protocol(node("f", kind="forecast"), node("t", inputs=["f"], content="{{output:f}}"))
        with self.assertRaisesRegex(runner.ExperimentError, "Forecast leakage"):
            runner.validate_protocol(bad)
        bad["nodes"][1]["kind"] = "reactivity"
        self.assertEqual(runner.validate_protocol(bad), ["f", "t"])

    def test_failed_forecast_does_not_block_target_but_failed_text_parent_does(self):
        p = protocol(node("f", kind="forecast"), node("t", after=["f"]),
                     node("dependent", kind="reactivity", inputs=["f"], content="{{output:f}}"), node("last"))
        self.prepare(p)
        transport = FixtureTransport([response("unfinished", done_reason="length"), response(), response()])
        result = runner.run_protocol(self.run, transport=transport)
        self.assertEqual(len(transport.requests), 3)
        self.assertEqual(result["counts"], {"incomplete": 1, "complete": 2, "blocked": 1})

    def test_limit_counts_dispatches_and_resume_does_not_repeat(self):
        self.prepare(protocol(node("a"), node("b", inputs=["a"], content="{{output:a}}"), node("c")))
        transport = FixtureTransport([response("", done=False), response("c")])
        first = runner.run_protocol(self.run, limit=1, transport=transport)
        self.assertEqual(first["dispatched_this_call"], 1)
        self.assertEqual(first["counts"], {"incomplete": 1, "blocked": 1, "pending": 1})
        second = runner.run_protocol(self.run, transport=transport)
        self.assertEqual(second["dispatched_this_call"], 1)
        self.assertEqual(len(transport.requests), 2)
        third = runner.run_protocol(self.run, transport=transport)
        self.assertEqual(third["dispatched_this_call"], 0)

    def test_crash_after_dispatch_is_ambiguous_and_never_retried(self):
        self.prepare(protocol(node("a"), node("b", inputs=["a"], content="{{output:a}}"), node("c")))
        transport = FixtureTransport([SimulatedKill(), response("c")])
        with self.assertRaises(SimulatedKill):
            runner.run_protocol(self.run, transport=transport)
        self.assertEqual(runner.status(self.run)["counts"], {"ambiguous": 1, "pending": 2})
        second = runner.run_protocol(self.run, transport=transport)
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(second["counts"], {"ambiguous": 1, "blocked": 1, "complete": 1})

    def test_crash_after_response_before_receipt_remains_ambiguous(self):
        self.prepare()
        transport = FixtureTransport()
        with patch.object(runner, "decode_response", side_effect=SimulatedKill()):
            with self.assertRaises(SimulatedKill):
                runner.run_protocol(self.run, transport=transport)
        self.assertTrue((self.run / "nodes/a/response.raw").exists())
        runner.run_protocol(self.run, transport=transport)
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(runner.status(self.run)["counts"], {"ambiguous": 1})

    def test_crash_before_dispatch_can_resume_matching_request(self):
        self.prepare()
        _, p = runner.load_run(self.run)
        runner.write_once(self.run / "nodes/a/request.json", runner.render_request(p, p["nodes"][0], {}))
        transport = FixtureTransport()
        runner.run_protocol(self.run, transport=transport)
        self.assertEqual(len(transport.requests), 1)

    def test_transport_timeout_persists_partial_and_stops_batch(self):
        self.prepare(protocol(node("a"), node("b")))
        transport = FixtureTransport([TransportError("timeout", "deadline", b'{"partial":')])
        with self.assertRaisesRegex(runner.ExperimentError, "Dispatch stopped"):
            runner.run_protocol(self.run, transport=transport)
        self.assertEqual((self.run / "nodes/a/response.raw").read_bytes(), b'{"partial":')
        self.assertEqual(runner.status(self.run)["counts"], {"transport_error": 1, "pending": 1})

    def test_identity_change_refuses_resume_before_generation(self):
        self.prepare(protocol(node("a"), node("b")))
        first = FixtureTransport()
        runner.run_protocol(self.run, limit=1, transport=first)
        other = FixtureTransport(identity={"digest": "different"})
        with self.assertRaisesRegex(runner.ExperimentError, "identity changed"):
            runner.run_protocol(self.run, transport=other)
        self.assertEqual(other.requests, [])

    def test_identity_is_checked_between_batches(self):
        self.prepare(protocol(node("a"), node("b")))
        transport = FixtureTransport()
        calls = iter([{"digest": "one"}, {"digest": "two"}])
        transport.identity = lambda model: next(calls)
        with self.assertRaisesRegex(runner.ExperimentError, "during batch"):
            runner.run_protocol(self.run, transport=transport, identity_every=1)
        self.assertEqual(len(transport.requests), 1)

    def test_changed_protocol_and_result_bytes_are_detected(self):
        self.prepare()
        transport = FixtureTransport()
        runner.run_protocol(self.run, transport=transport)
        result_path = self.run / "nodes/a/result.json"
        result = json.loads(result_path.read_bytes())
        result["text"] = "tampered"
        result_path.write_bytes(json_bytes(result))
        with self.assertRaisesRegex(runner.ExperimentError, "decode mismatch"):
            runner.verify(self.run)

    def test_parent_receipt_tampering_invalidates_descendant(self):
        self.prepare(protocol(node("a"), node("b", inputs=["a"], content="{{output:a}}")))
        runner.run_protocol(self.run, transport=FixtureTransport())
        path = self.run / "nodes/a/result.json"
        value = json.loads(path.read_bytes())
        value["elapsed_seconds"] = 555
        path.write_bytes(json_bytes(value))
        with self.assertRaisesRegex(runner.ExperimentError, "parent identity"):
            runner.verify(self.run)

    def test_snapshot_tampering_is_detected_before_dispatch(self):
        self.prepare()
        (self.run / "protocol.json").write_text("{}")
        with self.assertRaisesRegex(runner.ExperimentError, "Snapshot hash"):
            runner.run_protocol(self.run, transport=FixtureTransport())

    def test_freeze_and_packets_refuse_overwrite(self):
        self.prepare()
        with self.assertRaisesRegex(runner.ExperimentError, "existing"):
            runner.prepare(self.input, self.run, repository=self.root)
        runner.run_protocol(self.run, transport=FixtureTransport())
        pack = self.root / "research/outputs/blind"
        receipt = runner.blind(self.run, pack)
        self.assertEqual(receipt["passages"], 1)
        self.assertNotIn("fixture:1", (pack / "reading.md").read_text())
        with self.assertRaisesRegex(runner.ExperimentError, "already exists"):
            runner.blind(self.run, pack)

    def test_invalid_protocols_rejected(self):
        variants = []
        p = protocol(); p["nodes"][0]["id"] = "../bad"; variants.append(p)
        p = protocol(); p["nodes"].append(deepcopy(p["nodes"][0])); variants.append(p)
        p = protocol(); p["nodes"][0]["after"] = ["missing"]; variants.append(p)
        p = protocol(node("a", after=["b"]), node("b", after=["a"])); variants.append(p)
        p = protocol(); p["nodes"][0]["messages"][1]["content"] = "{{truth:x}}"; variants.append(p)
        p = protocol(); p["nodes"][0]["inputs"] = ["a"]; variants.append(p)
        p = protocol(); p["options"]["num_predict"] = 50; variants.append(p)
        p = protocol(); p["deadline_seconds"] = 999; variants.append(p)
        for p in variants:
            with self.subTest(protocol=p), self.assertRaises(runner.ExperimentError):
                runner.validate_protocol(p)

    def test_declared_node_priority_respected_with_topological_order(self):
        p = protocol(node("b", after=["a"]), node("c"), node("a"))
        self.assertEqual(runner.validate_protocol(p), ["c", "a", "b"])

    def test_context_overflow_fails_without_truncating(self):
        p = protocol(node("a", content="a" * 16000))
        with self.assertRaisesRegex(runner.ExperimentError, "context"):
            runner.render_request(p, p["nodes"][0], {})

    def test_output_and_source_symlink_guards(self):
        outside = self.root.parent / "outside-not-allowed"
        with self.assertRaisesRegex(runner.ExperimentError, "inside"):
            runner.guard_output(outside, self.root)
        source = self.root / "source"
        source.write_text("text")
        link = self.root / "link"
        link.symlink_to(source)
        with self.assertRaisesRegex(runner.ExperimentError, "Symlink"):
            runner.stable_read(link)
        destination = self.root / "research/outputs/link"
        destination.parent.mkdir(parents=True)
        destination.symlink_to(self.root / "other", target_is_directory=True)
        with self.assertRaisesRegex(runner.ExperimentError, "symlink"):
            runner.guard_output(destination / "run", self.root)


class DecodeTests(unittest.TestCase):
    def test_stop_reasons_empty_and_token_counts_remain_distinct(self):
        self.assertEqual(decode_response(response(), "fixture:1", 1024)["status"], "complete")
        self.assertEqual(decode_response(response(" "), "fixture:1", 1024)["status"], "empty")
        self.assertEqual(decode_response(response(done_reason="length"), "fixture:1", 1024)["status"], "incomplete")
        self.assertEqual(decode_response(response(eval_count=2048), "fixture:1", 1024)["status"], "incomplete")
        self.assertEqual(decode_response(b"not json", "fixture:1", 1024)["status"], "invalid_response")
        self.assertEqual(decode_response(response(eval_count="4"), "fixture:1", 1024)["status"], "invalid_response")
        self.assertEqual(decode_response(response(done_reason=4), "fixture:1", 1024)["status"], "invalid_response")
        self.assertTrue(decode_response(response(prompt_eval_count="unusable"), "fixture:1", 1024)["complete"])

    def test_model_mismatch_is_fatal(self):
        with self.assertRaisesRegex(TransportError, "different model"):
            decode_response(response(model="other"), "fixture:1", 1024)

    def test_endpoint_cannot_redirect_to_remote_or_files(self):
        for endpoint in ("https://127.0.0.1", "http://localhost:11434", "http://volya:11434",
                         "http://127.0.0.1/path", "file:///tmp/x", "http://u:p@127.0.0.1"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                endpoint_parts(endpoint)


class LocalHTTPTests(unittest.TestCase):
    def setUp(self):
        owner = self
        self.mode = "normal"
        self.calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                owner.calls.append((self.path, self.rfile.read(length)))
                if owner.mode == "redirect":
                    self.send_response(302); self.send_header("Location", "http://example.com/"); self.end_headers()
                    return
                data = response()
                if owner.mode == "oversized":
                    data = b"x" * 2048
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                try:
                    if owner.mode == "slow":
                        for byte in data:
                            self.wfile.write(bytes([byte])); self.wfile.flush(); time.sleep(.025)
                    else:
                        self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = OllamaTransport(f"http://127.0.0.1:{self.server.server_port}", max_response_bytes=1024)

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)

    def test_real_local_http_receipt(self):
        data = self.client.generate(b'{"model":"fixture:1"}', timeout=1)
        self.assertEqual(json.loads(data)["message"]["content"], "A complete answer.")
        self.assertEqual(self.calls, [("/api/chat", b'{"model":"fixture:1"}')])

    def test_redirect_is_never_followed(self):
        self.mode = "redirect"
        with self.assertRaises(TransportError) as context:
            self.client.generate(b"{}", timeout=1)
        self.assertEqual(context.exception.code, "http-status")
        self.assertEqual(len(self.calls), 1)

    def test_oversized_response_is_bounded(self):
        self.mode = "oversized"
        with self.assertRaises(TransportError) as context:
            self.client.generate(b"{}", timeout=1)
        self.assertEqual(context.exception.code, "response-size")

    def test_total_deadline_defeats_slow_dribble(self):
        self.mode = "slow"
        started = time.monotonic()
        with self.assertRaises(TransportError) as context:
            self.client.generate(b"{}", timeout=.12)
        self.assertEqual(context.exception.code, "timeout")
        self.assertLess(time.monotonic() - started, .8)


if __name__ == "__main__":
    unittest.main()
