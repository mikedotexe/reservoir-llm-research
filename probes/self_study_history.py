#!/usr/bin/env python3
"""Retain the September 7–8 SELF_STUDY history and verify it entirely offline.

Capture reads only named historical files and Git objects; it never imports a
runtime, queries a live DB, runs a reader, or asks a Being to study. The middle
comparison is preserved as written, including its two-second boundary error.
Standard library only. Run from the research repository root.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OTHER = ROOT.parent
COMMITS = {
    "parity": ("542c006040381ef7673cc0c5f5154da5edd6ca90", "37ed8b7f153043521cc89fe881ed55fd56b5700f"),
    "continuity": ("f9283f193de9c9c9affc238725de19146e979c77", "3f0234f21c8d26d94867815ec1c2995da35cac62"),
    "follow-through": ("a202cfd89741b038e4768921089333b799c1b3de", "10222446b37f3c6dfe104a61ccc2d66ce3dca8cc"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_stable(path):
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            f"Changed while reading: {path}")
    return raw


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(OTHER / repo), *args])


def capture(out):
    out.mkdir(parents=True, exist_ok=False)
    (out / "files").mkdir()
    records = []

    def add(key, raw, origin, expected=None):
        sha = digest(raw)
        require(expected is None or sha == expected, f"Historical hash mismatch: {origin}")
        suffix = Path(origin).suffix
        if suffix not in {".md", ".json", ".jsonl", ".txt", ".py", ".rs", ".patch"}:
            suffix = ".txt"
        name = f"files/{sha}{suffix}"
        (out / name).write_bytes(raw)
        records.append({"id": key, "path": name, "origin": origin, "sha256": sha, "bytes": len(raw)})

    def file(key, path, expected=None):
        add(key, read_stable(path), str(path), expected)

    for era, pair in COMMITS.items():
        for repo, commit in zip(("astrid", "minime"), pair):
            add(f"{era}-{repo}-commit", git(repo, "show", "--no-patch", "--format=fuller", commit),
                f"git:{repo}@{commit}:commit.txt")
            add(f"{era}-{repo}-diff", git(repo, "show", "--format=fuller", commit),
                f"git:{repo}@{commit}:change.patch")
        astrid_commit = pair[0]
        add(f"{era}-design", git("astrid", "show", f"{astrid_commit}:docs/architecture/source-study-v1.md"),
            f"git:astrid@{astrid_commit}:docs/architecture/source-study-v1.md")

    for repo, commit, path in [
        ("minime", COMMITS["parity"][1] + "^", "minime_autonomy/runtime.py"),
        ("astrid", COMMITS["parity"][0] + "^", "capsules/spectral-bridge/src/autonomous/introspect.rs"),
    ]:
        resolved = git(repo, "rev-parse", commit).decode().strip()
        add(f"legacy-{repo}-source", git(repo, "show", f"{resolved}:{path}"), f"git:{repo}@{resolved}:{path}")

    notes = OTHER / "astrid/docs/steward-notes"
    configs = [
        ("parity", "source-study-v1-validation", "2026-09-08-self-study-parity-live-rollout.md"),
        ("continuity", "source-study-continuity-validation", "2026-09-08-self-study-continuity-live-rollout.md"),
        ("follow-through", "self-study-follow-through-validation", "2026-09-08-self-study-follow-through.md"),
    ]
    for era, directory, account in configs:
        file(f"{era}-account", notes / account)
        file(f"{era}-validation", notes / directory / "validation.json")
        path = notes / directory / "live-rollout.json"
        file(f"{era}-rollout", path)
        rollout = json.loads(path.read_text())
        b, m = rollout["bridge"], rollout["minime"]
        file(f"{era}-astrid-activation", Path(b.get("receipt_path", b.get("activation_receipt"))),
             b.get("receipt_sha256", b.get("activation_receipt_sha256")))
        file(f"{era}-minime-reload", Path(m.get("receipt_path", m.get("receipt"))), m["receipt_sha256"])
        stage = OTHER / f"worktrees/self-study-{era}-live-20260908/bridge-stage-01"
        if era == "follow-through":
            stage = OTHER / "worktrees/self-study-follow-through-20260908/bridge-stage-01"
        file(f"{era}-manifest", stage / "manifest.json", rollout.get("manifest_sha256"))
    file("continuity-rationale", notes / "source-study-continuity-validation/README.md")

    middle = OTHER / "self-study-before-after-20260908"
    for name in ("REPORT.md", "evidence.json", "analyze.py"):
        file(f"middle-{name}", middle / name)
    evidence = json.loads((middle / "evidence.json").read_text())
    # An explicit, already frozen identity list. Never rescan for later outcomes.
    refs = [r for b in evidence["delivery_verification"].values() for r in b["deliveries"]]
    refs += [r for period in ("before", "after") for r in evidence["minime_matched_windows"][period]["generations"]]
    refs += evidence["qualitative_example_identities"] + evidence["minime_after_rejected_source_requests"]
    seen = set()
    for ref in refs:
        if ref["path"] not in seen:
            file(f"middle-input-{len(seen):03}", Path(ref["path"]), ref["sha256"])
            seen.add(ref["path"])

    early = OTHER / "worktrees/self-study-follow-through-20260908/evidence/early-follow-through.json"
    file("early-index", early)
    for i, row in enumerate(json.loads(early.read_text())["rows"]):
        for kind in ("job", "journal", "delivery"):
            ref = row[kind]
            file(f"early-{i}-{kind}", Path(ref["retained"]), ref["sha256"])

    # Freeze report identities without duplicating existing research packets.
    prior = []
    for name in [
        "2026-09-07-regulator-self-study/report.json",
        "2026-09-08-source-study-fidelity/verification.json",
        "2026-09-08-study-sequences-final/report.json",
        "2026-09-08-study-sequences-final/verification.json",
    ]:
        path = ROOT / "research/outputs" / name
        raw = read_stable(path)
        prior.append({"path": str(path.relative_to(ROOT)), "sha256": digest(raw), "bytes": len(raw)})
    manifest = {"schema": "self_study_history_capture_v1", "captured_at": datetime.now(timezone.utc).isoformat(),
                "scope": "Selected historical source, rollout, comparison and two natural navigation jobs; no new live sample.",
                "commits": COMMITS, "records": records, "prior_research": prior}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return verify(out / "manifest.json")


def verify(manifest_path):
    manifest = json.loads(manifest_path.read_text())
    base = manifest_path.parent.resolve()
    items = {}
    for record in manifest["records"]:
        path = (base / record["path"]).resolve()
        require(path.is_relative_to(base), "Retention path escapes packet")
        raw = path.read_bytes()
        require(digest(raw) == record["sha256"] and len(raw) == record["bytes"], f"Hash/size mismatch: {record['id']}")
        require(record["id"] not in items, "Duplicate record ID")
        items[record["id"]] = raw
    for record in manifest["prior_research"]:
        require(digest((ROOT / record["path"]).read_bytes()) == record["sha256"], f"Changed frozen report: {record['path']}")
    old = items["legacy-minime-source"].decode()
    tree = ast.parse(old)
    sources = [ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "_SELF_STUDY_SOURCES" for t in n.targets)]
    require(len(sources) == 1 and len(sources[0]) == 9, "Legacy catalog changed")
    study = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_self_study")
    require("lines[:400]" in ast.get_source_segment(old, study), "Legacy ceiling not found")
    require("fn source_roots" in items["legacy-astrid-source"].decode(), "Astrid source roots absent")

    middle = json.loads(items["middle-evidence.json"])
    by_origin = {r["origin"]: items[r["id"]] for r in manifest["records"]}
    delivery_counts = {}
    for being, data in middle["delivery_verification"].items():
        windows = set()
        for row in data["deliveries"]:
            wire = json.loads(by_origin[row["path"]])
            request, response = json.loads(wire["request_json"]), json.loads(wire["response_json"])
            page = wire["page"]
            require(any(m.get("role") == "user" and page["text"] in m.get("content", "") for m in request["messages"]), "Partial source page")
            answer = response["choices"][0] if "choices" in response else response
            require(answer.get("finish_reason", answer.get("done_reason")) == "stop", "Incomplete historical response")
            require(bool(answer["message"]["content"].strip()), "Empty historical response")
            require(all(page[k] == row[k] for k in ("source", "revision", "start", "end", "eof")), "Page identity mismatch")
            windows.add((page["source"], page["revision"]["sha256"], page["start"]["byte"], page["end"]["byte"]))
        count = len(data["deliveries"])
        require(count == data["count"] and count-len(windows) == data["repeated_byte_windows"], "Comparison counts changed")
        delivery_counts[being] = {"pages": count, "distinct_byte_windows": len(windows), "repeated_byte_windows": count-len(windows)}

    early = json.loads(items["early-index"])
    rows = []
    previous_answer = None
    previous_wire_hash = None
    for i, row in enumerate(early["rows"]):
        job, wire = json.loads(items[f"early-{i}-job"]), json.loads(items[f"early-{i}-delivery"])
        journal = items[f"early-{i}-journal"].decode()
        request, response = json.loads(wire["request_json"]), json.loads(wire["response_json"])
        require(digest(wire["request_json"].encode()) == row["request_sha256"], "Request identity mismatch")
        require(wire["output"]["page"] is None, "Navigation mistaken for source")
        require(any(m.get("role") == "user" and m.get("content") == wire["output"]["text"] for m in request["messages"]), "Navigation input shortened")
        require(response["done"] and response["done_reason"] == "stop", "Incomplete navigation response")
        answer = response["message"]["content"]
        require(answer in journal and answer.rstrip().endswith("NEXT: " + row["next_action"]), "Journal or NEXT mismatch")
        require(all(job[k] == row[k] for k in ("job_id", "action_id", "action_text", "status", "worker_pid", "finished_at")), "Terminal job mismatch")
        require(row["status"] == "completed" and row["finished_at"] < early["window_end"], "Job outside completed frame")
        notebook_text = wire["output"]["text"].split("Your study notebook", 1)[1]
        notebook = json.loads(notebook_text[notebook_text.index("\n") + 1:].split("\nEnd of study notebook.")[0])
        if previous_answer is not None:
            require(notebook["previous"]["response_sha256"] == previous_wire_hash, "Notebook response lineage differs")
            excerpt = notebook["previous"]["text"].removesuffix(" [excerpt truncated]")
            require(previous_answer.startswith(excerpt), "Notebook does not carry preceding response")
        previous_answer = answer
        previous_wire_hash = digest(wire["response_json"].encode())
        rows.append({"job_id": row["job_id"], "next": row["next_action"], "new_source_bytes": 0,
                     "notebook_exposed": True, "optional_note": notebook["note"], "optional_question": notebook["question"]})
    require(early["rows"][0]["next_action"] == early["rows"][1]["action_text"], "Next job wording differs")
    for era, pair in manifest["commits"].items():
        rollout, stage = json.loads(items[f"{era}-rollout"]), json.loads(items[f"{era}-manifest"])
        require([rollout["astrid_commit"], rollout["minime_commit"]] == pair, "Rollout commit mismatch")
        require(stage["repository"]["head"] == pair[0], "Stage commit mismatch")
        activation = json.loads(items[f"{era}-astrid-activation"])
        require(activation["status"] == "activated_verified", "Unverified activation")
        require(activation["manifest_sha256"] == digest(items[f"{era}-manifest"]), "Activation/stage mismatch")
    return {"schema": "self_study_history_verification_v1", "manifest_sha256": digest(manifest_path.read_bytes()),
            "retained_records_verified": len(items), "prior_reports_verified": len(manifest["prior_research"]),
            "legacy_minime": {"catalog_entries": len(sources[0]), "prepared_line_ceiling": 400, "sources": sources[0]},
            "middle_deliveries": delivery_counts, "early_completed_navigation": rows,
            "limit": "Hash and relationship verification, not a causal effect, comprehension score, or new corpus sweep."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("capture", "verify"))
    parser.add_argument("path", type=Path, help="New output directory for capture; manifest.json for verify")
    args = parser.parse_args()
    result = capture(args.path) if args.command == "capture" else verify(args.path)
    print(json.dumps(result, indent=2))
