#!/usr/bin/env python3
"""Stage a private, offline S-021 walkthrough from the closed archive (stdlib only).

Read-only with respect to the archive. No provider calls. The small derived packet
is ignored by Git; bundling it is a separate local packaging decision.
"""
import argparse
import hashlib
import json
from pathlib import Path

CLOSED_SHA = "98bba29466b707ac2cfea71063f15b74df6b07d4b0bc42cd1a3d47085411fc3a"
SCORE_SHA = "ce1550f8651c8bcf8c8bcdcc3f4e642954e3c6e3ebfc2653915a1f5cba064eb0"
DESIGN_SHA = "a2adfbf7af230695b8e55e569017cfd25554958db3852de7763f40027adf5b6d"


def checked_json(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Source hash differs: {path}")
    return json.loads(raw)


def stage(archive: Path, destination: Path):
    archive, destination = archive.resolve(), destination.resolve()
    if destination.is_relative_to(archive):
        raise ValueError("Output must be outside the closed archive")
    checked_json(archive / "CLOSED.json", CLOSED_SHA)
    design = checked_json(archive / "designs/study-v2.json", DESIGN_SHA)
    scores = checked_json(archive / "scores/study-v1.json", SCORE_SHA)
    evidence = scores["run"]["evidence_files"]
    rows, prompts = [], {}
    for row in scores["rows"]:
        node = row["node_id"]
        folder = f"nodes/{node}"
        files = {
            name: checked_json(archive / "runs/study-v1" / folder / name,
                               evidence[f"{folder}/{name}"])
            for name in ("request.json", "result.json", "response.raw")
        }
        request, result, raw = (files[k] for k in ("request.json", "result.json", "response.raw"))
        if result["status"] != "complete" or not raw["done"]:
            raise ValueError(f"Incomplete source: {node}")
        prefix, suffix = request["messages"][-1]["content"], raw["message"]["content"]
        if prefix != row["supplied_prefix"] or suffix != row["raw_suffix"] or suffix != result["text"]:
            raise ValueError(f"Source text differs: {node}")
        prompt_key = f'{row["base_index"]}-{row["rule"]}'
        messages = request["messages"][:-1]
        if prompt_key in prompts and prompts[prompt_key] != messages:
            raise ValueError(f"Shared task differs: {node}")
        prompts[prompt_key] = messages
        rows.append({"id": node, "base": row["base_index"], "rule": row["rule"],
                     "condition": row["condition"], "seed": row["seed"],
                     "status": result["status"], "prefix": prefix, "suffix": suffix,
                     "requestSha256": evidence[f"{folder}/request.json"],
                     "responseSha256": evidence[f"{folder}/response.raw"]})
    if len(rows) != 72:
        raise ValueError("Expected exactly 72 saved routing calls")
    packet = {"schemaVersion": 1, "study": "S-021", "source": {
        "closedSha256": CLOSED_SHA, "scoreSha256": SCORE_SHA, "designSha256": DESIGN_SHA,
        "model": design["model"], "modelDigest": design["model_digest"],
        "providerVersion": design["provider_version"], "temperature": design["options"]["temperature"],
        "contextTokens": design["options"]["num_ctx"]},
        "worlds": [{"base": c["base_index"], "subject": c["focal"], "x": c["x"],
                    "oldThreshold": c["threshold"], "changedThreshold": c["later_threshold"]}
                   for c in design["cases"]], "prompts": prompts, "rows": rows}
    payload = (json.dumps(packet, ensure_ascii=False, indent=2) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return {"rows": len(rows), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
            "destination": str(destination), "source_archive_unchanged": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] /
                        "desktop/ReservoirScope/src/local-studies/s021.json")
    args = parser.parse_args()
    print(json.dumps(stage(args.archive, args.output), indent=2))
