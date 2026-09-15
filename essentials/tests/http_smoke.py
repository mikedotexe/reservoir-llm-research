#!/usr/bin/env python3
"""Exercise the real CLI/URLSession transport against a newly owned loopback fixture.

Python standard library only. This does not discover endpoints, load a model, or
contact an existing service. Each case binds a new ephemeral 127.0.0.1 port.
Usage: python3 essentials/tests/http_smoke.py --cli /path/to/essentials-run --output receipt.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.server
import json
import pathlib
import subprocess
import tempfile
import threading
from contextlib import contextmanager

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "essentials-http-fixture-model"
PROVIDER_MODEL = "essentials-http-fixture-provider"
TEXT = "I notice the broad field and wonder which pattern will persist."
BODY_LIMIT = 65_536
CAPTURE_LIMIT = 8


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FixtureServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 2

    def __init__(self, scenario: str):
        self.scenario = scenario
        self.captures: list[dict] = []
        self.capture_overflow = 0
        self.capture_lock = threading.Lock()
        super().__init__(("127.0.0.1", 0), FixtureHandler)


class FixtureHandler(http.server.BaseHTTPRequestHandler):
    server: FixtureServer

    def log_message(self, *_args) -> None:
        pass

    def do_GET(self) -> None:
        self.handle_fixture()

    def do_POST(self) -> None:
        self.handle_fixture()

    def handle_fixture(self) -> None:
        self.connection.settimeout(5)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = BODY_LIMIT + 1
        if length < 0 or length > BODY_LIMIT:
            self.send_error(413)
            return
        payload = self.rfile.read(length)
        try:
            body = json.loads(payload) if payload else None
        except (ValueError, UnicodeDecodeError):
            body = None
        capture = {"method": self.command, "path": self.path,
                   "content_type": self.headers.get("Content-Type"),
                   "body_bytes": len(payload), "body_sha256": hashlib.sha256(payload).hexdigest(),
                   "body": body}
        with self.server.capture_lock:
            if len(self.server.captures) >= CAPTURE_LIMIT:
                self.server.capture_overflow += 1
                self.send_error(429)
                return
            self.server.captures.append(capture)
        scenario = self.server.scenario
        if scenario == "http_error":
            self.send_error(503, "Owned fixture failure")
            return
        if scenario == "redirect" and self.path != "/redirected":
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/redirected")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        response = {"done": scenario != "partial", "model": PROVIDER_MODEL,
                    "done_reason": "length" if scenario == "length" else "stop",
                    "eval_count": 256 if scenario == "length" else 15,
                    "message": {"role": "assistant", "content": TEXT}}
        encoded = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        try:
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass


@contextmanager
def fixture(scenario: str):
    server = FixtureServer(scenario)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        require(not thread.is_alive(), "Owned fixture did not stop")


def run_case(cli: pathlib.Path, temporary: pathlib.Path, scenario: str) -> dict:
    with fixture(scenario) as server:
        spec = {"stage": 3, "seed": 20260909, "steps": 31, "turnEvery": 30,
                "language": {"backend": "ollama", "endpoint": f"http://127.0.0.1:{server.server_port}", "model": MODEL}}
        config_path = temporary / f"{scenario}-spec.json"
        output_path = temporary / f"{scenario}-run.json"
        config_path.write_text(json.dumps(spec), encoding="utf-8")
        completed = subprocess.run([str(cli), "run", "--config", str(config_path), "--output", str(output_path)],
                                   capture_output=True, text=True, timeout=30, check=False)
        require(output_path.is_file(), f"{scenario}: no retained run ({completed.stderr[-1000:]})")
        require(output_path.stat().st_size < 16_777_216, f"{scenario}: unexpected output size")
        record = json.loads(output_path.read_text(encoding="utf-8"))
        captures = list(server.captures)
        require(server.capture_overflow == 0, f"{scenario}: fixture capture limit exceeded")
        require(len(captures) == 1, f"{scenario}: expected one request, received {len(captures)}")
        request = captures[0]
        body = request["body"]
        require(request["method"] == "POST" and request["path"] == "/api/chat", f"{scenario}: wrong HTTP request")
        require(request["content_type"] == "application/json", f"{scenario}: incorrect content type")
        require(isinstance(body, dict) and body.get("model") == MODEL, f"{scenario}: explicit model missing")
        require(body.get("stream") is False, f"{scenario}: streaming was not disabled")
        require(body.get("options", {}).get("num_predict") == 256, f"{scenario}: output limit differs")
        require(body.get("options", {}).get("temperature") == 0, f"{scenario}: temperature differs")
        messages = body.get("messages", [])
        require(len(messages) == 1 and messages[0].get("role") == "user", f"{scenario}: unexpected message contract")
        turns, frames = record["turns"], record["frames"]
        require(len(turns) == 1 and turns[0]["observedStep"] == 30, f"{scenario}: incorrect turn boundary")
        turn = turns[0]
        require(messages[0].get("content") == turn["prompt"], f"{scenario}: retained prompt differs from sent body")
        require(turn["backend"] == "ollama" and turn["model"] == MODEL, f"{scenario}: request identity missing")
        require(all(all(value == 0 for value in frame["input"][18:66]) for frame in frames[:30]),
                f"{scenario}: semantic feedback appeared before reply")
        if scenario == "success":
            require(completed.returncode == 0 and record["status"] == "completed", "success: run did not finish")
            require(len(frames) == 31 and turn["status"] == "completed", "success: incorrect completion count")
            require(turn.get("applicationStep") == 31 and frames[30].get("semanticTurnID") == 1,
                    "success: reply not applied at next boundary")
            require(turn.get("reply") == TEXT and turn.get("rawReply") == TEXT, "success: reply not retained")
            require(turn.get("providerModel") == PROVIDER_MODEL and turn.get("tokenCount") == 15,
                    "success: provider identity or count missing")
            require(frames[30]["input"][18:66] == turn["semanticVector"] and any(turn["semanticVector"]),
                    "success: actual applied feedback differs")
        else:
            require(completed.returncode == 1 and record["status"] == "failed", f"{scenario}: failure did not stop run")
            require(len(frames) == 30 and turn["status"] == "failed", f"{scenario}: failed turn advanced state")
            require(turn.get("applicationStep") is None and turn.get("semanticVector") is None
                    and turn.get("encodedFeatures") is None and turn.get("reply") is None,
                    f"{scenario}: failed/partial reply became feedback")
            require(all(frame.get("semanticTurnID") is None for frame in frames), f"{scenario}: false feedback linkage")
            if scenario in ("partial", "length"):
                require(turn.get("rawReply") == TEXT and turn.get("providerModel") == PROVIDER_MODEL,
                        f"{scenario}: incomplete text or provider identity not retained")
                require(turn.get("stopReason") == ("length" if scenario == "length" else "stop"),
                        f"{scenario}: stop reason not retained")
            else:
                require(turn.get("rawReply") is None, f"{scenario}: failed HTTP response became raw model text")
        # Exercise the exported-record verifier as a distinct CLI invocation.
        verification = subprocess.run([str(cli), "verify", str(output_path)], capture_output=True,
                                      text=True, timeout=30, check=False)
        require(verification.returncode == 0, f"{scenario}: retained record cannot verify ({verification.stderr[-1000:]})")
        return {"scenario": scenario, "passed": True, "http_requests": len(captures),
                "request_method": request["method"], "request_path": request["path"],
                "request_body_bytes": request["body_bytes"], "request_body_sha256": request["body_sha256"],
                "explicit_model": MODEL, "stream": body["stream"], "num_predict": body["options"]["num_predict"],
                "exit_code": completed.returncode, "run_status": record["status"],
                "frames": len(frames), "turn_status": turn["status"], "application_step": turn.get("applicationStep"),
                "raw_reply_retained": turn.get("rawReply") == TEXT,
                "provider_model": turn.get("providerModel"), "stop_reason": turn.get("stopReason"),
                "exported_record_verifies": True,
                "redirect_followed": any(item["path"] == "/redirected" for item in captures)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    cli = args.cli.resolve(strict=True)
    sources = [pathlib.Path(__file__).resolve(), ROOT / "llm/Language.swift", ROOT / "stages/EssentialsSession.swift",
               ROOT / "stages/RunTypes.swift", ROOT / "stages/Verification.swift", ROOT / "runner/Main.swift"]
    before = {str(path.relative_to(ROOT.parent)): sha256(path) for path in sources}
    binary_hash = sha256(cli)
    with tempfile.TemporaryDirectory(prefix="essentials-http-smoke-") as directory:
        cases = [run_case(cli, pathlib.Path(directory), scenario)
                 for scenario in ("success", "partial", "length", "http_error", "redirect")]
    require(sha256(cli) == binary_hash, "CLI changed during qualification")
    require(before == {str(path.relative_to(ROOT.parent)): sha256(path) for path in sources}, "Source changed during qualification")
    report = {"schema": "essentials.http_smoke.v1", "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "passed": True, "case_count": len(cases), "cases": cases,
              "cli_path": str(cli), "cli_sha256": binary_hash, "source_sha256": before,
              "fixture_boundary": "New ephemeral 127.0.0.1 servers only; no existing endpoints, model calls, pulls, or service changes.",
              "limits": {"request_body_bytes": BODY_LIMIT, "request_captures_per_server": CAPTURE_LIMIT,
                         "subprocess_timeout_seconds": 30, "cases": 5},
              "rerun": "python3 essentials/tests/http_smoke.py --cli '/path/to/final/essentials-run' --output 'native/ReservoirScope/validation/0.8.0/http-smoke.json'"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"HTTP smoke: {len(cases)}/{len(cases)} passed; receipt {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
