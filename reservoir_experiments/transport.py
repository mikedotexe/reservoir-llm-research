"""Bounded Ollama transport; numeric loopback only, no retries or redirects."""
from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import re
import socket
import threading
import time
from urllib.parse import urlsplit

MAX_RESPONSE_BYTES = 1024 * 1024


class TransportError(RuntimeError):
    def __init__(self, code: str, message: str, partial: bytes = b""):
        super().__init__(message)
        self.code = code
        self.partial = partial


def endpoint_parts(endpoint: str) -> tuple[str, int]:
    parsed = urlsplit(endpoint)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
            or parsed.username or parsed.password or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        raise ValueError("Endpoint must be http://127.0.0.1:<port> without a path")
    try:
        port = parsed.port or 11434
    except ValueError as exc:
        raise ValueError("Invalid endpoint port") from exc
    if not 1 <= port <= 65535:
        raise ValueError("Invalid endpoint port")
    return "127.0.0.1", port


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")


def decode_response(raw: bytes, model: str, max_tokens: int) -> dict:
    """Provider completion, not semantic/forecast correctness.

    Optional prompt metadata is retained without making malformed metadata a
    completion failure. Matches the frozen desktop completion boundary.
    """
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get("done"), bool):
            raise ValueError("missing boolean done")
        text = value["message"]["content"]
        if not isinstance(text, str):
            raise ValueError("non-string message content")
        provider_model = value.get("model")
        if provider_model is not None and not isinstance(provider_model, str):
            raise ValueError("non-string model")
        if value.get("done_reason") is not None and not isinstance(value["done_reason"], str):
            raise ValueError("non-string done_reason")
        if provider_model is not None and provider_model != model:
            raise TransportError("model-identity", "Provider returned a different model", raw)
        count = value.get("eval_count")
        if count is not None and (type(count) is not int or not -(2**63) <= count < 2**63):
            raise ValueError("invalid eval_count")
        count_valid = count is None or (type(count) is int and 0 <= count <= max_tokens)
        complete = value["done"] and value.get("done_reason") != "length" and count_valid
        status = "complete" if complete and text.strip() else ("empty" if complete else "incomplete")
        return {"status": status, "complete": complete and bool(text.strip()), "text": text,
                "provider_model": provider_model, "stop_reason": value.get("done_reason"),
                "eval_count": count, "prompt_eval_count": value.get("prompt_eval_count"),
                "total_duration": value.get("total_duration"),
                "load_duration": value.get("load_duration"),
                "prompt_eval_duration": value.get("prompt_eval_duration"),
                "eval_duration": value.get("eval_duration")}
    except TransportError:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        return {"status": "invalid_response", "complete": False, "text": None,
                "error": f"Invalid nonstreaming response envelope: {exc}"}


