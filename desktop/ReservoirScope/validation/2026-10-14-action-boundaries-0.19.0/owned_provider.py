#!/usr/bin/env python3
"""Bounded synthetic Ollama-shaped fixture; never starts or contacts a model.

Run only by explicit operator action. A new target/qa directory receives exact
response bytes and bounded request metadata. No prompt bodies are logged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import socket
import time

MODEL = "reservoir-fixture:input-evidence-0.16"
MAX_REQUEST_BYTES = 1_048_576
MAX_CHAT_REQUESTS = 5
MAX_HTTP_REQUESTS = 32
DESKTOP = Path(__file__).resolve().parents[2]
CASES = (
    {"name": "wide-reported", "value": 9_007_199_254_740_993, "expected": "reported"},
    {"name": "absent", "expected": "absent"},
    {"name": "malformed-string", "value": "2450", "expected": "unusable/wrongType"},
    {"name": "maximum-u64", "value": 18_446_744_073_709_551_615, "expected": "reported"},
    {"name": "incomplete-reported", "value": 321, "expected": "reported", "complete": False},
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def response_for(index: int) -> tuple[dict, bytes]:
    if not 1 <= index <= MAX_CHAT_REQUESTS:
        raise ValueError("fixed synthetic response sequence exhausted")
    case = CASES[index - 1]
    body = {
        "model": MODEL,
        "done": case.get("complete", True),
        "done_reason": "stop" if case.get("complete", True) else "length",
        "eval_count": 32,
        "message": {"role": "assistant", "content": (
            f"This is synthetic input-evidence fixture reply {index}. "
            "The optional provider count is separate from the writing and numerical state. "
            "These words are fixed test material, not a model observation."
        )},
    }
    if "value" in case:
        body["prompt_eval_count"] = case["value"]
    return case, json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def validate_request(raw: bytes) -> dict:
    if not 0 < len(raw) <= MAX_REQUEST_BYTES:
        raise ValueError("request byte bound")
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("request must be an object")
    messages = body.get("messages")
    if (body.get("model") != MODEL or body.get("stream") is not False
            or body.get("options") != {"num_predict": 1024, "temperature": 0, "num_ctx": 8192}
            or "format" in body
            or not isinstance(messages, list) or len(messages) != 1
            or not isinstance(messages[0], dict) or messages[0].get("role") != "user"
            or not isinstance(messages[0].get("content"), str)):
        raise ValueError("request differs from the frozen sustained fixture contract")
    prompt = messages[0]["content"].encode("utf-8")
    return {"requestBytes": len(raw), "requestSha256": digest(raw),
            "promptBytes": len(prompt), "promptSha256": digest(prompt),
            "model": body["model"], "options": body["options"], "stream": False}


def create_output(path: Path) -> Path:
    qa = (DESKTOP / "target/qa").resolve()
    output = path.absolute()
    # Existing parents must not redirect the selected output through a symlink.
    if output != output.resolve() or qa not in output.parents:
        raise ValueError("output must be a new ordinary directory under this desktop target/qa")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    return output


def run(output: Path, lifetime: int) -> None:
    if not 1 <= lifetime <= 900:
        raise ValueError("lifetime must be 1..900 seconds")
    output = create_output(output)
    started = time.monotonic()
    chat_count = 0
    http_count = 0
    sent_count = 0
    stop_reason = "lifetime-expired"

    def log(value: dict) -> None:
        row = {"atUtc": datetime.now(timezone.utc).isoformat(),
               "monotonicNs": str(time.monotonic_ns()), **value}
        with (output / "requests.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *_):
            pass

        def respond(self, status: int, data: bytes) -> bool:
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return True
            except (BrokenPipeError, ConnectionResetError, socket.timeout):
                return False

        def do_GET(self):
            nonlocal http_count
            http_count += 1
            status = 200 if self.path == "/api/tags" else 404
            body = {"models": [{"name": MODEL, "model": MODEL,
                                "digest": "synthetic-no-model-weights"}]} if status == 200 else {"error": "unknown fixture path"}
            sent = self.respond(status, json.dumps(body).encode())
            log({"method": "GET", "path": self.path[:256], "status": status,
                 "socketWriteCompleted": sent})

        def do_POST(self):
            nonlocal http_count, chat_count, sent_count
            http_count += 1
            if self.path != "/api/chat":
                self.respond(404, b'{"error":"unknown fixture path"}')
                log({"method": "POST", "path": self.path[:256], "status": 404})
                return
            try:
                sizes = self.headers.get_all("Content-Length", [])
                if len(sizes) != 1 or self.headers.get("Transfer-Encoding") is not None:
                    raise ValueError("one bounded Content-Length required")
                size = int(sizes[0])
                if not 0 < size <= MAX_REQUEST_BYTES:
                    raise ValueError("request byte bound")
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise ValueError("short request")
                metadata = validate_request(raw)
                if chat_count >= MAX_CHAT_REQUESTS:
                    raise ValueError("fixed synthetic response sequence exhausted")
            except (ValueError, TypeError, KeyError, socket.timeout) as error:
                sent = self.respond(400, json.dumps({"error": str(error)}).encode())
                log({"method": "POST", "path": self.path, "status": 400,
                     "rejected": str(error), "socketWriteCompleted": sent})
                return
            chat_count += 1
            case, response = response_for(chat_count)
            filename = f"response-{chat_count:02d}-{case['name']}.json"
            with (output / filename).open("xb") as f:
                f.write(response)
                f.flush()
                os.fsync(f.fileno())
            log({"method": "POST", "path": self.path, "request": chat_count,
                 "case": case, **metadata, "responseFile": filename,
                 "responseBytes": len(response), "responseSha256": digest(response)})
            sent = self.respond(200, response)
            sent_count += int(sent)
            log({"response": chat_count, "status": 200, "socketWriteCompleted": sent})

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        server.timeout = 0.25
        identity = {"endpoint": f"http://127.0.0.1:{server.server_port}", "model": MODEL,
                    "pid": os.getpid(), "synthetic": True, "startedAtUtc": datetime.now(timezone.utc).isoformat(),
                    "lifetimeSeconds": lifetime, "maximumChatRequests": MAX_CHAT_REQUESTS,
                    "maximumHttpRequests": MAX_HTTP_REQUESTS, "scriptSha256": digest(Path(__file__).read_bytes()),
                    "scenario": [case["name"] for case in CASES]}
        with (output / "endpoint.json").open("x") as f:
            json.dump(identity, f, indent=2); f.write("\n")
        log({"lifecycle": "started", **identity})
        print(json.dumps(identity), flush=True)
        while time.monotonic() - started < lifetime:
            if (output / "stop-request").exists():
                stop_reason = "explicit-stop-file"
                break
            if http_count >= MAX_HTTP_REQUESTS:
                stop_reason = "http-request-limit"
                break
            server.handle_request()
    log({"lifecycle": "stopped", "reason": stop_reason,
         "elapsedSeconds": time.monotonic() - started,
         "chatRequests": chat_count, "httpRequests": http_count, "responsesWritten": sent_count})


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("--lifetime-seconds", type=int, default=900)
    args = p.parse_args()
    run(args.output, args.lifetime_seconds)


if __name__ == "__main__":
    main()
