"""Fixed, outcome-independent reading samples with separately blinded evidence.

This module never contacts a provider. Allocation and run identity belong only
to the private key and receipt; reader documents use opaque packet numbers.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import random
import re

from . import runner

SHUFFLE_SEED = 20261024
PRESELECTED_CASE_INDICES = frozenset((0, 1, 2, 3, 12, 13, 14, 15))
MEMORY_ARMS = ("original", "paraphrase", "notebook", "irrelevant", "none")
SELECTION_VERSION = 1


def _slot(node: dict) -> dict:
    return {"node_id": node["id"], "episode": node["episode"],
            "condition": node["condition"], "kind": node["kind"], "seed": node["seed"],
            "source_unavailable": False}


def _selected_opportunities(protocol: dict) -> list[dict]:
    """Selection reads allocation only, never text, correctness, or availability."""
    study = protocol["study"]
    nodes = protocol["nodes"]
    if study in ("S-013", "S-016"):
        kind = "prose" if study == "S-013" else "catalog"
        selected = []
        for node in nodes:
            if node["kind"] != kind or node["seed"] != 7 or node.get("metadata", {}).get("replicate"):
                continue
            index = node.get("metadata", {}).get("case_index")
            if type(index) is not int:
                raise runner.ExperimentError("Reading selection requires an integer frozen case_index")
            if index in PRESELECTED_CASE_INDICES:
                selected.append(_slot(node))
    elif study in ("S-014", "S-015"):
        cases = protocol.get("cases")
        if not isinstance(cases, list):
            raise runner.ExperimentError("Reading selection requires frozen cases")
        case_ids = [case["id"] for case in cases if type(case.get("variant")) is int and case["variant"] == 0]
        if len(set(case_ids)) != len(case_ids):
            raise runner.ExperimentError("Reading selection has duplicate case IDs")
        unavailable = {row["episode"] for row in protocol.get("unavailable_sources", [])}
        eligible = {}
        for node in nodes:
            if node["seed"] != 7 or node["episode"] not in case_ids:
                continue
            if study == "S-014":
                if node["kind"] != "target":
                    continue
                key = (node["episode"], "target")
            else:
                if node["kind"] != "application" or node.get("metadata", {}).get("delay") != "delayed":
                    continue
                key = (node["episode"], node["condition"])
                if key[1] not in MEMORY_ARMS:
                    raise runner.ExperimentError("Unexpected memory arm in fixed reading selection")
            if key in eligible:
                raise runner.ExperimentError("Duplicate reading opportunity")
            eligible[key] = node
        selected = []
        for episode in case_ids:
            for condition in (("target",) if study == "S-014" else MEMORY_ARMS):
                node = eligible.get((episode, condition))
                selected.append(_slot(node) if node else {
                    "node_id": None, "episode": episode, "condition": condition,
                    "kind": "target" if study == "S-014" else "application", "seed": 7,
                    "source_unavailable": episode in unavailable})
    else:
        raise runner.ExperimentError(f"No fixed reading selection for {study}")
    selected.sort(key=lambda slot: (slot["episode"], slot["condition"], slot["node_id"] or ""))
    random.Random(SHUFFLE_SEED).shuffle(selected)
    return selected


def _literal_block(text: str) -> str:
    # A model may emit Markdown headings or fences. Preserve its text inside a
    # longer fence so it cannot masquerade as another packet or another role.
    longest = max((len(match.group()) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return fence + "text\n" + text + ("" if text.endswith("\n") else "\n") + fence + "\n"


def study_reading(run: Path, out: Path) -> dict:
    """Export the predeclared study sample, retaining unavailable opaque slots.

    ``reading.md`` contains generated outputs only. ``evidence.md`` contains the
    exact saved request messages for the same packet numbers, without evaluator
    truth or allocation labels. Prompts and outputs can themselves reveal an arm;
    this is recorded as a blinding limitation rather than edited away.
    """
    run = Path(run).resolve()
    with runner.exclusive_lock(run / ".run.lock"):
        verification = runner.verify(run)
        manifest, protocol = runner.load_run(run)
        destination = runner.guard_output(Path(out), Path(manifest["repository"]))
        if destination.exists():
            raise runner.ExperimentError("Reading export refuses an existing destination")
        records = runner.read_results(run)
        state = runner.status(run, verify_first=False)["nodes"]
        selected = _selected_opportunities(protocol)
        output_doc = ["# Output reading packet\n\nRead these outputs before opening the separate evidence packet. "
                      "Each packet is one preselected opportunity; missing and incomplete outputs retain their slots. "
                      "Allocation labels are withheld. Text itself may reveal its conditions.\n"]
        evidence_doc = ["# Evidence reading packet\n\nUse these messages only after recording output-only notes. "
                        "Packet numbers match the output document. Messages are copied exactly from saved requests; "
                        "evaluator truth and allocation labels are withheld. Prompt content may reveal its conditions.\n"]
        key = []
        for number, slot in enumerate(selected, 1):
            nid = slot["node_id"]
            record = records.get(nid, {})
            status = (state[nid] if nid is not None else
                      "source_unavailable" if slot["source_unavailable"] else "not_scheduled")
            text = record.get("text")
            if text is not None and not isinstance(text, str):
                raise runner.ExperimentError("Reading output text must be a string or null")
            heading = f"\n## Packet {number:03d}\n\nStatus: {status}.\n\n"
            output_doc.append(heading)
            evidence_doc.append(heading)
            if text is None:
                output_doc.append("No generated text is retained for this opportunity.\n")
            elif text == "":
                output_doc.append("The retained generated text is empty.\n")
            else:
                if status != "complete":
                    output_doc.append("This retained output is incomplete or otherwise unavailable for the primary score.\n\n")
                output_doc.append(_literal_block(text))
            item = {"packet_number": number, **slot, "status": status,
                    "retained_text": text is not None, "request_sha256": None, "result_sha256": None}
            directory = run / "nodes" / nid if nid is not None else None
            request_path = directory / "request.json" if directory is not None else None
            if request_path is not None and request_path.exists():
                raw = runner.stable_read(request_path)
                messages = json.loads(raw)["messages"]
                for ordinal, message in enumerate(messages, 1):
                    evidence_doc.append(f"### Message {ordinal} — {message['role']}\n\n")
                    evidence_doc.append(_literal_block(message["content"]))
                    evidence_doc.append("\n")
                item["request_sha256"] = runner.sha(raw)
                item["message_count"] = len(messages)
            else:
                evidence_doc.append("No rendered request was retained for this opportunity.\n")
                item["message_count"] = 0
            if directory is not None and (directory / "result.json").exists():
                item["result_sha256"] = runner.sha(runner.stable_read(directory / "result.json"))
            key.append(item)
        counts = dict(Counter(item["status"] for item in key))
        missing = [{"packet_number": item["packet_number"], "status": item["status"]}
                   for item in key if item["status"] != "complete"]
        destination.mkdir(parents=True, mode=0o700)
        runner.write_once(destination / "reading.md", "".join(output_doc).encode("utf-8"))
        runner.write_once(destination / "evidence.md", "".join(evidence_doc).encode("utf-8"))
        runner.write_json(destination / "allocation-key.json", key)
        receipt = {
            "schema_version": 1, "selection_version": SELECTION_VERSION, "shuffle_seed": SHUFFLE_SEED,
            "created_at": runner.now(), "study": protocol["study"], "split": protocol["split"],
            "model": protocol["model"], "protocol_id": protocol["id"], "run": str(run),
            "git_head": manifest["git_head"], "verified": verification["valid"],
            "manifest_sha256": runner.sha(runner.stable_read(run / "manifest.json")),
            "protocol_sha256": runner.sha(runner.stable_read(run / "protocol.json")),
            "identity_sha256": runner.sha(runner.stable_read(run / "identity.json")) if (run / "identity.json").exists() else None,
            "exporter_sha256": runner.sha(runner.stable_read(Path(__file__))),
            "planned": len(key), "selected": len(key), "complete": counts.get("complete", 0),
            "incomplete": counts.get("incomplete", 0), "source_unavailable": counts.get("source_unavailable", 0),
            "retained_text": sum(item["retained_text"] for item in key), "status_counts": counts,
            "missing_selected_opportunities": missing,
            "files": {name: runner.sha(runner.stable_read(destination / name))
                      for name in ("reading.md", "evidence.md", "allocation-key.json")},
            "blinding_limit": "Unedited prompt and output content may reveal an allocation; packet labels do not.",
        }
        runner.write_json(destination / "receipt.json", receipt)
        return receipt
