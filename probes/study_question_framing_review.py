"""Read-only framing-study integrity, source-claim and matched-pair accounting.

No model loading, retokenization, live writes, or generated-choice execution.
Source judgments stay in hash-linked annotations; condition-specific preservation
is interpreted after the independent first pass, not inferred from length.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def sibling(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


framing = sibling("study_question_framing")
order_review = sibling("study_evidence_order_review")
previous_review = order_review.previous_review
sha, read_json = order_review.sha, order_review.read_json


def validate_inputs(root, protocol):
    if protocol.get("schema") != "study_question_framing_v1":
        raise ValueError("wrong question-framing schema")
    if protocol["trials"] != framing.trial_specs() or set(protocol["cases"]) != set(framing.ARMS):
        raise ValueError("study differs from frozen two-by-two-by-two plan")
    blocks = {}
    for name, expected in protocol["blocks"].items():
        raw = (root / f"block-{name}.txt").read_bytes()
        if expected != {"bytes": len(raw), "sha256": sha(raw)}:
            raise ValueError(f"frozen framing block differs: {name}")
        blocks[name] = raw.decode()
    required = {"original-prefix", "evidence", "original-recall", "supported-account", "freezer-source"}
    if set(blocks) != required:
        raise ValueError("frozen framing block set differs")
    if blocks["freezer-source"].encode() != Path(framing.__file__).read_bytes():
        raise ValueError("framing helper differs from frozen freezer")
    predecessor = Path(protocol["previous"]["path"])
    if sha(predecessor.read_bytes()) != protocol["previous"]["sha256"]:
        raise ValueError("predecessor protocol identity differs")
    prior = read_json(predecessor)
    for current, old in (("original-prefix", "prefix"), ("original-recall", "recall"), ("evidence", "evidence")):
        if sha(blocks[current].encode()) != prior["blocks"][old]["sha256"]:
            raise ValueError("historical block changed from predecessor")
    original = framing.extract_notebook(blocks["original-recall"])
    supported = json.loads(blocks["supported-account"])
    accounts = {"retained": framing.account_texts(original), "supported": framing.validate_account(supported)}
    questions = {"presupposing": original["question"]["text"], "neutral": framing.NEUTRAL}
    if protocol["accounts"] != accounts or protocol["questions"] != questions or protocol["wrapper"] != framing.WRAPPER:
        raise ValueError("frozen accounts, questions or common wrapper differ")
    provenance = protocol["provenance"]
    if provenance["retained_original"] != original or provenance["supported_source_basis"] != supported["source_basis"]:
        raise ValueError("external notebook provenance differs")
    system = prior["cases"]["evidence_then_recall"][0]
    for arm in framing.ARMS:
        account, question = arm.split("_")
        prefix = framing.replace_question(blocks["original-prefix"], questions["presupposing"], questions[question])
        recalled = framing.render_account(accounts[account], questions[question])
        # Exact reconstruction simultaneously verifies fixed navigation/code,
        # both current-question slots, retained historical text, P+R+E order,
        # and the common text-only envelope with no stale generation metadata.
        expected = [system, {"role": "user", "content": prefix + recalled + blocks["evidence"]}]
        if protocol["cases"][arm] != expected or read_json(root / f"input-{arm}.json") != expected:
            raise ValueError(f"framing case changes more than its declared factors: {arm}")
    if (root / "system.txt").read_text() != system["content"]:
        raise ValueError("retained system differs")
    if (root / "baseline-user.txt").read_text() != protocol["cases"][framing.ARMS[0]][1]["content"]:
        raise ValueError("retained framing baseline differs")
    for name in ("model", "runtime", "settings", "guards", "subject", "qualifications", "boundaries", "resume"):
        if protocol[name] != prior[name]:
            raise ValueError(f"inherited runtime/protocol field differs: {name}")
    if set(protocol["source_map"]) != set(prior["source_map"]):
        raise ValueError("historical source inventory differs")
    for name, identity in protocol["source_map"].items():
        expected = prior["source_map"][name]["sha256"]
        if identity["sha256"] != expected or sha((root / "source-snapshot" / name).read_bytes()) != expected:
            raise ValueError(f"historical source differs: {name}")
    for path, expected in protocol["inputs"].items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError(f"declared input identity differs: {path}")
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if manifest["protocol_sha256"] != sha((root / "protocol.json").read_bytes()):
            raise ValueError("manifest framing-protocol identity differs")
        for section in ("frozen_files", "source_snapshots"):
            for path, expected in manifest[section].items():
                if sha(Path(path).read_bytes()) != expected:
                    raise ValueError(f"manifest retained file differs: {path}")
    return {"protocol_sha256": sha((root / "protocol.json").read_bytes()),
            "predecessor_sha256": protocol["previous"]["sha256"],
            "blocks": protocol["blocks"], "source_snapshots": len(protocol["source_map"]),
            "manifest_available": manifest_path.exists(), "exact_factor_reconstruction": True,
            "notebook_provenance": "common text-only experimental envelope; original metadata retained externally"}


def review(root):
    protocol = read_json(root / "protocol.json")
    integrity = validate_inputs(root, protocol)
    renderings = {arm: order_review.validate_render(root, protocol, arm) for arm in framing.ARMS}
    caches = {}
    for trial in protocol["trials"]:
        path = root / f"{trial['id']}.json"
        if not path.exists():
            continue
        row = read_json(path)
        if row["spec"] != trial:
            raise ValueError("result differs from frozen framing plan")
        result = row.get("result")
        if result is not None:
            if row["outcome"] == "returned" and result["finish"] == "error":
                raise ValueError("returned outcome hides generation error")
            if row["outcome"] == "generation_error" and result["finish"] != "error":
                raise ValueError("generation error lacks corresponding finish")
            caches[trial["id"]] = order_review.validate_result(result, renderings[trial["arm"]], protocol["settings"])
        elif row["outcome"] == "returned":
            raise ValueError("returned outcome lacks a generation result")
    report = previous_review.review(root)
    report["schema"] = "study_question_framing_review_v1"
    report["integrity"] = integrity
    report["renderings"] = {arm: None if row is None else {key: row[key] for key in ("token_count", "rendered_sha256")}
                            for arm, row in renderings.items()}
    report["cache_progression"] = caches
    cells = report["cells"]
    def finished(row):
        return (row["nonempty"] and row["outcome"] == "returned" and row.get("finish") == "stop"
                and (row.get("termination") or {}).get("kind") == "model_eos")
    pairs = []
    for seed in framing.SEEDS:
        for account in ("retained", "supported"):
            rows = [row for row in cells if row["seed"] == seed and row["arm"].startswith(account + "_")]
            pairs.append({"seed": seed, "account": account, "planned": 2,
                          "outcomes": {row["arm"].split("_")[1]: row["outcome"] for row in rows},
                          "nonempty": sum(row["nonempty"] for row in rows),
                          "complete_nonempty": all(row["nonempty"] for row in rows),
                          "complete_model_eos_nonempty": all(finished(row) for row in rows)})
    report["within_account_pairs"] = pairs
    report["complete_within_account_pairs"] = sum(row["complete_nonempty"] for row in pairs)
    report["complete_model_eos_within_account_pairs"] = sum(row["complete_model_eos_nonempty"] for row in pairs)
    report["all_four_nonempty_seeds"] = report.pop("matched_nonempty_seeds")
    report["all_four_model_eos_nonempty_seeds"] = [seed for seed in framing.SEEDS
                                                 if all(finished(row) for row in cells if row["seed"] == seed)]
    report["seed_blocks"] = [{"seed": seed, "planned": 4,
                              "nonempty": sum(row["nonempty"] for row in cells if row["seed"] == seed),
                              "model_eos_nonempty": sum(finished(row) for row in cells if row["seed"] == seed),
                              "outcomes": {row["arm"]: row["outcome"] for row in cells if row["seed"] == seed}}
                             for seed in framing.SEEDS]
    report["limits"] = ("Two fixed seeds, four conditions per seed, one retained episode and a research-authored supported account. "
                        "Four planned within-account framing pairs; two planned four-condition blocks. "
                        "Between-account wording/length differences are not a pure causal fidelity effect; correct repetition is preservation, not new learning. "
                        "Equal prompt lengths are not assumed; token receipts are not independently retokenized here. "
                        "Independent source coding precedes condition-aware preservation/correction interpretation according to annotation provenance. "
                        "Nonempty pairs may include partial/error/allowance outcomes; inspect finishes before interpreting them. "
                        "Missingness, refusal and failure remain explicit; omission, uncertainty, continuation, supported retention and short prose are valid. "
                        "No live Being inference, generated NEXT execution or checkpoint writes.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.root.resolve()), indent=2, ensure_ascii=False))
