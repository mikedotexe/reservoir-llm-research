"""Read-only validation and accounting for the frozen source-first study.

No model loading, tokenization, prompt preparation, or evidence writes. The
review checks exact derived inputs and retained receipts; it does not infer
understanding from length, choices, or successful completion.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan = sibling("study_source_first")
old = sibling("study_evidence_order_review")
sha, read_json, digest = old.sha, old.read_json, plan.digest
FIELDS = ("proxy_status", "fixture_role", "shown_call_path", "saved_note")
OUTCOMES = {"returned", "generation_error", "admission_unavailable", "cell_wall_resource_limit", "dependency_unavailable"}


def verify_hashes(mapping, label):
    for path, expected in mapping.items():
        if digest(path) != expected:
            raise ValueError(f"{label} identity differs: {path}")


def validate_inputs(root, protocol):
    if protocol.get("schema") != "study_source_first_v1" or protocol["trials"] != plan.trial_specs():
        raise ValueError("source-first schema or frozen trial plan differs")
    predecessor = Path(protocol["previous"]["path"])
    if protocol["previous"]["sha256"] != plan.PREVIOUS_SHA or digest(predecessor) != plan.PREVIOUS_SHA:
        raise ValueError("predecessor protocol identity differs")
    prior = read_json(predecessor)
    blocks = {}
    required = {"original-evidence", "evidence", "freezer-source", "runtime-source", "reviewer-source"}
    if set(protocol["blocks"]) not in (required, required | {"rubric"}):
        raise ValueError("frozen block inventory differs")
    for name, receipt in protocol["blocks"].items():
        raw = (root / f"block-{name}.txt").read_bytes()
        if receipt != {"sha256": sha(raw), "bytes": len(raw)}:
            raise ValueError(f"frozen block differs: {name}")
        blocks[name] = raw.decode()
    if {p.name for p in root.glob("block-*.txt")} != {f"block-{name}.txt" for name in blocks}:
        raise ValueError("undeclared frozen block")
    for name, filename in (("freezer-source", "study_source_first.py"), ("runtime-source", "study_source_first_runtime.py"), ("reviewer-source", "study_source_first_review.py")):
        if blocks[name].encode() != Path(__file__).with_name(filename).read_bytes():
            raise ValueError(f"running source differs from frozen {name}")
    if (sha(blocks["original-evidence"].encode()) != prior["blocks"]["evidence"]["sha256"]
            or blocks["original-evidence"] != (predecessor.parent / "block-evidence.txt").read_text()
            or blocks["evidence"] != plan.adapt_evidence(blocks["original-evidence"])):
        raise ValueError("historical source/receipt adaptation differs")
    for field, expected in (("system", plan.SYSTEM), ("question", plan.QUESTION),
                            ("first_invitation", plan.FIRST), ("final_invitation", plan.FINAL),
                            ("first_wrapper", plan.FIRST_WRAPPER), ("account_wrapper", plan.ACCOUNT_WRAPPER),
                            ("evidence", blocks["evidence"]), ("accounts", prior["accounts"]),
                            ("original_provenance", prior["provenance"])):
        if protocol[field] != expected:
            raise ValueError(f"frozen prompt field differs: {field}")
    for field in ("model", "runtime", "settings", "guards"):
        if protocol[field] != prior[field]:
            raise ValueError(f"inherited runtime field differs: {field}")
    if (root / "system.txt").read_text() != protocol["system"] or read_json(root / "criteria.json") != protocol["criteria"]:
        raise ValueError("system or criteria receipt differs")
    if set(protocol["source_map"]) != set(prior["source_map"]):
        raise ValueError("source snapshot inventory differs")
    if {p.name for p in (root / "source-snapshot").iterdir()} != set(protocol["source_map"]):
        raise ValueError("source snapshot directory inventory differs")
    for name, receipt in protocol["source_map"].items():
        original = prior["source_map"][name]
        local = root / "source-snapshot" / name
        if receipt != {**original, "copy": str(local.resolve())}:
            raise ValueError(f"source identity fields differ: {name}")
        if digest(local) != original["sha256"] or digest(predecessor.parent / "source-snapshot" / name) != original["sha256"]:
            raise ValueError(f"source snapshot bytes differ: {name}")
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if manifest["protocol_sha256"] != digest(root / "protocol.json"):
            raise ValueError("manifest protocol identity differs")
        expected_frozen = {str(p) for p in (root / "protocol.json", root / "criteria.json", root / "system.txt", *sorted(root.glob("block-*.txt")))}
        expected_snapshots = {str(p) for p in (root / "source-snapshot").iterdir()}
        if set(manifest["frozen_files"]) != expected_frozen or set(manifest["source_snapshots"]) != expected_snapshots:
            raise ValueError("manifest frozen file inventory differs")
        required_sources = {str(Path(__file__).with_name(name).resolve()) for name in ("study_source_first.py", "study_source_first_runtime.py", "study_source_first_review.py", "study_evidence_order.py")}
        required_sources |= {str(Path(protocol["runtime"]) / name) for name in ("generation_controls.py", "coupled_astrid_server.py", "real_model_coupling_study.py")}
        libraries = ("mlx_lm/generate.py", "mlx_lm/sample_utils.py", "mlx_lm/models/gemma4_text.py", "mlx_lm/models/cache.py")
        remaining = set(manifest["sources"]) - required_sources
        if not required_sources <= set(manifest["sources"]) or len(remaining) != len(libraries) or any(sum(p.endswith("/" + name) for p in remaining) != 1 for name in libraries):
            raise ValueError("manifest generation source inventory differs")
        for section in ("sources", "frozen_files", "source_snapshots"):
            verify_hashes(manifest[section], "manifest " + section)
        model = Path(protocol["model"])
        index = read_json(model / "model.safetensors.index.json")
        assets = set(index["weight_map"].values()) | {"config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja", "model.safetensors.index.json"}
        if set(manifest["assets"]) != assets:
            raise ValueError("manifest model asset inventory differs")
        verify_hashes({str(model / name): value for name, value in manifest["assets"].items()}, "model asset")
        if set(manifest["versions"]) != {"mlx", "mlx-lm", "numpy", "transformers", "tokenizers"}:
            raise ValueError("manifest dependency version inventory differs")
    return {"protocol_sha256": digest(root / "protocol.json"), "predecessor_sha256": plan.PREVIOUS_SHA,
            "source_snapshots": len(protocol["source_map"]), "manifest_available": manifest_path.exists(),
            "exact_factor_reconstruction": True, "model_asset_hashes_checked": manifest_path.exists()}


def native_eos_ids(protocol):
    # Same immutable local assets, no MLX imports or tokenizer execution.
    config = read_json(Path(protocol["model"]) / "generation_config.json")
    value = config.get("eos_token_id")
    values = value if isinstance(value, list) else [value]
    if not values or any(type(token) is not int or token < 0 for token in values):
        raise ValueError("native EOS IDs unavailable in pinned model configuration")
    return set(values)


def validate_render(root, spec, messages):
    path = root / f"rendered-{spec['id']}.json"
    if not path.exists():
        return None
    row = read_json(path)
    if row["id"] != spec["id"] or row["arm"] != spec["arm"] or row["rendered_sha256"] != sha(row["rendered_text"].encode()):
        raise ValueError("rendered trial identity differs")
    old.natural_integer(row["token_count"], "prompt token count")
    if len(row["token_ids"]) != row["token_count"]:
        raise ValueError("rendered token count differs")
    for token in row["token_ids"]:
        old.natural_integer(token, "prompt token ID")
    position = 0
    for message in messages:
        content = message["content"].strip()
        found = row["rendered_text"].find(content, position)
        if found < 0:
            raise ValueError("rendered messages are absent or out of order")
        position = found + len(content)
    system, user = [message["content"].strip() for message in messages]
    expected = ("<bos><|turn>system\n" + system + "<turn|>\n<|turn>user\n" + user
                + "<turn|>\n<|turn>model\n<|channel>thought\n<channel|>")
    if row["rendered_text"] != expected:
        raise ValueError("rendered text differs from the pinned Gemma thinking-off frame")
    return row


def validate_result(row, rendering, settings, eos_ids):
    result = row["result"]
    if row["outcome"] == "returned":
        if row.get("error") or result["finish"] == "error":
            raise ValueError("returned outcome hides generation error")
    elif row["outcome"] == "generation_error":
        if not row.get("error") or result["finish"] != "error":
            raise ValueError("generation-error outcome lacks matching error")
    else:
        raise ValueError("unavailable outcome contains generation result")
    if not isinstance(result["text"], str) or result["response_sha256"] != sha(result["text"].encode()):
        raise ValueError("response hash differs")
    cache = old.validate_result(result, rendering, settings)
    termination, finish = result.get("termination"), result["finish"]
    if finish == "error":
        if termination is not None or result["terminal_tokens"]:
            raise ValueError("error outcome claims terminal evidence")
    elif finish == "length":
        if not isinstance(termination, dict) or termination.get("kind") != "output_allowance" or termination.get("model_eos_reached") is not False or termination.get("stop_token_id") is not None:
            raise ValueError("allowance termination evidence differs")
    else:
        if not isinstance(termination, dict) or not result["tokens"] or termination.get("stop_token_id") != result["tokens"][-1]:
            raise ValueError("stop token differs from yielded terminal token")
        native = result["tokens"][-1] in eos_ids
        if termination.get("model_eos_reached") is not native or (termination.get("kind") == "model_eos") is not native:
            raise ValueError("claimed model EOS differs from native token identity")
        if not native and termination.get("kind") not in ("channel_boundary", "server_stop_special"):
            raise ValueError("unknown non-native terminal reason")
    return cache


def expected_input(root, protocol, spec, rows, eligibility):
    dependency, first_text = None, None
    if spec["dependency"]:
        first_id = spec["dependency"]
        if first_id not in rows:
            return None, None
        first = rows[first_id]
        result = first.get("result") or {}
        dependency = {"id": first_id, "result_file_sha256": digest(root / f"{first_id}.json"),
                      "eligible": eligibility[first_id], "outcome": first["outcome"],
                      "finish": result.get("finish"), "termination": result.get("termination")}
        if not dependency["eligible"]:
            return None, dependency
        first_text = result["text"]
        dependency["response_sha256"] = sha(first_text.encode())
    return {"spec": spec, "messages": plan.build_messages(protocol, spec, first_text), "dependency": dependency}, dependency


def load_annotations(root, specs):
    path = root / "annotations.json"
    rows = read_json(path) if path.exists() else None
    if rows is None:
        return {}
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("annotations must be a list or null")
    indexed = {row["id"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed) - {s["id"] for s in specs}:
        raise ValueError("duplicate or unplanned annotation")
    return indexed


def validate_annotation_quotes(value, text):
    """Validate response and ambiguity-context quotations at any nesting depth."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("quote", "context_quote", "quoted_context"):
                if not isinstance(item, str) or not item or item not in text:
                    raise ValueError("annotation/context quote absent from response")
            elif key == "context_quotes":
                if not isinstance(item, list):
                    raise ValueError("context_quotes must be a list")
                for quote in item:
                    if not isinstance(quote, str) or not quote or quote not in text:
                        raise ValueError("ambiguity context quote absent from response")
            else:
                validate_annotation_quotes(item, text)
    elif isinstance(value, list):
        for item in value:
            validate_annotation_quotes(item, text)


