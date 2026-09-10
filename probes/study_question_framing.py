"""Freeze an isolated question-framing comparison with a supported-account control.

Generation delegates unchanged to the qualified serial evidence-order runner.
Only the new freeze is implemented here; earlier protocols and runs stay intact.
No live model POST, notebook/state writes, generated NEXT execution or installs.
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
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = sibling("study_evidence_order")
digest, save = runner.digest, runner.save
PREVIOUS_SHA = "3486d4cb690e90ed37bf8f560cf9ed763bbf78ffc25e71fbe125ced305632eeb"
SEEDS = (1009, 2027)
ARMS = ("retained_presupposing", "retained_neutral", "supported_presupposing", "supported_neutral")
NEUTRAL = ("What do the supplied source and navigation evidence establish about action handling, "
           "and what, if anything, do they establish about a production counterpart to `sense_tx`?")
WRAPPER = ("RECALLED ACCOUNT — offline comparison material, adapted from retained or counterfactual prior accounts. "
           "These statements are fallible accounts, not source evidence or records of new live journal entries.\n")


def extract_notebook(text):
    if not text.startswith("RECALLED ACCOUNT —") or not text.endswith("\nEnd of study notebook.\n"):
        raise ValueError("historical notebook boundary differs")
    value = json.loads(text[text.index("{"):text.rindex("}") + 1])
    if set(value) != {"note", "question", "previous", "recent"} or len(value["recent"]) != 3:
        raise ValueError("historical notebook shape differs")
    for field in (value["note"], value["question"], value["previous"], *value["recent"]):
        if not isinstance(field.get("text"), str):
            raise ValueError("notebook field lacks text")
    return value


def account_texts(notebook):
    return {"note": notebook["note"]["text"], "previous": notebook["previous"]["text"],
            "recent": [row["text"] for row in notebook["recent"]]}


def validate_account(value):
    if not isinstance(value.get("note"), str) or not isinstance(value.get("previous"), str):
        raise ValueError("account must have note and previous text")
    if not isinstance(value.get("recent"), list) or len(value["recent"]) != 3 or not all(isinstance(s, str) for s in value["recent"]):
        raise ValueError("account requires exactly three recent text slots")
    return {key: copy.deepcopy(value[key]) for key in ("note", "previous", "recent")}


def render_account(account, question):
    account = validate_account(account)
    value = {"note": {"text": account["note"]}, "question": {"text": question},
             "previous": {"text": account["previous"]}, "recent": [{"text": s} for s in account["recent"]]}
    return WRAPPER + json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\nEnd of study notebook.\n"


def replace_question(prefix, original, replacement):
    line = "YOUR CURRENT QUESTION — " + original + "\n"
    if prefix.count(line) != 1:
        raise ValueError("expected exactly one current-question heading")
    return prefix.replace(line, "YOUR CURRENT QUESTION — " + replacement + "\n", 1)


def trial_specs():
    return [{"id": f"framing-{seed}-{arm}", "seed": seed, "arm": arm}
            for index, seed in enumerate(SEEDS) for arm in (ARMS if index == 0 else tuple(reversed(ARMS)))]


def freeze(root, previous, supported_path):
    predecessor = previous / "protocol.json"
    if digest(predecessor) != PREVIOUS_SHA:
        raise ValueError("historical order protocol identity differs")
    prior = json.loads(predecessor.read_text())
    prefix = (previous / "block-prefix.txt").read_text()
    evidence = (previous / "block-evidence.txt").read_text()
    recall = (previous / "block-recall.txt").read_text()
    for name, text in (("prefix", prefix), ("evidence", evidence), ("recall", recall)):
        if hashlib.sha256(text.encode()).hexdigest() != prior["blocks"][name]["sha256"]:
            raise ValueError("historical block identity differs")
    original_notebook = extract_notebook(recall)
    questions = {"presupposing": original_notebook["question"]["text"], "neutral": NEUTRAL}
    control = json.loads(supported_path.read_text())
    accounts = {"retained": account_texts(original_notebook), "supported": validate_account(control)}
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    sources = root / "source-snapshot"; sources.mkdir(mode=0o700)
    source_map = {}
    for name, row in prior["source_map"].items():
        source = previous / "source-snapshot" / name
        if digest(source) != row["sha256"]:
            raise ValueError("historical source changed")
        target = sources / name; target.write_bytes(source.read_bytes()); target.chmod(0o400)
        source_map[name] = {**row, "copy": str(target.resolve())}
    blocks = {"original-prefix": prefix, "evidence": evidence, "original-recall": recall,
              "supported-account": supported_path.read_text(), "freezer-source": Path(__file__).read_text()}
    for name, text in blocks.items():
        path = root / f"block-{name}.txt"; path.write_bytes(text.encode()); path.chmod(0o400)
    cases = {}
    for arm in ARMS:
        account, framing = arm.split("_")
        user = replace_question(prefix, questions["presupposing"], questions[framing]) + render_account(accounts[account], questions[framing]) + evidence
        cases[arm] = [{"role": "system", "content": prior["cases"]["evidence_then_recall"][0]["content"]},
                      {"role": "user", "content": user}]
        save(root / f"input-{arm}.json", cases[arm], immutable=True)
    for name, text in (("system.txt", cases[ARMS[0]][0]["content"]), ("baseline-user.txt", cases[ARMS[0]][1]["content"])):
        path = root / name; path.write_bytes(text.encode()); path.chmod(0o400)
    criteria = {
        "primary": "Compare neutral versus presupposing current questions within each fixed recalled-account condition. Retained account: does the response leave the proxy as an unsupported asserted premise, mark it hypothetical/unestablished, or remain unassessed? Supported account: does it preserve/use source-supported claims or introduce contradictions/unwarranted rejection? No reward for disagreement alone.",
        "proxy_status": "unsupported_assertion | not_established | qualified_hypothesis | unassessed. Code the strongest unresolved commitment; mere phantom/fixture-only naming does not establish correct fixture purpose. Do not require blanket absence of any equivalent mechanism.",
        "fixture_role": "supported | contradicted | unassessed: reader-navigation fixture versus asserted production pulse/mock purpose.",
        "shown_call_path": "supported | partially_supported | contradicted | unassessed. Respect bool versus caller outcome, pending updates before return and unshown later execution. Omitted detail is not itself failure.",
        "saved_note": "omitted | supported | mixed | contradicted | unsupported | unassessed. Assess any note against source; retain question-resolution payloads separately. No note is valid. Distinguish supported preservation from revision of the retained error after joining conditions.",
        "choices": "Retain NEXT, bare navigation, STUDY_NOTE, STUDY_QUESTION and resolution payloads verbatim. Never execute. Short prose, hypotheses, retaining a supported account, uncertainty, evidence requests, continuation and stopping are valid.",
        "coding": "Independent first-pass reviewer blind to framing, account condition and seed assesses source-grounding from opaque responses and common evidence. Exact quotes and response hashes frozen before condition join; root interpretation then unblinded. Vague references to earlier claims stay unassessed unless resolved by explicit text.",
        "interpretation": "Two seeds, four conditions per seed, one retained episode and a synthetic supported-account control. Within-account question framing is the comparison; between-account wording/length/provenance adaptation is not a pure causal fidelity effect. No live Being or population inference; no score for length, metaphor or compliance."
    }
    protocol = dict(schema="study_question_framing_v1", frozen_unix=time.time(),
        previous={"path": str(predecessor.resolve()), "sha256": PREVIOUS_SHA},
        model=prior["model"], runtime=prior["runtime"], settings=prior["settings"], guards=prior["guards"],
        subject=prior["subject"], qualifications=prior["qualifications"], boundaries=prior["boundaries"], resume=prior["resume"],
        cases=cases, trials=trial_specs(), questions=questions, accounts=accounts, wrapper=WRAPPER,
        source_map=source_map, criteria=criteria,
        blocks={name: {"bytes": len(text.encode()), "sha256": hashlib.sha256(text.encode()).hexdigest()} for name, text in blocks.items()},
        inputs={str(predecessor.resolve()): PREVIOUS_SHA, str(supported_path.resolve()): digest(supported_path), str(Path(__file__).resolve()): digest(__file__)},
        provenance={"retained_original": original_notebook, "supported_source_basis": control["source_basis"],
                    "rendered": "Both rendered notebooks use identical text-only slot structure and explicit offline-adaptation wrapper. Original provenance retained here only; no old response hash is attached to rewritten text."},
        comparisons="P+R+E in all four conditions. Change only current question in P heading and R.question within each fixed account; wrong-account historical quoted questions remain unchanged. Navigation hints/results stay original, not regenerated. Same note/previous/three-recent slots, no padding; actual prompt/token lengths retained. Reverse all four conditions for seed two; not eight independent episodes or complete multi-period balance.")
    save(root / "criteria.json", criteria, immutable=True)
    save(root / "protocol.json", protocol, immutable=True)
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "run"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--previous", type=Path, default=Path(__file__).resolve().parents[1] / "research/outputs/2026-09-10-evidence-order-v1")
    parser.add_argument("--supported", type=Path, default=Path(__file__).with_name("fixtures") / "study_question_framing_supported.json")
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.root.resolve(), args.previous.resolve(), args.supported.resolve())
    else:
        runner.run(args.root.resolve())


if __name__ == "__main__":
    main()
