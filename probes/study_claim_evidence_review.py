"""Read-only integrity and outcome accounting for claim/evidence adjacency.

Uses the qualified token/cache validator; never loads the model or tokenizes text.
Grounding judgments remain independently authored, hash-linked annotations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


plan = sibling("study_claim_evidence")
qualified = sibling("study_source_first_review")
sha, read_json, digest = qualified.sha, qualified.read_json, plan.digest
FIELDS = qualified.FIELDS


def validate_inputs(root, protocol):
    if protocol.get("schema") != "study_claim_evidence_v1" or protocol["trials"] != plan.trial_specs():
        raise ValueError("claim/evidence plan differs")
    path = Path(protocol["previous"]["path"])
    if protocol["previous"]["sha256"] != plan.PREVIOUS_SHA or digest(path) != plan.PREVIOUS_SHA:
        raise ValueError("predecessor identity differs")
    prior = read_json(path)
    for key in ("model", "runtime", "settings", "guards", "system", "question", "account_wrapper", "accounts", "original_provenance"):
        if protocol[key] != prior[key]:
            raise ValueError(f"inherited field differs: {key}")
    if protocol["intro"] != plan.INTRO or protocol["layouts"] != {k: list(v) for k, v in plan.LAYOUTS.items()}:
        raise ValueError("common invitation or layout differs")
    if set(protocol["adapter_sources"]) != {str(Path(__file__).with_name(name).resolve()) for name in plan.DEPENDENCIES}:
        raise ValueError("adapter inventory differs")
    plan.verify_adapter(protocol)
    blocks = {}
    required = {"evidence", "rubric", "selections"} | {"source-" + Path(p).stem for p in protocol["adapter_sources"]}
    if set(protocol["blocks"]) != required or {p.stem[6:] for p in root.glob("block-*.txt")} != required:
        raise ValueError("frozen block inventory differs")
    for name, receipt in protocol["blocks"].items():
        raw = (root / f"block-{name}.txt").read_bytes()
        if receipt != {"sha256": sha(raw), "bytes": len(raw)}:
            raise ValueError("frozen block hash differs")
        blocks[name] = raw.decode()
    for source, expected in protocol["adapter_sources"].items():
        if sha(blocks["source-" + Path(source).stem].encode()) != expected:
            raise ValueError("frozen adapter copy differs")
    evidence = blocks["evidence"]
    if evidence != (path.parent / "block-evidence.txt").read_text() or sha(evidence.encode()) != prior["blocks"]["evidence"]["sha256"]:
        raise ValueError("historical evidence bytes differ")
    if protocol["evidence_parts"] != plan.split_evidence(evidence) or protocol["selections"] != json.loads(blocks["selections"]):
        raise ValueError("source partition or selected claims differ")
    plan.validate_selections(protocol["accounts"], protocol["selections"])
    if (root / "system.txt").read_text() != protocol["system"] or read_json(root / "criteria.json") != protocol["criteria"]:
        raise ValueError("system or criteria receipt differs")
    if set(protocol["source_map"]) != set(prior["source_map"]) or {p.name for p in (root / "source-snapshot").iterdir()} != set(prior["source_map"]):
        raise ValueError("source snapshot inventory differs")
    for name, row in protocol["source_map"].items():
        target = root / "source-snapshot" / name
        if row != {**prior["source_map"][name], "copy": str(target)} or digest(target) != row["sha256"] or digest(path.parent / "source-snapshot" / name) != row["sha256"]:
            raise ValueError("historical source identity differs")
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if manifest["protocol_sha256"] != digest(root / "protocol.json"):
            raise ValueError("manifest protocol identity differs")
        expected = {str(p) for p in (root / "protocol.json", root / "criteria.json", root / "system.txt", *sorted(root.glob("block-*.txt")))}
        if set(manifest["frozen_files"]) != expected or set(manifest["source_snapshots"]) != {str(p) for p in (root / "source-snapshot").iterdir()}:
            raise ValueError("manifest artifact inventory differs")
        required_sources = {str(Path(__file__).with_name(n).resolve()) for n in
                            ("study_source_first_runtime.py", "study_source_first.py", "study_source_first_review.py", "study_evidence_order.py")}
        required_sources |= {str(Path(protocol["runtime"]) / n) for n in ("generation_controls.py", "coupled_astrid_server.py", "real_model_coupling_study.py")}
        libraries = ("mlx_lm/generate.py", "mlx_lm/sample_utils.py", "mlx_lm/models/gemma4_text.py", "mlx_lm/models/cache.py")
        remaining = set(manifest["sources"]) - required_sources
        if not required_sources <= set(manifest["sources"]) or len(remaining) != len(libraries) or any(sum(p.endswith("/" + n) for p in remaining) != 1 for n in libraries):
            raise ValueError("runtime source inventory differs")
        for section in ("sources", "frozen_files", "source_snapshots"):
            qualified.verify_hashes(manifest[section], "manifest " + section)
        model = Path(protocol["model"])
        names = set(read_json(model / "model.safetensors.index.json")["weight_map"].values()) | {"config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja", "model.safetensors.index.json"}
        if set(manifest["assets"]) != names or set(manifest["versions"]) != {"mlx", "mlx-lm", "numpy", "transformers", "tokenizers"}:
            raise ValueError("model/dependency inventory differs")
        qualified.verify_hashes({str(model / name): value for name, value in manifest["assets"].items()}, "model asset")
    return {"protocol_sha256": digest(root / "protocol.json"), "predecessor_sha256": plan.PREVIOUS_SHA,
            "source_snapshots": len(protocol["source_map"]), "exact_factor_reconstruction": True,
            "manifest_available": manifest_path.exists(), "model_asset_hashes_checked": manifest_path.exists()}


def summarize(cells):
    return {"planned": len(cells), "outcomes": dict(Counter(c["outcome"] for c in cells)),
            "nonempty": sum(c["nonempty"] for c in cells), "eligible": sum(c["eligible"] for c in cells),
            "annotated": sum(c["annotation"] is not None for c in cells)}


def validate_source_quotes(value, evidence):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_quote":
                if not isinstance(item, str) or not item or item not in evidence:
                    raise ValueError("source quote absent from evidence")
            else:
                validate_source_quotes(item, evidence)
    elif isinstance(value, list):
        for item in value:
            validate_source_quotes(item, evidence)


def review(root):
    root = Path(root).resolve(); protocol = read_json(root / "protocol.json")
    integrity = validate_inputs(root, protocol)
    specs = protocol["trials"]; ids = {s["id"] for s in specs}
    for prefix in ("", "input-", "rendered-"):
        if any(p.stem.removeprefix(prefix) not in ids for p in root.glob(prefix + "claim-evidence-*.json")):
            raise ValueError("unplanned trial artifact")
    annotations = qualified.load_annotations(root, specs)
    cells, caches, renderings = [], {}, {}
    for spec in specs:
        ident = spec["id"]; messages = plan.build_messages(protocol, spec)
        if read_json(root / f"input-{ident}.json") != {"spec": spec, "messages": messages, "dependency": None}:
            raise ValueError("exact fixed input differs")
        rendering = qualified.validate_render(root, spec, messages)
        renderings[ident] = None if rendering is None else {k: rendering[k] for k in ("token_count", "rendered_sha256")}
        path = root / f"{ident}.json"; row = read_json(path) if path.exists() else None
        if row is not None and (not isinstance(row, dict) or row.get("spec") != spec or row.get("outcome") not in qualified.OUTCOMES - {"dependency_unavailable"}):
            raise ValueError("outcome differs from plan")
        result = row.get("result") if row else None
        if row and row["outcome"] in ("returned", "generation_error") and result is None:
            raise ValueError("generated outcome lacks result")
        if result is not None:
            if rendering is None:
                raise ValueError("generation lacks rendered input")
            caches[ident] = qualified.validate_result(row, rendering, protocol["settings"], qualified.native_eos_ids(protocol))
        annotation = annotations.get(ident)
        if annotation:
            if not result or not result["text"].strip() or annotation.get("response_sha256") != result["response_sha256"]:
                raise ValueError("annotation lacks nonempty matching response")
            qualified.validate_annotation_quotes(annotation, result["text"])
            validate_source_quotes(annotation, (root / "block-evidence.txt").read_text())
            for quote in annotation.get("evidence_quotes", []):
                if not quote.get("source_quote") or quote["source_quote"] not in (root / "block-evidence.txt").read_text():
                    raise ValueError("source quote absent from evidence")
        cell = {**spec, "outcome": row["outcome"] if row else "missing", "nonempty": bool(result and result["text"].strip()),
                "eligible": bool(row and plan.previous.eligible_first(row)), "annotation": annotation,
                "assessment": {k: (annotation or {}).get(k) or "unassessed" for k in FIELDS}}
        if result:
            cell.update({k: result[k] for k in ("finish", "termination", "prompt_tokens", "completion_tokens", "seconds", "admission_seconds", "response_sha256")})
            cell["authored"] = qualified.old.previous_review.authored_fields(result["text"])
        cells.append(cell)
    complete = root / "completed.json"
    if complete.exists():
        receipt = read_json(complete)
        if (any(c["outcome"] == "missing" for c in cells) or receipt.get("cells") != len(specs)
                or receipt.get("live_writes") is not False or receipt.get("sources_unchanged") is not True
                or receipt.get("model_assets_unchanged") is not True or not integrity["manifest_available"]):
            raise ValueError("completion receipt contradicts evidence")
    pairs = []
    for seed in plan.SEEDS:
        for account in ("retained", "supported"):
            group = [c for c in cells if c["seed"] == seed and c["arm"].startswith(account + "_")]
            pairs.append({"seed": seed, "account": account, **summarize(group), "ids": [c["id"] for c in group],
                          "complete_eligible": all(c["eligible"] for c in group)})
    return {"schema": "study_claim_evidence_review_v1", **summarize(cells), "cells": cells,
            "pairs": pairs, "complete_eligible_pairs": sum(p["complete_eligible"] for p in pairs),
            "seed_blocks": [{"seed": seed, **summarize([c for c in cells if c["seed"] == seed])} for seed in plan.SEEDS],
            "integrity": integrity, "renderings": renderings, "cache_progression": caches, "completed": complete.exists(),
            "limits": protocol["criteria"]["limits"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("root", type=Path)
    args = parser.parse_args(); print(json.dumps(review(args.root), indent=2, ensure_ascii=False))
