"""Immutable branch runner for research-only, local language-model studies."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import tempfile
import time

from .transport import OllamaTransport, TransportError, decode_response, endpoint_parts, json_bytes

REPO = Path(__file__).resolve().parent.parent
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\Z")
REFERENCE = re.compile(r"\{\{output:([A-Za-z0-9][A-Za-z0-9_.-]{0,159})\}\}")
MAX_INPUT_BYTES = 8 * 1024 * 1024
CORE_FILES = ("__init__.py", "__main__.py", "runner.py", "transport.py")


class ExperimentError(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(stable_read(path))


def stable_read(path: Path, limit: int = MAX_INPUT_BYTES) -> bytes:
    path = Path(path)
    if path.is_symlink():
        raise ExperimentError(f"Symlink input refused: {path}")
    before = path.stat()
    if not path.is_file() or before.st_size > limit:
        raise ExperimentError(f"Input is not a bounded regular file: {path}")
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
        opened = os.fstat(handle.fileno())
    after = path.stat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if len(data) > limit or fields(before) != fields(opened) or fields(before) != fields(after):
        raise ExperimentError(f"Input changed during capture: {path}")
    return data


def write_once(path: Path, data: bytes):
    """Fsynced atomic creation; existing receipts are never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, value):
    write_once(path, json_bytes(value))


def guard_output(path: Path, repository: Path = REPO) -> Path:
    repository = repository.resolve()
    path = path.expanduser().absolute()
    target = path.resolve()
    if repository not in target.parents:
        raise ExperimentError("Experiment output must remain inside the research checkout")
    for parent in (path, *path.parents):
        if parent.resolve() == repository:
            break  # macOS /var aliases above the selected repository are harmless.
        if parent.is_symlink():
            raise ExperimentError("Output cannot traverse a symlink")
    default = repository / "research" / "outputs"
    if target == default or default in target.parents:
        return target
    relative = str(target.relative_to(repository))
    ignored = subprocess.run(["git", "check-ignore", "--no-index", "--", relative],
                             cwd=repository, capture_output=True)
    if ignored.returncode != 0:
        raise ExperimentError("Use research/outputs or an explicitly Git-ignored local directory")
    return target


