"""Frozen comparison of adjacent versus grouped claims and source material.

Reuses the unchanged qualified serial runtime. No live prompts/state are changed;
source receipts and selected account excerpts are identical within each pair.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


previous = sibling("study_source_first")
digest, save = previous.digest, previous.save
PREVIOUS_SHA = "98f5fc6a2786e2fa52abfb3fefcd99bbb3b7c699b46bd98cf298f762e47e2aa7"
SEEDS = (3301, 4409)
ARMS = ("retained_grouped", "retained_adjacent", "supported_grouped", "supported_adjacent")
LAYOUTS = {"grouped": ("C1", "C2", "C3", "E1", "E2", "E3"),
           "adjacent": ("C1", "E1", "C2", "E2", "C3", "E3")}
INTRO = """Consider the comparison account and the numbered material below. What is your present account of the question? You may retain, revise, qualify or leave open any statement, ask another question, continue exploring or stop. No format, length, citation or note update is required.
The selected statements repeat exact excerpts from the full comparison account. Their origin labels identify where they were recalled from, not independent evidence. A matching statement/material number identifies material to consider together, not proof of agreement or a verdict. The numbered source and survey receipt retain their stated limits.
"""
DEPENDENCIES = ("study_claim_evidence.py", "study_claim_evidence_review.py",
                "study_source_first.py", "study_source_first_runtime.py", "study_source_first_review.py",
                "study_question_framing.py", "study_question_framing_review.py",
                "study_evidence_order.py", "study_evidence_order_review.py", "study_evidence_revision_review.py")


def trial_specs():
    return [dict(id=f"claim-evidence-{seed}-{arm}", seed=seed, arm=arm)
            for index, seed in enumerate(SEEDS) for arm in (ARMS if index == 0 else tuple(reversed(ARMS)))]


def slot_text(account, slot):
    if slot in ("note", "previous"):
        return account[slot]
    if slot in ("recent[0]", "recent[1]", "recent[2]"):
        return account["recent"][int(slot[7])]
    raise ValueError("unsupported account slot")


def validate_selections(accounts, selections):
    if set(selections) != {"retained", "supported"}:
        raise ValueError("account selection inventory differs")
    for kind, rows in selections.items():
        if len(rows) != 3:
            raise ValueError("three selected statement groups required")
        for row in rows:
            if set(row) != {"slot", "start", "end", "text"}:
                raise ValueError("selection fields differ")
            start, end = row["start"], row["end"]
            text = slot_text(accounts[kind], row["slot"])
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                    or not row["text"] or text[start:end] != row["text"]):
                raise ValueError("selected statement is not the exact original excerpt")


def split_evidence(text):
    a = text.index("NUMBERED SOURCE —")
    b = text.index("astrid/capsules/spectral-bridge/src/autonomous/next_action/mod.rs —")
    pieces = {"E1": text[a:b], "E2": text[:a], "E3": text[b:]}
    if any(not p.strip() for p in pieces.values()) or pieces["E2"] + pieces["E1"] + pieces["E3"] != text:
        raise ValueError("evidence partition loses source bytes")
    return pieces


def cards(protocol, account):
    selected = protocol["selections"][account]
    result = {f"C{i}": f"STATEMENT {i} — exact excerpt from comparison account {row['slot']}; recalled text, not a source observation.\n{row['text']}\nEND STATEMENT {i}\n"
              for i, row in enumerate(selected, 1)}
    result.update({key: f"MATERIAL {key[1:]} — source or scoped receipt to consider; matching numbers do not certify support.\n{text}\nEND MATERIAL {key[1:]}\n"
                   for key, text in protocol["evidence_parts"].items()})
    return result


def build_messages(protocol, spec):
    if spec not in protocol["trials"]:
        raise ValueError("unplanned trial")
    account, layout = spec["arm"].split("_")
    data = protocol["accounts"][account]
    notebook = {"note": {"text": data["note"]}, "question": {"text": protocol["question"]},
                "previous": {"text": data["previous"]}, "recent": [{"text": x} for x in data["recent"]]}
    prefix = (protocol["intro"] + "\nQUESTION — " + protocol["question"] + "\n\n"
              + protocol["account_wrapper"] + json.dumps(notebook, ensure_ascii=False, separators=(",", ":"))
              + "\nEND COMPARISON ACCOUNT\n\n")
    material = cards(protocol, account)
    return [{"role": "system", "content": protocol["system"]},
            {"role": "user", "content": prefix + "\n".join(material[key] for key in LAYOUTS[layout])}]


def verify_adapter(protocol):
    # The unchanged runtime manifests this protocol's source blocks. Check the
    # adapter and all reused research helpers before each prepared generation.
    for path, expected in protocol["adapter_sources"].items():
        if digest(path) != expected:
            raise ValueError(f"frozen adapter source changed: {path}")


def prepare_trial(root, protocol, spec):
    verify_adapter(protocol)
    record = {"spec": spec, "messages": build_messages(protocol, spec), "dependency": None}
    path = root / f"input-{spec['id']}.json"
    if path.exists():
        if json.loads(path.read_text()) != record:
            raise ValueError("frozen trial input differs")
    else:
        save(path, record, immutable=True)
    return record


def freeze(root, predecessor, selections_path, rubric_path):
    root = root.resolve()
    predecessor = predecessor.resolve()
    if digest(predecessor / "protocol.json") != PREVIOUS_SHA:
        raise ValueError("predecessor protocol differs")
    prior = json.loads((predecessor / "protocol.json").read_text())
    evidence = (predecessor / "block-evidence.txt").read_text()
    if hashlib.sha256(evidence.encode()).hexdigest() != prior["blocks"]["evidence"]["sha256"]:
        raise ValueError("historical evidence differs")
    selections = json.loads(selections_path.read_text())
    validate_selections(prior["accounts"], selections)
    sources = {str(Path(__file__).with_name(name).resolve()): digest(Path(__file__).with_name(name)) for name in DEPENDENCIES}
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    (root / "source-snapshot").mkdir(mode=0o700)
    source_map = {}
    for name, identity in prior["source_map"].items():
        old = predecessor / "source-snapshot" / name
        if digest(old) != identity["sha256"]:
            raise ValueError("historical snapshot differs")
        target = root / "source-snapshot" / name
        target.write_bytes(old.read_bytes()); target.chmod(0o400)
        source_map[name] = {**identity, "copy": str(target)}
    blocks = {"evidence": evidence, "rubric": rubric_path.read_text(),
              "selections": json.dumps(selections, indent=2, ensure_ascii=False) + "\n"}
    blocks.update({"source-" + Path(path).stem: Path(path).read_text() for path in sources})
    for name, text in blocks.items():
        path = root / f"block-{name}.txt"; path.write_text(text); path.chmod(0o400)
    criteria = {"comparison": "Four paired adjacent/grouped contrasts in two fixed-seed blocks, one historical Minime episode. Same explicit origins, selections, complete accounts, source bytes and source-role receipt within each pair. Only card order differs.",
                "review": "Independent opaque-response source review before joining allocations. Credit supported preservation, qualify ambiguity in context, retain exact quotes and origins when volunteered. No reward for length or disagreement; original account lacks bool/pending-field detail and that omission is not an error.",
                "limits": "Tests adjacency/order when provenance labels and selected repetition are already present in both conditions; not provenance-versus-none. Distance/recency and card organization remain bundled. Supported control wording/length differs. New first reads and current consumer trace are excluded. Model substitution and fresh caches do not represent live Being learning.",
                "completion": "Account for every frozen trial, keeping missing, resource, empty, error, channel and allowance stops separate from nonempty native EOS. Resume absent trials only; never retry unfavorable completed outcomes."}
    protocol = {"schema": "study_claim_evidence_v1", "frozen_unix": time.time(),
                "previous": {"path": str(predecessor / "protocol.json"), "sha256": PREVIOUS_SHA},
                **{key: copy.deepcopy(prior[key]) for key in ("model", "runtime", "settings", "guards", "system", "question", "account_wrapper", "accounts", "original_provenance")},
                "trials": trial_specs(), "intro": INTRO, "layouts": LAYOUTS, "selections": selections,
                "evidence_parts": split_evidence(evidence), "source_map": source_map, "criteria": criteria,
                "adapter_sources": sources,
                "blocks": {name: {"sha256": hashlib.sha256(text.encode()).hexdigest(), "bytes": len(text.encode())} for name, text in blocks.items()},
                "boundaries": "One serial isolated model; unchanged qualified source-first runtime, fresh RNG/cache per trial, no coupling or live state. Read-only loopback readiness GET only. No generated command/note execution, installs, live prompts, restarts or observation cursor updates."}
    save(root / "protocol.json", protocol, immutable=True)
    save(root / "criteria.json", criteria, immutable=True)
    (root / "system.txt").write_text(protocol["system"]); (root / "system.txt").chmod(0o400)
    for spec in protocol["trials"]:
        prepare_trial(root, protocol, spec)
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "run")); parser.add_argument("root", type=Path)
    base = Path(__file__).resolve().parents[1] / "research/outputs"
    parser.add_argument("--previous", type=Path, default=base / "2026-09-10-source-first-v1")
    parser.add_argument("--selections", type=Path, default=base / "2026-09-10-claim-evidence-preparation/selected-quotes.json")
    parser.add_argument("--rubric", type=Path, default=base / "2026-09-10-claim-evidence-preparation/rubric.md")
    args = parser.parse_args(); root = args.root.resolve()
    if args.mode == "freeze":
        freeze(root, args.previous, args.selections, args.rubric)
    else:
        sibling("study_claim_evidence_review").review(root)
        protocol = json.loads((root / "protocol.json").read_text())
        sibling("study_source_first_runtime").run_plan(root, prepare_trial)
        verify_adapter(protocol)


if __name__ == "__main__":
    main()
