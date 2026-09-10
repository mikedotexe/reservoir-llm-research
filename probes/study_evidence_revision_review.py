"""Summarize every frozen revision cell, preserving missingness and exact quotes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import statistics


def authored_fields(text):
    unfenced = re.sub(r"```.*?```", "", text, flags=re.S)
    result = {}
    for label in ("NEXT", "STUDY_NOTE", "STUDY_QUESTION"):
        matches = re.findall(rf"^{label}:\s*(.+)$", unfenced, flags=re.M)
        result[label] = matches[-1] if matches else None
    return result


def review(root):
    protocol = json.loads((root / "protocol.json").read_text())
    annotation_path = root / "annotations.json"
    annotations = json.loads(annotation_path.read_text()) if annotation_path.exists() else []
    indexed = {row["id"]: row for row in annotations}
    if len(indexed) != len(annotations):
        raise ValueError("duplicate annotations")
    specs = protocol["trials"]
    if set(indexed) - {row["id"] for row in specs}:
        raise ValueError("unplanned annotated cell")
    cells = []
    for spec in specs:
        path = root / f"{spec['id']}.json"
        if not path.exists():
            cells.append({**spec, "outcome": "missing", "nonempty": False})
            continue
        row = json.loads(path.read_text())
        if row["spec"] != spec:
            raise ValueError("result spec differs from frozen cell")
        result = row.get("result")
        cell = {**spec, "outcome": row["outcome"], "nonempty": bool(result and result["text"].strip())}
        if result:
            text = result["text"]
            if result["completion_tokens"] != len(result["tokens"]):
                raise ValueError("completion count differs from yielded tokens")
            if result["completion_tokens"] > protocol["settings"]["max_tokens"]:
                raise ValueError("completion exceeds frozen allowance")
            if any(result["initial_cache_positions"]):
                raise ValueError("trial cache was not fresh")
            actual = hashlib.sha256(text.encode()).hexdigest()
            if result["response_sha256"] != actual:
                raise ValueError("response digest differs")
            cell.update({key: result[key] for key in ("finish", "termination", "prompt_tokens", "completion_tokens", "seconds", "admission_seconds", "response_sha256")})
            cell["authored"] = authored_fields(text)
            if spec["id"] in indexed:
                annotation = indexed[spec["id"]]
                if annotation["response_sha256"] != actual:
                    raise ValueError("annotation response digest differs")
                for claim in annotation.get("claims", []):
                    if claim["quote"] not in text:
                        raise ValueError(f"annotation quote absent: {spec['id']}")
        if spec["id"] in indexed:
            cell["annotation"] = indexed[spec["id"]]
        cells.append(cell)
    arms = {}
    for arm in protocol["cases"]:
        rows = [row for row in cells if row["arm"] == arm]
        returned = [row for row in rows if "completion_tokens" in row]
        arms[arm] = dict(planned=len(rows), outcomes=dict(Counter(row["outcome"] for row in rows)), nonempty=sum(row["nonempty"] for row in rows),
                         tokens=[row["completion_tokens"] for row in returned],
                         seconds=[row["seconds"] for row in returned],
                         median_seconds=statistics.median(row["seconds"] for row in returned) if returned else None)
    prose = [row for row in cells if "authored" in row]
    return dict(schema="study_evidence_revision_review_v1", planned=len(specs), annotated=len(indexed),
                outcomes=dict(Counter(row["outcome"] for row in cells)), nonempty=sum(row["nonempty"] for row in cells),
                termination_kinds=dict(Counter((row["termination"] or {}).get("kind", "unknown") for row in prose)),
                authored_field_counts={label:sum(row["authored"][label] is not None for row in prose) for label in ("NEXT", "STUDY_NOTE", "STUDY_QUESTION")},
                matched_nonempty_seeds=[seed for seed in sorted({row["seed"] for row in specs}) if all(row["nonempty"] for row in cells if row["seed"] == seed)],
                arms=arms, cells=cells, limits="Two seeds, one retained episode, unblinded coding; no live NEXT execution or checkpoint write. Prose length is descriptive.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.root), indent=2, ensure_ascii=False))