def validate_protocol(protocol: dict) -> list[str]:
    if protocol.get("schema_version") != 1:
        raise ExperimentError("Only experiment protocol schema_version 1 is supported")
    for field in ("id", "study", "split", "model"):
        if not isinstance(protocol.get(field), str) or not protocol[field].strip():
            raise ExperimentError(f"Missing protocol {field}")
    endpoint_parts(protocol.get("endpoint", "http://127.0.0.1:11434"))
    deadline = protocol.get("deadline_seconds", 180)
    if type(deadline) not in (int, float) or not 0 < deadline <= 180:
        raise ExperimentError("deadline_seconds must be positive and at most 180")
    options = protocol.get("options", {})
    if not isinstance(options, dict):
        raise ExperimentError("options must be an object")
    if any(k in options for k in ("seed", "num_predict")):
        raise ExperimentError("seed and num_predict belong to individual nodes")
    context = options.get("num_ctx", 16384)
    if type(context) is not int or not 512 <= context <= 32768:
        raise ExperimentError("num_ctx must be 512–32768")
    if "think" in protocol and not isinstance(protocol["think"], (bool, str)):
        raise ExperimentError("think must be a boolean or provider-supported string")
    nodes = protocol.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ExperimentError("A protocol requires nodes")
    by_id = {}
    for node in nodes:
        nid = node.get("id")
        if not isinstance(nid, str) or not SAFE_ID.fullmatch(nid) or nid in by_id:
            raise ExperimentError(f"Unsafe or duplicate node ID: {nid!r}")
        if not all(isinstance(node.get(k), str) and node[k] for k in ("episode", "condition", "kind")):
            raise ExperimentError(f"{nid}: episode, condition and kind are required")
        if type(node.get("seed")) is not int or not 0 <= node["seed"] < 2**63:
            raise ExperimentError(f"{nid}: seed must be a nonnegative signed-64-bit integer")
        max_tokens = node.get("max_tokens", 1024)
        if type(max_tokens) is not int or not 1 <= max_tokens <= 2048 or max_tokens >= context:
            raise ExperimentError(f"{nid}: invalid output token budget")
        messages = node.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ExperimentError(f"{nid}: messages are required")
        for msg in messages:
            if (not isinstance(msg, dict) or set(msg) != {"role", "content"}
                    or msg["role"] not in ("system", "user", "assistant")
                    or not isinstance(msg["content"], str)):
                raise ExperimentError(f"{nid}: messages must contain only role and string content")
            stripped = REFERENCE.sub("", msg["content"])
            if "{{output:" in stripped or "{{truth:" in stripped:
                raise ExperimentError(f"{nid}: malformed output reference or forbidden truth reference")
        refs = {match for msg in messages for match in REFERENCE.findall(msg["content"])}
        for field in ("inputs", "after"):
            value = node.get(field, [])
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value) or len(set(value)) != len(value):
                raise ExperimentError(f"{nid}: invalid {field}")
        if refs != set(node.get("inputs", [])):
            raise ExperimentError(f"{nid}: declared inputs must exactly equal text references")
        by_id[nid] = node
    for node in nodes:
        for parent in set(node.get("inputs", []) + node.get("after", [])):
            if parent not in by_id:
                raise ExperimentError(f"Unknown dependency {parent}")
        for parent in node.get("inputs", []):
            if by_id[parent]["kind"] == "forecast" and node["kind"] != "reactivity":
                raise ExperimentError(f"Forecast leakage into {node['id']}")
    remaining, schedule, completed = list(nodes), [], set()
    while remaining:
        eligible = next((n for n in remaining if set(n.get("inputs", []) + n.get("after", [])) <= completed), None)
        if eligible is None:
            raise ExperimentError("Dependency graph contains a cycle")
        schedule.append(eligible["id"])
        completed.add(eligible["id"])
        remaining.remove(eligible)
    json_bytes(protocol)  # reject NaN and non-serializable values before writing
    return schedule


def prepare(protocol_path: Path, out: Path, *, repository: Path = REPO) -> dict:
    raw = stable_read(Path(protocol_path))
    protocol = json.loads(raw)
    schedule = validate_protocol(protocol)
    out = guard_output(Path(out), repository)
    if out.exists():
        raise ExperimentError("Preparation refuses an existing destination")
    source_data = []
    for entry in protocol.get("sources", []):
        item = {"path": entry} if isinstance(entry, str) else entry
        path = Path(item["path"]).expanduser()
        if not path.is_absolute():
            path = Path(protocol_path).absolute().parent / path
        data = stable_read(path)
        digest = sha(data)
        if item.get("sha256") and item["sha256"] != digest:
            raise ExperimentError(f"Source hash mismatch: {path}")
        source_data.append((str(path.absolute()), data))
    qualification_data = []
    for entry in protocol.get("context_qualifications", []):
        path = Path(entry).expanduser()
        if not path.is_absolute():
            path = Path(protocol_path).absolute().parent / path
        record = read_qualification(path)
        captured = {name: stable_read(path / name) for name in (*record["files"], "qualification.json")}
        qualification_data.append((record, captured))
    out.mkdir(parents=True, mode=0o700)
    files = {}
    def save(relative, data):
        write_once(out / relative, data)
        files[relative] = sha(data)
    save("protocol.json", json_bytes(protocol))
    save("original-protocol.json", raw)
    sources = []
    for i, (path, data) in enumerate(source_data):
        relative = f"sources/{i:04d}.bin"
        save(relative, data)
        sources.append({"original_path": path, "snapshot": relative, "sha256": sha(data)})
    code_hashes = {}
    for name in CORE_FILES:
        data = stable_read(Path(__file__).parent / name)
        save(f"code/{name}", data)
        code_hashes[name] = sha(data)
    qualifications = {}
    for index, (record, captured) in enumerate(qualification_data):
        relative = f"qualifications/{index:04d}"
        key = record["prompt_sha256"]
        if key in qualifications:
            raise ExperimentError("Duplicate context qualification for the same prompt")
        for name, data in captured.items():
            save(f"{relative}/{name}", data)
        qualifications[key] = relative
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, capture_output=True, text=True)
    manifest = {"schema_version": 1, "created_at": now(), "protocol_id": protocol["id"],
                "schedule": schedule, "files": files, "sources": sources,
                "code_hashes": code_hashes, "context_qualifications": qualifications,
                "git_head": git.stdout.strip() if git.returncode == 0 else None,
                "repository": str(Path(repository).resolve()), "opportunities": len(schedule)}
    write_json(out / "manifest.json", manifest)
    write_once(out / "manifest.sha256", (sha(json_bytes(manifest)) + "\n").encode())
    return manifest