def summarize(cells):
    return {"planned": len(cells), "outcomes": dict(Counter(row["outcome"] for row in cells)),
            "nonempty": sum(row["nonempty"] for row in cells), "eligible": sum(row["eligible"] for row in cells),
            "annotated": sum(row["annotation"] is not None for row in cells)}


def review(root):
    root = Path(root).resolve()
    protocol = read_json(root / "protocol.json")
    integrity = validate_inputs(root, protocol)
    specs = protocol["trials"]
    ids = {s["id"] for s in specs}
    for prefix in ("input-", "rendered-", ""):
        for path in root.glob(prefix + "source-first-*.json"):
            if path.stem.removeprefix(prefix) not in ids:
                raise ValueError("unplanned trial artifact")
    eos_ids = native_eos_ids(protocol)
    annotations = load_annotations(root, specs)
    rows, eligibility, cells, caches, renderings = {}, {}, [], {}, {}
    for spec in specs:
        trial_id = spec["id"]
        output_path = root / f"{trial_id}.json"
        row = read_json(output_path) if output_path.exists() else None
        if row is not None and (row.get("spec") != spec or row.get("outcome") not in OUTCOMES):
            raise ValueError("result spec or outcome differs from plan")
        expected, dependency = expected_input(root, protocol, spec, rows, eligibility)
        input_path = root / f"input-{trial_id}.json"
        retained = read_json(input_path) if input_path.exists() else None
        if retained is not None and (expected is None or retained != expected):
            raise ValueError("derived input or dependency identity differs")
        rendering = validate_render(root, spec, expected["messages"]) if expected is not None else None
        if (root / f"rendered-{trial_id}.json").exists() and (rendering is None or retained is None):
            raise ValueError("rendered trial lacks an eligible exact input")
        renderings[trial_id] = None if rendering is None else {k: rendering[k] for k in ("token_count", "rendered_sha256")}
        result = row.get("result") if row else None
        if row is not None:
            if row["outcome"] == "dependency_unavailable":
                if not spec["dependency"] or dependency is None or dependency["eligible"] or row.get("dependency") != dependency or result is not None or retained is not None:
                    raise ValueError("dependency-unavailable outcome contradicts prerequisite")
            elif expected is None or retained is None:
                raise ValueError("attempt lacks a valid derived input")
            elif result is None and row["outcome"] in ("returned", "generation_error"):
                raise ValueError("generated outcome lacks a generation result")
            if result is not None:
                caches[trial_id] = validate_result(row, rendering, protocol["settings"], eos_ids)
            rows[trial_id] = row
        nonempty = bool(result and result["text"].strip())
        eligible = bool(nonempty and row["outcome"] == "returned" and result["finish"] == "stop" and result["termination"]["kind"] == "model_eos")
        eligibility[trial_id] = eligible
        annotation = annotations.get(trial_id)
        if annotation is not None:
            if result is None or annotation.get("response_sha256") != result["response_sha256"]:
                raise ValueError("annotation lacks matching response identity")
            validate_annotation_quotes(annotation, result["text"])
        cell = {**spec, "outcome": row["outcome"] if row else "missing", "nonempty": nonempty, "eligible": eligible,
                "annotation": annotation, "assessment": {k: (annotation or {}).get(k) or "unassessed" for k in FIELDS}}
        if result:
            cell.update({k: result[k] for k in ("finish", "termination", "prompt_tokens", "completion_tokens", "seconds", "admission_seconds", "response_sha256")})
            cell["authored"] = old.previous_review.authored_fields(result["text"])
        cells.append(cell)
    completed_path = root / "completed.json"
    if completed_path.exists():
        completed = read_json(completed_path)
        if len(rows) != len(specs) or completed.get("cells") != len(specs) or completed.get("live_writes") is not False or completed.get("sources_unchanged") is not True or completed.get("model_assets_unchanged") is not True or not integrity["manifest_available"]:
            raise ValueError("completion receipt contradicts recorded outcomes or identity checks")
    pairs, blocks = [], []
    for block, first_seed in plan.BLOCKS:
        first = next(c for c in cells if c["block"] == block and c["phase"] == "first")
        finals = [c for c in cells if c["block"] == block and c["phase"] == "final"]
        blocks.append({"block": block, "first_seed": first_seed, "first_id": first["id"], "first_outcome": first["outcome"],
                       "first_eligible": first["eligible"], "finals": summarize(finals), "carried_dependencies": [c["id"] for c in finals if c["dependency"]]})
        for account in ("retained", "supported"):
            members = [c for c in finals if c["arm"].startswith(account + "_")]
            pairs.append({"block": block, "account": account, **summarize(members),
                          "outcomes": {c["arm"].split("_")[1]: c["outcome"] for c in members},
                          "complete_nonempty": all(c["nonempty"] for c in members),
                          "complete_eligible": all(c["eligible"] for c in members), "ids": [c["id"] for c in members]})
    return {"schema": "study_source_first_review_v1", **summarize(cells), "first": summarize([c for c in cells if c["phase"] == "first"]),
            "finals": summarize([c for c in cells if c["phase"] == "final"]), "cells": cells, "within_account_pairs": pairs,
            "complete_eligible_pairs": sum(p["complete_eligible"] for p in pairs), "dependency_blocks": blocks,
            "integrity": integrity, "renderings": renderings, "cache_progression": caches, "completed": completed_path.exists(),
            "limits": "Two first-read dependency clusters, eight final trials, four within-account contrasts, one historical episode. Carriage includes extra visible context and compute, with fresh caches; it is not hidden persistent reasoning. Nonempty is separate from eligible native-EOS completion. Missing annotations are unassessed. Retained token receipts are not independently retokenized. Source-supported preservation, uncertainty, omitted notes and voluntary choices remain valid. No model calls, generated-choice execution, or live state writes."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.root), indent=2, ensure_ascii=False))
