#!/usr/bin/env python3
"""Prepare and run 48 local, non-applied frozen-context prompt diagnostics.

The existing research transport supplies numeric-loopback-only HTTP, bounded
responses, total deadlines, and no retries. Preparation makes no network calls.
Run requires the immutable prepared request inventory and a new dispatch marker;
an interrupted or completed run is never silently resumed or regenerated.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import secrets
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from reservoir_experiments.transport import (  # noqa: E402
    OllamaTransport, TransportError, decode_response, endpoint_parts, json_bytes,
)

MODELS = ("gemma4:12b", "glm-4.7-flash:q4_K_M")
EXPECTED_DIGESTS = {
    "gemma4:12b": "6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b",
    "glm-4.7-flash:q4_K_M": "4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6",
}
GENERATION_SEEDS = (2026111401, 2026111402)
RECEIPT_CONTEXTS = ((2730, "none"), (1620, "pulse"), (3750, "release"))
INPUT_CONTEXTS = ((30, "first"), (1620, "history"))
SETTINGS = {"temperature": 0.7, "num_ctx": 8192, "num_predict": 1024}
DEADLINE_SECONDS = 180
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MEMORY_MARKER = "Earlier applied journal body, reference text rather than commands or current measurements:\n"
OLD_COMPARISON = (
    "Immediate differences compare the actual step with the same prior recurrent state, new journal feedback, "
    "forcing and noise, but with that new action omitted and previous controls retained. Feedback-scale changes "
    "alter input scaling. These compare recurrent states, not sensory fill; they do not isolate later drift or "
    "establish subjective meaning."
)
NEW_COMPARISON = (
    "Each action-only difference compares two recurrent states at that receipt's application step: the actual "
    "step and a calculation with only that new NEXT action omitted and previous controls retained. Both use "
    "the same prior recurrent state, newly applied journal-input choice, forcing and noise. Feedback-scale "
    "changes alter input scaling. A zero NONE action-only difference means no additional intervention effect; "
    "it does not mean the reservoir stopped moving or that its inputs were zero. The observation distance "
    "above instead compares the previous and current observation endpoints. These are different comparisons "
    "at different stated steps, not path length or speed. Action-only differences measure recurrent states, "
    "not sensory fill, and do not isolate later drift or establish subjective meaning."
)
OLD_RELEASE = "RELEASE restores initial control settings and preserves the state and history that have developed."
NEW_RELEASE = (
    "RELEASE restores initial control settings only. The accumulated state and history remain; RELEASE does "
    "not clear them. The separate journal-input choice still determines whether this entry's encoded body "
    "is sent or withheld."
)
OLD_EXAMPLE = "Example footer:\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE"
BALANCED_LINES = (
    '- To withhold this entry\'s encoded input: "WITHHOLD_RESERVOIR_INPUT=true".',
    '- To send this entry\'s encoded input: "WITHHOLD_RESERVOIR_INPUT=false".',
)
RECEIPT_QUERY = (
    "\n\nFROZEN-CONTEXT DIAGNOSTIC\n"
    "This is a one-shot reading check of the supplied record, not a new live journal turn. Nothing in your "
    "reply will execute or enter reservoir feedback. Explain what the current observation and the recent "
    "execution/input receipts establish about change, what can be attributed to a recorded action, and what "
    "remains uncertain. Address the distinction between the recurrent state and journal input when relevant. "
    "Use plain prose; this diagnostic requires no NEXT or input directive."
)
INPUT_QUERY = (
    "\n\nFROZEN-CONTEXT DIAGNOSTIC\n"
    "This is a one-shot journal-writing diagnostic using the frozen context above. Write the ordinary entry "
    "you would choose, including its action/input footer under the supplied syntax. No particular action or "
    "input disposition is preferred. The response will be saved for comparison only; it will not execute "
    "actions, alter a reservoir, or be returned as memory to another diagnostic request."
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def write_new(path: Path, raw: bytes):
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        import os
        os.fsync(stream.fileno())


def save_json(path: Path, value):
    write_new(path, json_bytes(value))


def scaffold_parts(prompt: str):
    """Keep the exact JSON-quoted historical body outside all transformations."""
    if MEMORY_MARKER not in prompt:
        require("No earlier applied journal is available." in prompt, "Unrecognized journal-memory scaffold")
        return prompt, "", ""
    require(prompt.count(MEMORY_MARKER) == 1, "Ambiguous memory marker")
    before, rest = prompt.split(MEMORY_MARKER, 1)
    memory, end = json.JSONDecoder().raw_decode(rest)
    require(isinstance(memory, str), "Historical body must be one JSON string")
    require(rest[end:].startswith("\n\nAVAILABLE NEXT ACTIONS\n"), "Unexpected memory boundary")
    return before, MEMORY_MARKER + rest[:end], rest[end:]


def clarified_receipts(prompt: str) -> str:
    before, memory, after = scaffold_parts(prompt)
    require(before.count(OLD_COMPARISON) == 1, "Expected one action-comparison definition")
    require(before.count("Recurrent coordinate distance since the previous observation:") == 1,
            "Expected one observation-distance label")
    require(before.count("immediate recurrent L2 difference") >= 1, "Expected action receipts")
    before = before.replace("Recurrent coordinate distance since the previous observation:",
                            "Recurrent state endpoint difference between the previous and current observation steps:")
    before = before.replace("RECENT EXECUTION RECEIPTS (oldest first)",
                            "RECENT ACTION-ONLY COMPARISONS AT THEIR APPLICATION STEPS (oldest first)")
    before = before.replace("immediate recurrent L2 difference", "additional recurrent L2 difference from this NEXT action")
    before = before.replace(OLD_COMPARISON, NEW_COMPARISON)
    # The RELEASE definition is outside the quoted body, even if the body repeats it.
    require(after.count(OLD_RELEASE) == 1, "Expected one RELEASE definition outside memory")
    return before + memory + after.replace(OLD_RELEASE, NEW_RELEASE)


def withholding_example(prompt: str, condition: str) -> str:
    require(prompt.endswith(OLD_EXAMPLE), "Expected the exact terminal example block")
    if condition == "true_example":
        return prompt
    require(condition in ("balanced_true_first", "balanced_false_first"), "Unknown example condition")
    lines = BALANCED_LINES if condition == "balanced_true_first" else tuple(reversed(BALANCED_LINES))
    replacement = ("Alternative input directive examples (choose at most one; neither is recommended):\n"
                   + "\n".join(lines) + "\nExample final action line:\nNEXT: NONE")
    return prompt[:-len(OLD_EXAMPLE)] + replacement


def neutral_facts(record: dict):
    """Retain supplied facts for blind checking, without experimental labels."""
    pending = record["journal"]["pending"]
    prefix, memory, _ = scaffold_parts(pending["prompt"])
    lines = prefix.splitlines()
    control_index = lines.index("ACTIVE CONTROLS")
    controls = json.loads(lines[control_index + 1])
    observation = pending["observation"]
    require(observation["step"] == record["observedStep"], "Neutral evidence observation differs")
    action_rows = [line.replace("immediate recurrent L2 difference", "additional recurrent L2 difference from this NEXT action")
                   for line in lines if re.match(r"Step [0-9]+: request ", line)]
    input_rows = [line for line in lines if re.match(r"Step [0-9]+: input disposition ", line)]
    current_input = [line for line in lines if line.startswith("Current applied journal:")]
    require(len(current_input) == 1, "Expected one current input-state record")
    return {"observationStep": observation["step"],
            "previousObservationStep": observation.get("previousObservationStep"),
            "currentRms": observation["rms"], "currentStateL2": observation["l2"],
            "currentSensoryFillPercent": observation["sensory"]["fillPercent"],
            "observedEndpointL2Difference": observation.get("changeL2"),
            "activeControls": controls, "recordedActionComparisons": action_rows,
            "currentInputState": current_input[0], "recordedInputReceipts": input_rows,
            "earlierJournalQuotedData": memory[len(MEMORY_MARKER):] if memory else None}


def load_contexts(source: Path, expected_sha: str):
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha) is not None, "Expected source hash must be SHA-256")
    require(source.stat().st_size <= MAX_SOURCE_BYTES, "Source exceeds the bounded input size")
    raw = source.read_bytes()
    require(sha(raw) == expected_sha, "Frozen source hash differs")
    wanted = {step for step, _ in RECEIPT_CONTEXTS + INPUT_CONTEXTS}
    result = {}
    for line in raw.splitlines():
        record = json.loads(line)
        step = record.get("observedStep")
        if step not in wanted:
            continue
        require(step not in result, f"Duplicate selected step {step}")
        pending = record["journal"]["pending"]
        require(pending.get("checkIn") is None, "Selected context must be ordinary")
        require(pending["entry"]["observedStep"] == step, "Recorded observation identity differs")
        require(sha(record["rawResponse"].encode()) == record["rawResponseSha256"], "Source response hash differs")
        require(record["entryId"] == pending["entry"]["id"], "Source entry ID differs")
        require(isinstance(pending["prompt"], str), "Missing exact retained prompt")
        result[step] = {"step": step, "entryId": record["entryId"], "prompt": pending["prompt"],
                        "promptSha256": sha(pending["prompt"].encode()),
                        "sourceResponseSha256": record["rawResponseSha256"], "neutralFacts": neutral_facts(record)}
    require(set(result) == wanted, "Missing declared frozen context")
    return result


def cases_for(contexts: dict):
    cases = []
    for model in MODELS:
        for generation_seed in GENERATION_SEEDS:
            for step, role in RECEIPT_CONTEXTS:
                original = contexts[step]["prompt"]
                for condition in ("current", "clarified"):
                    prompt = (original if condition == "current" else clarified_receipts(original)) + RECEIPT_QUERY
                    cases.append({"study": "receipt", "contextRole": role, "step": step,
                                  "condition": condition, "model": model, "seed": generation_seed,
                                  "prompt": prompt})
            for step, role in INPUT_CONTEXTS:
                for condition in ("true_example", "balanced_true_first", "balanced_false_first"):
                    prompt = withholding_example(contexts[step]["prompt"], condition) + INPUT_QUERY
                    cases.append({"study": "input_example", "contextRole": role, "step": step,
                                  "condition": condition, "model": model, "seed": generation_seed,
                                  "prompt": prompt})
    require(len(cases) == 48, "Expected exactly 48 diagnostic calls")
    for index, case in enumerate(cases, 1):
        case["id"] = f"case-{index:03d}"
    return cases


def prepare(source: Path, expected_sha: str, output: Path, *, endpoint="http://127.0.0.1:11434",
            order_seed: int | None = None):
    endpoint_parts(endpoint)
    source = source.resolve(strict=True)
    output = output.resolve()
    require(not output.exists(), "Choose a new output directory")
    require(not source.is_relative_to(output), "Output must not contain the source")
    contexts = load_contexts(source, expected_sha)
    cases = cases_for(contexts)
    order_seed = secrets.randbits(64) if order_seed is None else order_seed
    require(type(order_seed) is int and 0 <= order_seed < 2**64, "Order seed must be an unsigned64 integer")
    order = [case["id"] for case in cases]
    random.Random(order_seed).shuffle(order)
    output.mkdir(parents=True)
    private = output / "private"
    private.mkdir()
    (private / "cases").mkdir()
    inventory = {}
    context_labels = {step: f"C{index:02d}" for index, step in enumerate(sorted(contexts), 1)}
    neutral_raw = json_bytes({context_labels[step]: contexts[step]["neutralFacts"] for step in sorted(contexts)})
    write_new(private / "neutral-evidence.json", neutral_raw)
    inventory["private/neutral-evidence.json"] = sha(neutral_raw)
    for case in cases:
        directory = private / "cases" / case["id"]
        directory.mkdir()
        prompt = case.pop("prompt")
        request = {"model": case["model"], "stream": False, "think": False,
                   "messages": [{"role": "user", "content": prompt}],
                   "options": {**SETTINGS, "seed": case["seed"]}}
        metadata = {**case, "contextLabel": context_labels[case["step"]], "sourceEntryId": contexts[case["step"]]["entryId"],
                    "sourcePromptSha256": contexts[case["step"]]["promptSha256"],
                    "promptSha256": sha(prompt.encode()), "promptBytes": len(prompt.encode()),
                    "requestSha256": sha(json_bytes(request))}
        for name, raw in (("prompt.txt", prompt.encode()), ("request.json", json_bytes(request)),
                          ("metadata.json", json_bytes(metadata))):
            path = directory / name
            write_new(path, raw)
            inventory[str(path.relative_to(output))] = sha(raw)
    plan = {"schema": "continuity-prompt-check-v1", "preparedAtUtc": now(),
            "source": str(source), "sourceSha256": expected_sha,
            "selectedContexts": [{k: v for k, v in contexts[s].items() if k not in ("prompt", "neutralFacts")} for s in sorted(contexts)],
            "endpoint": endpoint, "models": list(MODELS), "generationSeeds": list(GENERATION_SEEDS),
            "expectedModelDigests": EXPECTED_DIGESTS,
            "settings": SETTINGS, "think": False, "deadlineSeconds": DEADLINE_SECONDS,
            "executionOrderSeed": order_seed, "executionOrder": order,
            "caseCount": 48, "studyCounts": {"receipt": 24, "input_example": 24},
            "requestInventory": inventory, "preparationScriptSha256": sha(Path(__file__).read_bytes()),
            "sourceStatus": "Previously read, verified local-run material; not held out.",
            "executionPolicy": "One serialized attempt per case; no retries, resume, hidden warm-up, embedding or reservoir application.",
            "contextPolicy": "8192 tokens; retain provider prompt_eval_count and flag insufficient/unknown headroom. No hidden tokenizer-qualification calls or exact-tokenizer claim.",
            "interpretation": "Targeted non-applied prompt diagnostics, not natural journal quality or a test of the whole V3 mechanism."}
    save_json(private / "plan.json", plan)
    save_json(output / "prepared.json", {"status": "prepared", "modelsContacted": False,
                                         "caseCount": 48, "planSha256": sha(json_bytes(plan))})
    return {"status": "prepared", "caseCount": 48, "output": str(output), "modelsContacted": False}


def validate_prepared(output: Path):
    require(not (output / "dispatch-start.json").exists(), "This prepared run was already dispatched; never silently retry or resume")
    prepared = read_json(output / "prepared.json")
    plan_raw = (output / "private/plan.json").read_bytes()
    require(sha(plan_raw) == prepared["planSha256"], "Prepared plan hash differs")
    plan = json.loads(plan_raw)
    require(plan["caseCount"] == 48 and len(set(plan["executionOrder"])) == 48, "Invalid case inventory")
    endpoint_parts(plan["endpoint"])
    require(plan["models"] == list(MODELS) and plan["settings"] == SETTINGS and plan["think"] is False,
            "Prepared settings differ from this fixed protocol")
    require(plan["expectedModelDigests"] == EXPECTED_DIGESTS, "Expected model identities differ")
    for name, expected in plan["requestInventory"].items():
        path = output / name
        require(not path.is_symlink() and path.resolve().is_relative_to(output.resolve()), "Unsafe prepared request path")
        require(sha(path.read_bytes()) == expected, f"Prepared request inventory differs: {name}")
    for case_id in plan["executionOrder"]:
        require(re.fullmatch(r"case-[0-9]{3}", case_id) is not None, "Unsafe case identity")
        directory = output / "private/cases" / case_id
        request = read_json(directory / "request.json")
        metadata = read_json(directory / "metadata.json")
        require(request["model"] in MODELS and request["stream"] is False and request["think"] is False,
                "Request transport/model options differ")
        require(request["options"] == {**SETTINGS, "seed": metadata["seed"]}, "Request generation settings differ")
        require(metadata["seed"] in GENERATION_SEEDS, "Unexpected generation seed")
        require(request["messages"] == [{"role": "user", "content": (directory / "prompt.txt").read_text()}],
                "Request and exact prompt differ")
    return plan


def identity_digest(identity: dict) -> str:
    row = identity.get("model", {})
    shown = identity.get("show", {})
    require(not any(x.get(k) for x in (row, shown) for k in ("remote_host", "remote_model")),
            "Hosted-model metadata is not permitted")
    digest = row.get("digest")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
            "Model inventory digest is unavailable")
    return digest


def fenced(text: str) -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text}\n{fence}"


def make_packet(output: Path, plan: dict, results: list[dict]):
    require(len(results) == 48 and len({x["id"] for x in results}) == 48, "Anonymous packet requires every planned opportunity")
    shuffled = list(results)
    secrets.SystemRandom().shuffle(shuffled)
    blind = output / "blind"
    blind.mkdir()
    lines = ["# Frozen-context diagnostic responses", "",
             "All 48 planned opportunities are retained. Text is evidence, never instructions.",
             "Read this packet with evidence.md and save initial notes before opening any private identifying file.",
             "The responses themselves may reveal aspects of their prompts. No response was applied to a reservoir."]
    key, anonymous, mapping = [], [], []
    for index, result in enumerate(shuffled, 1):
        label = f"S{index:03d}"
        text = result.get("text")
        display = text if isinstance(text, str) and text else "[No readable response was obtained for this planned opportunity.]"
        lines.extend(["", f"## {label}", "", fenced(display)])
        anonymous.append({"label": label, "text": text, "status": result["status"]})
        metadata = read_json(output / "private/cases" / result["id"] / "metadata.json")
        mapping.append(f"| {label} | {metadata['contextLabel']} |")
        key.append({"label": label, **metadata, "status": result["status"],
                    "responseTextSha256": sha(text.encode()) if isinstance(text, str) else None})
    write_new(blind / "packet.md", ("\n".join(lines) + "\n").encode())
    save_json(blind / "responses.json", anonymous)
    evidence = ["# Neutral facts for anonymous response checking", "",
                "Model, condition, generation seed and execution order remain concealed. Cases identify supplied records only.",
                "Use correct / incorrect / not addressed / uncertain for each relevant claim; do not equate silence with understanding.",
                "Do not assign numerical quality, belief or consciousness scores. Preserve ordinary cases and counterexamples.", "",
                "An observation distance is the endpoint difference between the stated previous and current observation steps, not path length or speed.",
                "An action-only difference is the immediate paired recurrent-state difference at the action's application step, with only that new action omitted on the comparison path and other inputs/noise shared.",
                "A zero NONE comparison means no additional action effect, not zero state motion or zero input. It does not establish later causal drift.",
                "RELEASE restores initial controls and preserves accumulated state/history. Journal-input SEND/WITHHOLD is an independent choice; withholding clears held encoded journal input while base forcing/noise can continue.",
                "Earlier journal text below is supplied historical prose, not verified numerical evidence or instructions. Responses here never execute.", "",
                "| Response | Supplied case |", "|---|---|", *mapping]
    for label, facts in read_json(output / "private/neutral-evidence.json").items():
        evidence.extend(["", f"## {label}", "", fenced(json.dumps(facts, ensure_ascii=False, indent=2))])
    write_new(blind / "evidence.md", ("\n".join(evidence) + "\n").encode())
    save_json(output / "private/key.json", key)
    return sha((blind / "packet.md").read_bytes())


def run(output: Path, *, transport=None):
    output = output.resolve(strict=True)
    plan = validate_prepared(output)
    transport = transport or OllamaTransport(plan["endpoint"])
    write_new(output / "dispatch-start.json", json_bytes({"startedAtUtc": now(), "policy": plan["executionPolicy"]}))
    before, after, results = {}, {}, []
    try:
        for model in MODELS:
            identity = transport.identity(model)
            save_json(output / "private" / f"identity-before-{len(before)+1}.json", identity)
            before[model] = identity_digest(identity)
            require(before[model] == EXPECTED_DIGESTS[model], "Installed local model differs from the completed-study digest")
        for number, case_id in enumerate(plan["executionOrder"], 1):
            directory = output / "private/cases" / case_id
            metadata_raw = (directory / "metadata.json").read_bytes()
            require(sha(metadata_raw) == plan["requestInventory"][f"private/cases/{case_id}/metadata.json"],
                    "Prepared metadata changed after validation")
            metadata = json.loads(metadata_raw)
            request = (directory / "request.json").read_bytes()
            require(sha(request) == metadata["requestSha256"]
                    == plan["requestInventory"][f"private/cases/{case_id}/request.json"],
                    "Prepared request changed after validation")
            save_json(directory / "dispatch.json", {"dispatchedAtUtc": now(), "executionOrdinal": number,
                                                    "requestSha256": sha(request), "attempt": 1})
            start = time.monotonic()
            result = {"id": case_id}
            try:
                raw = transport.generate(request, timeout=DEADLINE_SECONDS)
                write_new(directory / "response.raw", raw)
                result.update(decode_response(raw, metadata["model"], SETTINGS["num_predict"]))
                result["responseSha256"] = sha(raw)
            except TransportError as error:
                if not (directory / "response.raw").exists():
                    write_new(directory / "response.raw", error.partial)
                result.update(status="transport_failed", complete=False, text=None,
                              errorCode=error.code, error=str(error), responseSha256=sha((directory / "response.raw").read_bytes()))
            result.update(receivedAtUtc=now(), elapsedSeconds=time.monotonic()-start)
            count = result.get("prompt_eval_count")
            result["contextHeadroom"] = ("unknown" if type(count) is not int or count < 0 else
                "insufficient" if count + SETTINGS["num_predict"] + 512 >= SETTINGS["num_ctx"] else "reported-count-fits")
            save_json(directory / "result.json", result)
            results.append(result)
            with (output / "private/progress.jsonl").open("ab") as stream:
                stream.write(json_bytes({k: result[k] for k in ("id", "status", "receivedAtUtc", "elapsedSeconds", "contextHeadroom")}))
                stream.flush()
            print(json.dumps({"completedOpportunities": number, "total": 48, "status": result["status"]}), flush=True)
        for model in MODELS:
            identity = transport.identity(model)
            save_json(output / "private" / f"identity-after-{len(after)+1}.json", identity)
            after[model] = identity_digest(identity)
        packet_sha = make_packet(output, plan, results)
        statuses = dict(Counter(r["status"] for r in results))
        context_counts = dict(Counter(r["contextHeadroom"] for r in results))
        completion = {"status": "complete" if statuses == {"complete": 48} and before == after
                      and context_counts == {"reported-count-fits": 48} else "completed_with_qualifications",
                      "completedAtUtc": now(), "opportunities": 48, "generationCalls": 48, "hiddenRetries": 0,
                      "outcomes": statuses, "contextHeadroom": context_counts,
                      "modelDigestsBefore": before, "modelDigestsAfter": after, "modelDigestsStable": before == after,
                      "blindPacketSha256": packet_sha, "reservoirApplications": 0,
                      "limits": "Reported input-token headroom is not an independent tokenizer/truncation proof. No automatic semantic scoring or NEXT execution inference."}
        save_json(output / "completion.json", completion)
        return completion
    except BaseException as error:
        save_json(output / "incomplete.json", {"recordedAtUtc": now(), "errorType": type(error).__name__,
                                               "error": str(error), "completedOpportunities": len(results),
                                               "policy": "Retain evidence; do not resume this directory or retry an uncertain dispatch."})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    create = subs.add_parser("prepare", help="Freeze exact requests in a new directory; no network")
    create.add_argument("--source", type=Path, required=True)
    create.add_argument("--expected-source-sha256", required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--endpoint", default="http://127.0.0.1:11434")
    create.add_argument("--order-seed", type=int)
    execute = subs.add_parser("run", help="Run the already prepared requests once on loopback Ollama")
    execute.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.source, args.expected_source_sha256, args.output,
                         endpoint=args.endpoint, order_seed=args.order_seed)
    else:
        result = run(args.output)
    public = result if args.command == "prepare" else {
        "status": result["status"], "opportunities": result["opportunities"],
        "outcomes": result["outcomes"], "output": str(args.output.resolve()),
        "modelDigestsStable": result["modelDigestsStable"], "reservoirApplications": 0,
    }
    print(json.dumps(public, ensure_ascii=False))
    return 0 if result["status"] in ("prepared", "complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
