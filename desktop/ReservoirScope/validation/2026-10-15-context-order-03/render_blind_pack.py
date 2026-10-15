#!/usr/bin/env python3
"""Render terminal diagnostic text without exposing condition/source metadata.

Offline only. Requires an explicitly hash-bound final runner result; never reads
prompts or contacts the app/provider. Mapping is sealed outside the blind folder
before either blind file is published. Readers must not inspect that mapping.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat


MAX_RESULT = 4 * 1024 * 1024
MAX_BODY = 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def read_bound(path: Path, maximum: int) -> bytes:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink input is not permitted")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise ValueError("Ordinary input file required")
        data = f.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("Input exceeds its bounded size")
    return data


def exclusive_write(path: Path, data: bytes) -> None:
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def response_text(body: bytes) -> tuple[str | None, str]:
    """Recover unique authored content even if unrelated optional keys duplicate."""
    class Pairs(list):
        pass

    def unique(obj: object, key: str) -> object:
        if not isinstance(obj, Pairs):
            raise ValueError("Not an object")
        matches = [v for k, v in obj if k == key]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous authored content")
        return matches[0]

    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=Pairs)
        text = unique(unique(value, "message"), "content")
        if not isinstance(text, str):
            raise ValueError("Content is not text")
        text.encode("utf-8")  # Reject unpaired surrogate escapes, never replace them.
        return text, "empty" if text == "" else "available"
    except (ValueError, UnicodeError, TypeError):
        return None, "unavailable_or_ambiguous_json_content"


def render(slots: list[dict], texts: list[str | None], result_identity: dict,
           output: Path, mapping_path: Path, *, shuffle=None) -> dict:
    if len(slots) != 12 or len(texts) != 12:
        raise ValueError("Exactly twelve planned slots must be retained")
    if output.exists() or mapping_path.exists() or mapping_path.is_relative_to(output):
        raise ValueError("Use new outputs and a separate mapping outside the blind folder")
    candidates = [(i, text) for i, text in enumerate(texts) if text is not None and text != ""]
    (shuffle or secrets.SystemRandom().shuffle)(candidates)
    rows, mappings, chunks = [], [], ["# Response-only reading pack\n\n"
        "Texts are unchanged, including any incomplete ending. Source and condition "
        "information is withheld until first-pass notes are fixed.\n"]
    byte_count = len(chunks[0].encode("utf-8"))
    for number, (index, text) in enumerate(candidates, 1):
        reading_id = f"R{number:02d}"
        raw = text.encode("utf-8")
        runs = [len(x) for x in re.findall(r"`+", text)]
        fence = "`" * max(3, max(runs, default=0) + 1)
        prefix = f"\n## {reading_id}\n\n{fence}text\n"
        start = byte_count + len(prefix.encode("utf-8"))
        segment = prefix + text + "\n" + fence + "\n"
        chunks.append(segment)
        byte_count += len(segment.encode("utf-8"))
        rows.append({"readingId": reading_id, "text": text})
        mappings.append({"readingId": reading_id, "slotIndex": index,
                         "textBytes": len(raw), "textSha256": sha(raw),
                         "markdownUtf8Start": start, "markdownUtf8End": start + len(raw)})
    markdown = "".join(chunks).encode("utf-8")
    pack = json_bytes({"schema": "reservoir-response-only-pack-v1", "responses": rows})
    by_slot = {x["slotIndex"]: x for x in mappings}
    mapping = {"schema": "reservoir-condition-masked-mapping-v1",
               "preparedAtUtc": datetime.now(timezone.utc).isoformat(),
               "sourceResult": result_identity,
               "order": "secrets.SystemRandom shuffle; IDs assigned after shuffle",
               "sealedBeforeBlindFiles": True,
               "blindFiles": {"RESPONSES.md": {"bytes": len(markdown), "sha256": sha(markdown)},
                              "RESPONSES.json": {"bytes": len(pack), "sha256": sha(pack)}},
               "slots": [{"slotIndex": i, "sourceSlot": slot,
                          "textState": "unavailable" if texts[i] is None else
                                       "empty" if texts[i] == "" else "available",
                          "reading": by_slot.get(i)} for i, slot in enumerate(slots)]}
    # Check every source-text span before sealing the mapping or publishing packs.
    for m in mappings:
        if markdown[m["markdownUtf8Start"]:m["markdownUtf8End"]] != texts[m["slotIndex"]].encode("utf-8"):
            raise ValueError("Exact response span failed")
    sealed = json_bytes(mapping)
    exclusive_write(mapping_path, sealed)
    output.mkdir(mode=0o700)
    exclusive_write(output / "RESPONSES.md", markdown)
    exclusive_write(output / "RESPONSES.json", pack)
    return {"mapping": {"path": str(mapping_path), "sha256": sha(sealed)},
            "blindDirectory": str(output), "blindFiles": mapping["blindFiles"]}


def load_terminal(result_path: Path, expected_sha256: str) -> tuple[list[dict], list[str | None], dict]:
    raw = read_bound(result_path, MAX_RESULT)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or sha(raw) != expected_sha256:
        raise ValueError("Final result SHA-256 mismatch")
    result = json.loads(raw)
    terminal = {"completed", "stopped", "interrupted", "refused_or_failed",
                "failed_identity", "refused_before_network"}
    if result.get("schema") != "reservoir-context-order-run-v1" or result.get("status") not in terminal:
        raise ValueError("Final context-order runner result required")
    ended = datetime.fromisoformat(result["endedAtUtc"].replace("Z", "+00:00"))
    if ended.tzinfo is None:
        raise ValueError("Terminal time must have a timezone")
    slots = result.get("slots")
    order = [(step, c) for i, step in enumerate(range(60, 361, 60)) for c in ("AB" if i % 2 == 0 else "BA")]
    if not isinstance(slots, list) or len(slots) != 12:
        raise ValueError("Exactly twelve planned slots required")
    identities = [{"path": str(result_path), "bytes": len(raw), "sha256": sha(raw)}]

    def read_ref(ref: dict) -> bytes:
        path = Path(ref["path"])
        if not path.is_absolute() or path.parent != result_path.parent or path == result_path:
            raise ValueError("Response evidence must be a named file beside the final ledger")
        data = read_bound(path, MAX_BODY)
        if type(ref["bytes"]) is not int or len(data) != ref["bytes"] or sha(data) != ref["sha256"]:
            raise ValueError("Response evidence identity mismatch")
        identities.append({"path": str(path), "bytes": len(data), "sha256": sha(data)})
        return data

    texts, retained = [], []
    for n, (slot, (step, condition)) in enumerate(zip(slots, order), 1):
        if (slot.get("slot"), slot.get("anchorStep"), slot.get("condition")) != (n, step, condition):
            raise ValueError("Frozen twelve-slot order differs")
        if slot.get("status") in (None, "running", "dispatching"):
            raise ValueError("Unsettled slot in supposedly final result")
        text, state = None, "no_retained_response"
        if "response" in slot:
            if slot["status"] == "unstarted":
                raise ValueError("Unstarted slot cannot contain a response")
            text, state = response_text(read_ref(slot["response"]))
        if "text" in slot:
            retained_text = read_ref(slot["text"])
            if text is None or retained_text != text.encode("utf-8"):
                raise ValueError("Decoded text file does not match unique raw response content")
        retained.append({**slot, "blindExtraction": state})
        texts.append(text)
    # Fail closed if any input changed during preparation; no live-result following.
    for ref in identities:
        data = read_bound(Path(ref["path"]), MAX_RESULT)
        if len(data) != ref["bytes"] or sha(data) != ref["sha256"]:
            raise ValueError("Input changed during preparation")
    return retained, texts, {"ledger": identities[0], "boundFiles": identities[1:],
                             "terminalStatus": result["status"], "endedAtUtc": result["endedAtUtc"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--expected-result-sha256", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--mapping-output", type=Path, required=True)
    args = parser.parse_args()
    slots, texts, identity = load_terminal(args.result.absolute(), args.expected_result_sha256)
    summary = render(slots, texts, identity, args.output_directory.absolute(), args.mapping_output.absolute())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