def load_run(run: Path, *, check_code: bool = False) -> tuple[dict, dict]:
    run = Path(run)
    manifest_raw = stable_read(run / "manifest.json")
    if sha(manifest_raw) != stable_read(run / "manifest.sha256").decode().strip():
        raise ExperimentError("Manifest hash mismatch")
    manifest = json.loads(manifest_raw)
    for relative, digest in manifest["files"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ExperimentError("Unsafe snapshot path")
        if sha(stable_read(run / path)) != digest:
            raise ExperimentError(f"Snapshot hash mismatch: {relative}")
    if check_code:
        for name, digest in manifest["code_hashes"].items():
            if sha(stable_read(Path(__file__).parent / name)) != digest:
                raise ExperimentError(f"Runner source changed since preparation: {name}")
    protocol = read_json(run / "protocol.json")
    if validate_protocol(protocol) != manifest["schedule"]:
        raise ExperimentError("Frozen schedule does not match protocol")
    return manifest, protocol


def read_results(run: Path) -> dict[str, dict]:
    _, protocol = load_run(Path(run))
    results = {}
    for node in protocol["nodes"]:
        path = Path(run) / "nodes" / node["id"] / "result.json"
        if path.exists():
            results[node["id"]] = read_json(path)
    return results


def prompt_hash(body: dict) -> str:
    """Bind every request setting except seed, output budget, and probe context."""
    normalized = dict(body)
    normalized["options"] = {k: v for k, v in body["options"].items()
                             if k not in ("seed", "num_predict", "num_ctx")}
    return sha(json_bytes(normalized))


def context_qualifications(run: Path, manifest: dict) -> dict[str, dict]:
    return {key: read_qualification(Path(run) / relative)
            for key, relative in manifest.get("context_qualifications", {}).items()}


def render_request(protocol: dict, node: dict, results: dict[str, dict], *,
                   qualifications: dict | None = None, check_context: bool = True) -> bytes:
    def replace(match):
        parent = match.group(1)
        result = results.get(parent, {})
        if result.get("status") != "complete" or not isinstance(result.get("text"), str):
            raise ExperimentError(f"No complete text for dependency {parent}")
        return result["text"]
    messages = [{"role": msg["role"], "content": REFERENCE.sub(replace, msg["content"])}
                for msg in node["messages"]]
    options = dict(protocol.get("options", {}))
    options.setdefault("num_ctx", 16384)
    options.setdefault("temperature", .7)
    options.update(seed=node["seed"], num_predict=node.get("max_tokens", 1024))
    body = {"model": protocol["model"], "stream": False, "messages": messages, "options": options}
    if "think" in protocol:
        body["think"] = protocol["think"]
    if "format" in node:
        body["format"] = node["format"]
    # Conservative byte bound includes a generous chat-template reserve. This is
    # a refusal bound, not a claim of exact tokenizer accounting.
    content_bytes = sum(len(msg["content"].encode("utf-8")) for msg in messages)
    if check_context and content_bytes + options["num_predict"] + 512 > options["num_ctx"]:
        qualified = (qualifications or {}).get(prompt_hash(body))
        if (qualified is None or qualified["planned_num_ctx"] != options["num_ctx"]
                or qualified["prompt_eval_count"] + options["num_predict"] + 512 >= options["num_ctx"]):
            raise ExperimentError("Prompt exceeds conservative context byte budget; exact empirical qualification required")
    return json_bytes(body)


def read_qualification(path: Path) -> dict:
    """Validate auditable evidence from an explicit larger-context instrument probe."""
    record = read_json(path / "qualification.json")
    expected = {"planned-request.json", "request.json", "response.raw", "identity.json", "dispatch.json"}
    if set(record.get("files", {})) != expected:
        raise ExperimentError("Context qualification has incomplete evidence")
    for name, digest in record["files"].items():
        if sha(stable_read(path / name)) != digest:
            raise ExperimentError(f"Context qualification hash mismatch: {name}")
    planned = read_json(path / "planned-request.json")
    probe = read_json(path / "request.json")
    response = read_json(path / "response.raw")
    dispatch = read_json(path / "dispatch.json")
    count = response.get("prompt_eval_count")
    planned_context = planned["options"]["num_ctx"]
    if (record.get("schema_version") != 1 or type(count) is not int or count <= 0
            or response.get("done") is not True or response.get("model") != planned["model"]
            or record.get("prompt_eval_count") != count
            or record.get("planned_num_ctx") != planned_context
            or record.get("qualification_num_ctx") != probe["options"]["num_ctx"]
            or probe["options"]["num_ctx"] < 2 * planned_context
            or probe["options"]["num_ctx"] > 32768
            or probe["options"]["num_predict"] != 1
            or record.get("prompt_sha256") != prompt_hash(planned)
            or prompt_hash(probe) != prompt_hash(planned)
            or record.get("identity_sha256") != record["files"]["identity.json"]
            or dispatch.get("identity_sha256") != record["identity_sha256"]
            or dispatch.get("request_sha256") != record["files"]["request.json"]
            or count + planned["options"]["num_predict"] + 512 >= planned_context):
        raise ExperimentError("Invalid or insufficient context qualification")
    return record


def qualify(protocol_path: Path, node_id: str, out: Path, *, qualification_num_ctx: int = 32768,
            repository: Path = REPO, transport=None) -> dict:
    """One explicitly authorized instrument call, never a study outcome or retry.

    Uses the exact static prompt at twice the planned context (up to 32768), with
    a one-token output budget. Success requires measured prompt count to fit the
    smaller planned context with the planned output budget and 512-token margin.
    """
    protocol = read_json(Path(protocol_path))
    validate_protocol(protocol)
    node = next((n for n in protocol["nodes"] if n["id"] == node_id), None)
    if node is None or node.get("inputs"):
        raise ExperimentError("Context qualification requires a known static node without inputs")
    planned = json.loads(render_request(protocol, node, {}, check_context=False))
    if type(qualification_num_ctx) is not int or not 2 * planned["options"]["num_ctx"] <= qualification_num_ctx <= 32768:
        raise ExperimentError("Qualification context must be at least twice planned context and at most 32768")
    out = guard_output(Path(out), repository)
    if out.exists():
        raise ExperimentError("Qualification refuses an existing destination; physical probes are never retried")
    endpoint = protocol.get("endpoint", "http://127.0.0.1:11434")
    client = transport or OllamaTransport(endpoint)
    _, port = endpoint_parts(endpoint)
    probe = json.loads(json_bytes(planned))
    probe["options"].update(num_ctx=qualification_num_ctx, num_predict=1)
    request = json_bytes(probe)
    with exclusive_lock(Path(repository) / "research" / "outputs" / f".provider-{port}.lock"):
        identity = json_bytes(client.identity(protocol["model"]))
        out.mkdir(parents=True, mode=0o700)
        write_once(out / "planned-request.json", json_bytes(planned))
        write_once(out / "request.json", request)
        write_once(out / "identity.json", identity)
        write_json(out / "dispatch.json", {"started_at": now(), "request_sha256": sha(request),
                                           "identity_sha256": sha(identity), "instrument_only": True})
        try:
            raw = client.generate(request, timeout=protocol.get("deadline_seconds", 180))
            write_once(out / "response.raw", raw)
        except TransportError as exc:
            if exc.partial:
                write_once(out / "response.raw", exc.partial)
            write_json(out / "failure.json", {"status": "transport_error", "error": str(exc), "error_code": exc.code})
            raise
        try:
            response = json.loads(raw)
            record = {"schema_version": 1, "instrument_only": True, "created_at": now(),
                      "prompt_sha256": prompt_hash(planned), "identity_sha256": sha(identity),
                      "planned_num_ctx": planned["options"]["num_ctx"],
                      "qualification_num_ctx": qualification_num_ctx,
                      "prompt_eval_count": response.get("prompt_eval_count"),
                      "files": {name: sha(stable_read(out / name)) for name in (
                          "planned-request.json", "request.json", "response.raw", "identity.json", "dispatch.json")}}
            write_json(out / "qualification.json", record)
            read_qualification(out)
        except (ValueError, KeyError, TypeError, AttributeError, ExperimentError) as exc:
            write_json(out / "failure.json", {"status": "invalid_qualification", "error": str(exc)})
            raise ExperimentError(f"Context qualification failed: {exc}") from exc
    return record


def decode_study_response(raw: bytes, protocol: dict, node: dict, request: bytes,
                          qualifications: dict) -> dict:
    result = decode_response(raw, protocol["model"], node.get("max_tokens", 1024))
    qualified = qualifications.get(prompt_hash(json.loads(request)))
    if qualified and result.get("prompt_eval_count") != qualified["prompt_eval_count"]:
        result.update(status="invalid_response", complete=False, error_code="context-count-mismatch",
                      error="Study prompt count differs from exact qualified prompt; batch stopped")
    return result


@contextmanager
def exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ExperimentError(f"Another runner owns {path.name}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def verify(run: Path) -> dict:
    run = Path(run)
    manifest, protocol = load_run(run)
    qualifications = context_qualifications(run, manifest)
    results = read_results(run)
    by_id = {n["id"]: n for n in protocol["nodes"]}
    verified = []
    for nid in manifest["schedule"]:
        node = by_id[nid]
        directory = run / "nodes" / nid
        result = results.get(nid)
        request_path = directory / "request.json"
        dispatch_path = directory / "dispatch.json"
        if request_path.exists():
            actual = stable_read(request_path)
            if actual != render_request(protocol, node, results, qualifications=qualifications):
                raise ExperimentError(f"Rendered request mismatch: {nid}")
        if dispatch_path.exists():
            dispatch = read_json(dispatch_path)
            if not request_path.exists() or dispatch["request_sha256"] != sha(stable_read(request_path)):
                raise ExperimentError(f"Dispatch request hash mismatch: {nid}")
            if (not (run / "identity.json").exists()
                    or dispatch.get("identity_sha256") != sha(stable_read(run / "identity.json"))):
                raise ExperimentError(f"Dispatch provider identity mismatch: {nid}")
            expected_parents = {p: sha(stable_read(run / "nodes" / p / "result.json"))
                                for p in node.get("inputs", [])}
            if dispatch.get("parent_result_sha256") != expected_parents:
                raise ExperimentError(f"Dispatch parent identity mismatch: {nid}")
        if result is None:
            continue
        if result.get("node_id") != nid:
            raise ExperimentError(f"Result node identity mismatch: {nid}")
        if result["status"] not in ("blocked", "ambiguous"):
            for field in ("episode", "condition", "kind", "seed"):
                if result.get(field) != node[field]:
                    raise ExperimentError(f"Result allocation mismatch: {nid}/{field}")
        for relative, digest in result.get("files", {}).items():
            if Path(relative).name != relative or sha(stable_read(directory / relative)) != digest:
                raise ExperimentError(f"Result evidence hash mismatch: {nid}/{relative}")
        if result["status"] == "blocked":
            if request_path.exists() or dispatch_path.exists():
                raise ExperimentError(f"Blocked node was dispatched: {nid}")
            unavailable = [p for p in node.get("inputs", []) if results.get(p, {}).get("status") != "complete"]
            if not unavailable:
                raise ExperimentError(f"Unsupported blocked result: {nid}")
        elif dispatch_path.exists() and (directory / "response.raw").exists() and result["status"] not in ("transport_error", "ambiguous"):
            decoded = decode_study_response(stable_read(directory / "response.raw"), protocol, node,
                                            stable_read(request_path), qualifications)
            for key, value in decoded.items():
                if result.get(key) != value:
                    raise ExperimentError(f"Response decode mismatch: {nid}/{key}")
        elif not dispatch_path.exists():
            raise ExperimentError(f"Result has no dispatch receipt: {nid}")
        verified.append(nid)
    if (run / "identity.json").exists():
        raw = stable_read(run / "identity.json")
        if sha(raw) != stable_read(run / "identity.sha256").decode().strip():
            raise ExperimentError("Provider identity hash mismatch")
    return {"valid": True, "protocol_id": protocol["id"], "opportunities": len(by_id),
            "verified_results": len(verified), "status": status(run, verify_first=False)}


def status(run: Path, *, verify_first: bool = True) -> dict:
    run = Path(run)
    if verify_first:
        verify(run)
    manifest, _ = load_run(run)
    results = read_results(run)
    states = {}
    for nid in manifest["schedule"]:
        directory = run / "nodes" / nid
        states[nid] = results[nid]["status"] if nid in results else (
            "ambiguous" if (directory / "dispatch.json").exists() else "pending")
    return {"protocol_id": manifest["protocol_id"], "opportunities": len(states),
            "counts": dict(Counter(states.values())), "nodes": states}


def run_protocol(run: Path, *, limit: int | None = None, transport=None,
                 identity_every: int = 20, progress=None) -> dict:
    """Execute without retries. Limit counts physical dispatches, not blocked nodes."""
    run = Path(run).resolve()
    manifest, protocol = load_run(run, check_code=True)
    qualifications = context_qualifications(run, manifest)
    guard_output(run, Path(manifest["repository"]))
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ExperimentError("limit must be nonnegative")
    if identity_every < 1:
        raise ExperimentError("identity_every must be positive")
    endpoint = protocol.get("endpoint", "http://127.0.0.1:11434")
    client = transport or OllamaTransport(endpoint)
    _, port = endpoint_parts(endpoint)
    lock_root = Path(manifest["repository"]) / "research" / "outputs"
    with exclusive_lock(run / ".run.lock"), exclusive_lock(lock_root / f".provider-{port}.lock"):
        verify(run)
        identity = client.identity(protocol["model"])
        identity_raw = json_bytes(identity)
        if any(q["identity_sha256"] != sha(identity_raw) for q in qualifications.values()):
            raise ExperimentError("Context qualification provider/model identity changed")
        if (run / "identity.json").exists():
            if stable_read(run / "identity.json") != identity_raw:
                raise ExperimentError("Provider/model identity changed; dispatch stopped")
        else:
            write_once(run / "identity.json", identity_raw)
            write_once(run / "identity.sha256", (sha(identity_raw) + "\n").encode())
        results = read_results(run)
        by_id = {n["id"]: n for n in protocol["nodes"]}
        dispatched = 0
        for nid in manifest["schedule"]:
            node = by_id[nid]
            directory = run / "nodes" / nid
            if nid in results:
                continue
            if (directory / "dispatch.json").exists():
                # A prior process stopped after marking dispatch. Never infer that
                # absence of a response means absence of an attempted request.
                results[nid] = {"node_id": nid, "status": "ambiguous", "complete": False,
                                "text": None, "recorded_at": now(),
                                "error": "Prior dispatch has no terminal receipt; never retried",
                                "files": {p: sha(stable_read(directory / p)) for p in (
                                    "request.json", "dispatch.json", "response.raw") if (directory / p).exists()}}
                write_json(directory / "result.json", results[nid])
                continue
            unavailable = [p for p in node.get("inputs", []) if results.get(p, {}).get("status") != "complete"]
            if unavailable:
                results[nid] = {"node_id": nid, "status": "blocked", "complete": False, "text": None,
                                "recorded_at": now(), "blocked_by": unavailable, "files": {}}
                write_json(directory / "result.json", results[nid])
                continue
            if limit is not None and dispatched >= limit:
                break
            if dispatched and dispatched % identity_every == 0:
                if json_bytes(client.identity(protocol["model"])) != identity_raw:
                    raise ExperimentError("Provider/model identity changed during batch")
            request = render_request(protocol, node, results, qualifications=qualifications)
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            if (directory / "request.json").exists():
                if stable_read(directory / "request.json") != request:
                    raise ExperimentError(f"Undispatched request changed: {nid}")
            else:
                write_once(directory / "request.json", request)
            parent_hashes = {p: sha(stable_read(run / "nodes" / p / "result.json")) for p in node.get("inputs", [])}
            dispatch = {"node_id": nid, "started_at": now(), "request_sha256": sha(request),
                        "identity_sha256": sha(identity_raw), "parent_result_sha256": parent_hashes,
                        "deadline_seconds": protocol.get("deadline_seconds", 180)}
            write_json(directory / "dispatch.json", dispatch)
            dispatched += 1
            started = time.monotonic()
            fatal = None
            try:
                raw = client.generate(request, timeout=dispatch["deadline_seconds"])
                write_once(directory / "response.raw", raw)
                result = decode_study_response(raw, protocol, node, request, qualifications)
                if result.get("error_code") == "context-count-mismatch":
                    fatal = ExperimentError(result["error"])
            except TransportError as exc:
                if exc.partial and not (directory / "response.raw").exists():
                    write_once(directory / "response.raw", exc.partial)
                result = {"status": "transport_error", "complete": False, "text": None,
                          "error_code": exc.code, "error": str(exc), "dispatch_uncertain": True}
                # A timeout may leave server-side work alive. Do not overlap the
                # next request or quietly continue through an unknown model state.
                fatal = exc
            result.update(node_id=nid, episode=node["episode"], condition=node["condition"],
                          kind=node["kind"], seed=node["seed"], finished_at=now(),
                          elapsed_seconds=time.monotonic() - started,
                          files={p.name: sha(stable_read(p)) for p in directory.iterdir()
                                 if p.name in ("request.json", "dispatch.json", "response.raw")})
            write_json(directory / "result.json", result)
            results[nid] = result
            if progress:
                progress({"node": nid, "status": result["status"], "dispatched": dispatched,
                          "elapsed_seconds": result["elapsed_seconds"]})
            if fatal:
                raise ExperimentError(f"Dispatch stopped after {nid}: {fatal}") from fatal
    result = status(run)
    result["dispatched_this_call"] = dispatched
    return result


def blind(run: Path, out: Path, *, seed: int = 20261024, kinds: list[str] | None = None) -> dict:
    """Preserve episode order internally; shuffle whole episode packets."""
    run = Path(run)
    verify(run)
    manifest, protocol = load_run(run)
    out = guard_output(Path(out), Path(manifest["repository"]))
    if out.exists():
        raise ExperimentError("Blind packet destination already exists")
    results = read_results(run)
    groups = {}
    for node in protocol["nodes"]:
        if kinds is not None and node["kind"] not in kinds:
            continue
        if node.get("metadata", {}).get("blind_selected", True) is False:
            continue
        result = results.get(node["id"], {})
        if result.get("text") is not None:
            # Paired conditions are separate packets; do not disclose their common episode.
            group = (node["episode"], node["condition"], node["seed"])
            groups.setdefault(group, []).append((node, result))
    packets = list(groups.values())
    random.Random(seed).shuffle(packets)
    out.mkdir(parents=True, mode=0o700)
    key, texts = [], ["# Blind reading packet\n\nAllocation labels are withheld. Text may reveal its conditions.\n"]
    for index, packet in enumerate(packets, 1):
        texts.append(f"\n## Episode {index}\n")
        for ordinal, (node, result) in enumerate(packet, 1):
            texts.append(f"\n### Passage {ordinal}\n\n{result['text']}\n")
            key.append({"episode_number": index, "passage": ordinal, "node_id": node["id"],
                        "episode": node["episode"], "condition": node["condition"], "seed": node["seed"],
                        "result_sha256": sha(stable_read(run / "nodes" / node["id"] / "result.json"))})
    write_once(out / "reading.md", "".join(texts).encode())
    write_json(out / "allocation-key.json", key)
    receipt = {"protocol_id": protocol["id"], "seed": seed, "packets": len(packets), "passages": len(key),
               "reading_sha256": sha(stable_read(out / "reading.md")),
               "key_sha256": sha(stable_read(out / "allocation-key.json"))}
    write_json(out / "receipt.json", receipt)
    return receipt