class OllamaTransport:
    def __init__(self, endpoint: str, *, max_response_bytes: int = MAX_RESPONSE_BYTES):
        self.endpoint = endpoint
        self.host, self.port = endpoint_parts(endpoint)
        self.max_response_bytes = max_response_bytes

    def request(self, method: str, path: str, body: bytes | None = None,
                *, timeout: float = 180) -> bytes:
        if path not in ("/api/chat", "/api/version", "/api/tags", "/api/show"):
            raise ValueError("Unrecognized research endpoint")
        if not 0 < timeout <= 180:
            raise ValueError("Deadline must be positive and at most 180 seconds")
        deadline = time.monotonic() + timeout
        conn = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        partial = bytearray()
        timer = None
        response = None
        expired = threading.Event()
        try:
            conn.connect()
            sock = conn.sock

            def expire():
                expired.set()
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(max(.001, deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            conn.request(method, path, body=body,
                         headers={"Content-Type": "application/json", "Connection": "close"})
            response = conn.getresponse()
            length = response.getheader("Content-Length")
            if length is not None and int(length) > self.max_response_bytes:
                raise TransportError("response-size", "Provider response exceeds byte limit")
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or expired.is_set():
                    raise TransportError("timeout", "Total request deadline exceeded", bytes(partial))
                sock.settimeout(remaining)
                chunk = response.read1(min(65536, self.max_response_bytes + 1 - len(partial)))
                if not chunk:
                    break
                partial.extend(chunk)
                if len(partial) > self.max_response_bytes:
                    raise TransportError("response-size", "Provider response exceeds byte limit",
                                         bytes(partial[:self.max_response_bytes]))
                if response.isclosed():
                    break
            if expired.is_set() or time.monotonic() >= deadline:
                raise TransportError("timeout", "Total request deadline exceeded", bytes(partial))
            if response.status != 200:
                raise TransportError("http-status", f"Provider returned HTTP {response.status}", bytes(partial))
            return bytes(partial)
        except TransportError:
            raise
        except (OSError, http.client.HTTPException, ValueError) as exc:
            code = "timeout" if expired.is_set() or time.monotonic() >= deadline else "connection"
            raise TransportError(code, f"Local request failed: {type(exc).__name__}: {exc}", bytes(partial)) from exc
        finally:
            if timer:
                timer.cancel()
            if response:
                response.close()
            conn.close()

    def generate(self, request: bytes, *, timeout: float = 180) -> bytes:
        return self.request("POST", "/api/chat", request, timeout=timeout)

    def identity(self, model: str) -> dict:
        runtime = json.loads(self.request("GET", "/api/version", timeout=15))
        inventory = json.loads(self.request("GET", "/api/tags", timeout=15))
        matches = [x for x in inventory.get("models", []) if x.get("name") == model or x.get("model") == model]
        if len(matches) != 1 or not matches[0].get("digest"):
            raise TransportError("model-unavailable", "Selected model must have exactly one inventory digest")
        shown = json.loads(self.request("POST", "/api/show", json_bytes({"model": model}), timeout=15))
        return {"endpoint": self.endpoint, "runtime": runtime,
                "model": matches[0], "show": shown, "local_metadata": local_metadata(model)}


def local_metadata(model: str) -> dict:
    """Capture small manifest/config/template/parameter bytes, never full weights."""
    parts = model.rsplit(":", 1)
    name, tag = parts if len(parts) == 2 else (model, "latest")
    if any(p in ("", ".", "..") for p in (name + "/" + tag).split("/")):
        raise ValueError("Unsafe model name")
    name_parts = name.split("/")
    if len(name_parts) == 1:
        name_parts = ["registry.ollama.ai", "library", *name_parts]
    elif len(name_parts) == 2:
        name_parts = ["registry.ollama.ai", *name_parts]
    root = Path.home() / ".ollama" / "models"
    path = root.joinpath("manifests", *name_parts, tag)
    if not path.is_file():
        return {"available": False}
    if path.stat().st_size > MAX_RESPONSE_BYTES:
        raise ValueError("Model manifest exceeds metadata limit")
    raw = path.read_bytes()
    manifest = json.loads(raw)
    result = {"available": True, "manifest_sha256": hashlib.sha256(raw).hexdigest(),
              "manifest_text": raw.decode(), "small_blobs": {}}
    for index, item in enumerate([manifest.get("config", {}), *manifest.get("layers", [])]):
        digest = item.get("digest", "")
        kind = item.get("mediaType", "")
        if index and not any(word in kind for word in ("config", "template", "params", "system")):
            continue
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ValueError("Malformed local model layer digest")
        blob = root / "blobs" / digest.replace(":", "-")
        if blob.stat().st_size > MAX_RESPONSE_BYTES:
            raise ValueError("Model metadata blob exceeds size limit")
        data = blob.read_bytes()
        if len(data) > MAX_RESPONSE_BYTES or hashlib.sha256(data).hexdigest() != digest[7:]:
            raise ValueError("Invalid model metadata blob")
        result["small_blobs"][digest] = {"media_type": kind, "text": data.decode("utf-8")}
    return result
