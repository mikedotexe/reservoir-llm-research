"""Read-only normalization of legacy jobs and documented v1 generation attempts.

Only fixed local companions and verified system-prompt hashes are opened. Artifact
paths are evidence strings, never read instructions. Availability means usable
recorded text is retained separately; availability requires complete adapted messages.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Iterator

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
_SHA = re.compile(r"[0-9a-fA-F]{64}\Z")
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_STUB = "Action-level LLM job. The existing action finalizer owns prompt construction, validation, artifacts, and NEXT extraction."


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: Path, budget: list[int], warnings: list[str]) -> str | None:
    """Open each path component without following symlinks; bound total input."""
    fds: list[int] = []
    try:
        absolute = Path(os.path.abspath(path))
        fd = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
        fds.append(fd)
        for part in absolute.parts[1:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            fds.append(fd)
        fd = os.open(absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        fds.append(fd)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("not a regular file")
        if os.fstat(fd).st_size > budget[0]:
            raise ValueError("read budget exceeded")
        with os.fdopen(os.dup(fd), "rb") as handle:
            data = handle.read(budget[0] + 1)
        if len(data) > budget[0]:
            raise ValueError("read budget exceeded")
        budget[0] -= len(data)
        return data.decode("utf-8")
    except (OSError, ValueError, UnicodeError) as exc:
        warnings.append(f"{path.name}: {type(exc).__name__}: {exc}")
        return None
    finally:
        for fd in reversed(fds):
            os.close(fd)


def _when(value: object, warnings: list[str], *, milliseconds: bool = False) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            result = float(value) / (1000 if milliseconds else 1)
            if math.isfinite(result):
                return result
        except OverflowError:
            pass
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                return parsed.timestamp()
            warnings.append("timestamp has no timezone; not assumed local or UTC")
            return None
        except (ValueError, OverflowError):
            pass
    warnings.append("missing or invalid recorded timestamp")
    return None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _stub(text: str) -> bool:
    stripped = text.strip()
    return stripped == _STUB or bool(re.fullmatch(r"(?:<stub(?:\s[^>]*)?>.*|\[stub\]|stub)", stripped, re.I | re.S))


def _messages(raw: dict, path: Path, budget: list[int], warnings: list[str]) -> tuple[str | None, dict]:
    messages = raw.get("messages")
    complete = isinstance(messages, list) and bool(messages)
    resolved, missing = [], []
    root = path.parent.parent if _DAY.fullmatch(path.parent.name) else path.parent
    for index, message in enumerate(messages if isinstance(messages, list) else []):
        if not isinstance(message, dict) or not isinstance(message.get("role"), str):
            complete = False
            missing.append(index)
            continue
        content = _text(message.get("content"))
        digest = message.get("content_sha256")
        if content is None and isinstance(digest, str) and _SHA.fullmatch(digest) and message["role"] == "system":
            content = _read(root / "system_prompts" / f"{digest.lower()}.txt", budget, warnings)
        try:
            verified = isinstance(digest, str) and bool(_SHA.fullmatch(digest)) and content is not None and _sha(content) == digest.lower()
        except UnicodeError:
            verified = False
        if digest is not None and not verified:
            warnings.append(f"message {index}: unresolved or mismatched content_sha256")
            content = None
        if content is None:
            complete = False
            missing.append(index)
            continue
        if isinstance(message.get("chars"), int) and message["chars"] != len(content):
            complete = False
            warnings.append(f"message {index}: recorded character count mismatch")
        resolved.append({"role": message["role"], "content": content})
    source = raw.get("messages_source")
    metadata = {"prompt_status": "complete_recorded_messages" if complete else "partial" if resolved else "missing",
                "exact_prompt": bool(complete and source == "adapted" and raw.get("schema_version") == 1), "missing_message_indices": missing,
                "messages_source": source, "resolved_messages": resolved,
                "prompt_representation": "role-labeled recorded messages; server token template not verified"}
    if source == "reconstructed":
        metadata["prompt_status"] = "reconstructed" if complete else metadata["prompt_status"]
    if not complete:
        warnings.append("complete prompt unavailable")
    return ("\n\n".join(f"[{m['role']}]\n{m['content']}" for m in resolved) if resolved else None), metadata


def read_generation(path: Path, being: str, max_bytes: int = DEFAULT_MAX_BYTES) -> dict:
    """Return a normalized record, retaining malformed/failed attempts with warnings.

    ``occurred_at`` uses recorded creation time, not inferred journal time. IDs
    distinguish retries sharing one generation_id. Input paths should be canonical
    (without symlink components), including on systems where /tmp is a symlink.
    """
    if not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    path = Path(path)
    warnings: list[str] = []
    budget = [max_bytes]
    legacy = path.name == "job.json"
    fmt = "legacy_job" if legacy else "generation_v1"
    result = {"id": f"{being}:{fmt}:path:{_sha(str(path.absolute()))}", "being": being,
              "occurred_at": None, "lane": None, "backend": None, "status": "unreadable",
              "prompt_text": None, "prompt_available": 0, "response_text": None,
              "response_sha256": None, "journal_refs": [], "metadata": {"format": fmt, "source_path": str(path.absolute())},
              "warnings": warnings}
    text = _read(path, budget, warnings)
    if text is None:
        return result
    try:
        raw = json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant {value}")))
        if not isinstance(raw, dict):
            raise ValueError("record must be a JSON object")
        # Reject escaped lone surrogates before returning strings to SQLite/UTF-8.
        json.dumps(raw, ensure_ascii=False).encode("utf-8")
    except (ValueError, RecursionError) as exc:
        result["status"] = "malformed"
        warnings.append(f"invalid JSON record: {exc}")
        return result
    metadata = result["metadata"]
    metadata.update({"source_record": {k: v for k, v in raw.items() if k not in {"messages", "response_text"}},
                     "prompt_status": "missing", "exact_prompt": False})
    source_id = _text(raw.get("job_id" if legacy else "generation_id"))
    if source_id:
        attempt = raw.get("attempt_index")
        attempt = attempt if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt >= 0 else path.stem
        suffix = "" if legacy else f":a{attempt}"
        result["id"] = f"{being}:{fmt}:{source_id}{suffix}"
    else:
        warnings.append("source record identifier missing; using path identity")
    if raw.get("being", raw.get("system", being)) != being:
        warnings.append("record being differs from selected source being")
    if raw.get("schema_version") not in (None, 1):
        warnings.append("unrecognized schema version; known fields only")
    stamp = raw.get("created_at") if legacy else raw.get("created_at_unix_ms", raw.get("created_at"))
    result.update(occurred_at=_when(stamp, warnings, milliseconds=not legacy and "created_at_unix_ms" in raw),
                  lane=_text(raw.get("call_kind" if legacy else "lane")), backend=_text(raw.get("backend")),
                  status=_text(raw.get("status")) or "unknown")
    if legacy:
        prompt = _read(path.parent / "prompt.txt", budget, warnings)
        response = _read(path.parent / "result.txt", budget, warnings)
        if prompt is not None and _stub(prompt):
            metadata.update(prompt_status="stub", legacy_prompt_stub=prompt)
            prompt = None
        elif prompt is not None and prompt.strip():
            metadata["prompt_status"] = "captured_legacy"
            metadata["prompt_representation"] = "stored prompt.txt; full adapted request not established"
        else:
            prompt = None
        # Minime action-finalizer summaries are never generated language evidence.
        if response is not None and re.fullmatch(r"Executed autonomous action `[^`]+`\.?\s*", response):
            metadata["legacy_result_summary"] = response
            response = None
    else:
        prompt, prompt_metadata = _messages(raw, path, budget, warnings)
        metadata.update(prompt_metadata)
        response = _text(raw.get("response_text"))
    result.update(prompt_text=prompt, prompt_available=int(metadata["exact_prompt"]), response_text=response)
    if response is not None:
        try:
            result["response_sha256"] = _sha(response)
        except UnicodeError:
            warnings.append("response contains invalid Unicode; response hash unavailable")
        if raw.get("response_sha256") is not None and raw["response_sha256"] != result["response_sha256"]:
            warnings.append("response_sha256 mismatch; using hash computed from recorded response")
    elif raw.get("response_sha256"):
        metadata["unverified_response_sha256"] = raw["response_sha256"]
    links = raw.get("artifact_refs" if legacy else "linked_artifacts")
    for link in links if isinstance(links, list) else []:
        if isinstance(link, dict) and link.get("kind") == "journal":
            ref = _text(link.get("path_or_uri")) or _text(link.get("path")) or _text(link.get("file_path"))
            if ref and ref not in result["journal_refs"]:
                result["journal_refs"].append(ref)
    return result


def discover_generation_files(root: Path) -> Iterator[Path]:
    """Yield recognized records in deterministic directory order, without symlinks.

    Accept a jobs/generations directory or a narrower day/job directory. This
    walks metadata only; callers select date windows and limits before reading.
    """
    root = Path(root)
    if root.is_symlink():
        return
    if root.is_file():
        if root.name == "job.json" or (root.name.startswith("gen_") and root.suffix == ".json"):
            yield root
        return
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                children = sorted(entries, key=lambda item: item.name)
        except OSError:
            continue
        dirs = []
        for entry in children:
            if entry.is_file(follow_symlinks=False) and (entry.name == "job.json" or (entry.name.startswith("gen_") and entry.name.endswith(".json"))):
                yield Path(entry.path)
            elif entry.is_dir(follow_symlinks=False) and entry.name != "system_prompts":
                dirs.append(Path(entry.path))
        pending.extend(reversed(dirs))
