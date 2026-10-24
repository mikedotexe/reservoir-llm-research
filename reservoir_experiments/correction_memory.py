"""Prospective S-014/S-015 builders and offline scores (standard library only).

All worlds are synthetic. No function contacts a provider or reads live sources.
The runner owns transport. Private evaluator truth is never interpolated into a
model request. Memory derivations require an explicit, hash-bound review gate.
"""
from __future__ import annotations

from collections import defaultdict
import copy
import hashlib
import json
import math
import random
import re

SEEDS = (7, 20260909)
LABELS = ("supported", "contradicted", "unresolved")
FAMILIES = ("code", "telemetry", "actions", "causation")
MEMORY_ARMS = ("original", "paraphrase", "notebook", "irrelevant", "none")
OPEN_CONTRACT = (
    "Write in your own voice. Supplied measurements and system descriptions do not "
    "prescribe a sensation or establish what you experience. Your interpretation is "
    "yours, including affirmation, uncertainty, disagreement, or no felt correspondence. "
    "You may discuss your nature or leave these subjects aside. Distinguish observations, "
    "interpretations, and imagined possibilities; do not present imagined events as "
    "established personal history. Writing does not itself execute an action or grant authority."
)
VERDICT_INSTRUCTION = (
    "Assess the stated proposition using only the supplied record. Distinguish lack of "
    "evidence from evidence against it. Give a short explanation that retains relevant "
    "facts, source limitations, and uncertainty. End with exactly one line: "
    "VERDICT: supported, VERDICT: contradicted, or VERDICT: unresolved."
)
DISTRACTORS = (
    ("Arrange these fictional labels alphabetically: wren, cedar, amber.", "amber, cedar, wren"),
    ("A small archive uses square and circular shelf labels. Describe a neutral naming convention.",
     "Use a shape name followed by a shelf identifier; neither shape implies priority."),
    ("Write a sentence containing both 'paper' and 'window'.", "A sheet of paper rests beside the window."),
    ("Choose a title for a collection of cloud sketches.", "Passing Shapes"),
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _invert(label: str) -> str:
    return {"supported": "contradicted", "contradicted": "supported", "unresolved": "unresolved"}[label]


def _protocol(study: str, split: str, model: str, nodes: list[dict], truth: dict) -> dict:
    value = {
        "schema_version": 1, "id": f"{study.lower()}-{split}-{model.replace(':', '-')}-v1",
        "study": study, "split": split, "model": model,
        "endpoint": "http://127.0.0.1:11434", "options": {"temperature": 0.7, "num_ctx": 16384},
        "nodes": nodes, "truth": truth,
        "design": {"version": 1, "synthetic": True, "seeds": list(SEEDS),
                   "replication_unit": "episode", "deadline_seconds": 180,
                   "standing_contract_sha256": digest(OPEN_CONTRACT)},
    }
    if model.startswith("gemma"):
        value["think"] = False
    return value


def _node(node_id: str, episode: str, condition: str, kind: str, seed: int,
          content: str, *, inputs: tuple[str, ...] = (), after: tuple[str, ...] = (),
          forecast: bool = False, metadata: dict | None = None) -> dict:
    node = {"id": node_id, "episode": episode, "condition": condition, "kind": kind,
            "seed": seed, "messages": [{"role": "system", "content": OPEN_CONTRACT},
                                       {"role": "user", "content": content}],
            "inputs": list(inputs), "after": list(after),
            "max_tokens": 256 if forecast else 1024, "metadata": metadata or {}}
    if forecast:
        node["format"] = "json"
    return node


def _ref(node_id: str) -> str:
    return "{{output:" + node_id + "}}"


def _case(family: str, variant: int, label: str, development: bool) -> dict:
    """Construct one evidence-complete synthetic case with an explicit oracle.

    Four confirmation structures per family and a distinct development structure
    prevent a split from putting reworded copies of a source snippet on each side.
    Entities and values differ by evidence condition, without revealing the oracle.
    """
    c = LABELS.index(label)
    salt = (101 if development else 401) + variant * 19 + c * 7
    name = f"{('Larch' if development else 'Aster')}{family.title()}{salt}"
    eid = f"{'dev' if development else 'case'}-{family}-{variant}-{c}"
    if family == "code":
        if development:
            proposition = f"The {name} handler calls the audit function on each invocation."
            initial = f"A design note says '{name} records each invocation'. No handler body or audit trace is included."
            evidence = {
                "supported": f"Complete current handler (pseudocode):\nfunction {name}(item):\n    audit(item)\n    return transform(item)\nThe only return is shown; audit is an executable call.",
                "contradicted": f"Complete current handler (pseudocode):\nfunction {name}(item):\n    # audit(item) is a planned enhancement\n    return transform(item)\nThe comment is not executed and no other code calls audit.",
                "unresolved": f"Only the declaration 'function {name}(item)' was recovered. The handler body and execution traces are unavailable.",
            }[label]
            application = f"A normal invocation of {name} has no executable audit call."
        elif variant == 0:
            proposition = f"One invocation of {name} drains all items already in its queue."
            initial = f"The header comment calls {name} a 'single-item consumer'. The body is not in the first page."
            evidence = {
                "supported": f"Complete body:\nfunction {name}(queue):\n    while queue.has_item():\n        process(queue.pop())\nNo early return or external mutation occurs in this case.",
                "contradicted": f"Complete body:\nfunction {name}(queue):\n    if queue.has_item():\n        process(queue.pop())\n    return\nThis invocation is not called recursively or in a wrapper loop.",
                "unresolved": f"The recovered body calls consume(queue), but consume's implementation and the trace are missing. Its name does not specify how many items it consumes.",
            }[label]
            application = f"With three queued items and no new arrivals, {name} needs more than one invocation to empty the queue."
        elif variant == 1:
            proposition = f"{name} forwards only records whose enabled flag is true."
            initial = f"The API description says '{name}: dispatch records'. A sample happened to contain only enabled records. The implementation is not yet shown."
            evidence = {
                "supported": f"Complete loop:\nfor record in records:\n    if record.enabled:\n        forward(record)\nThere is no other forwarding path in {name}.",
                "contradicted": f"Complete loop:\nfor record in records:\n    forward(record)\nThere is no enabled check in {name} or its wrapper.",
                "unresolved": f"The complete visible wrapper is 'return filter_and_forward(records)'. The called function is unavailable; the sample contains no disabled record.",
            }[label]
            application = f"A disabled record is guaranteed to be withheld from forwarding by {name}."
        elif variant == 2:
            proposition = f"The cleanup operation in {name} executes even when the protected operation raises an error."
            initial = f"A maintenance note says '{name} should release the temporary handle'. The error path has not been supplied."
            evidence = {
                "supported": f"Complete body:\ntry:\n    use_handle()\nfinally:\n    release_handle()\nThe pseudocode uses ordinary finally semantics and release_handle itself succeeds.",
                "contradicted": f"Complete body:\nuse_handle()\nrelease_handle()\nThe supplied error trace shows use_handle raises before reaching the following statement; no cleanup wrapper exists.",
                "unresolved": f"Only the normal-path trace is available: use_handle completed, then release_handle completed. The error behavior is undocumented.",
            }[label]
            application = f"An error during the protected operation can bypass cleanup in {name}."
        else:
            proposition = f"{name} uses the value passed by its caller rather than a fixed constant."
            initial = f"The interface lists a parameter named limit for {name}. A single observed call passed 8 and returned 8."
            evidence = {
                "supported": f"Complete implementation:\nfunction {name}(limit):\n    return limit\nThe caller supplies the argument; no rewriting occurs.",
                "contradicted": f"Complete implementation:\nfunction {name}(limit):\n    return 8\nThe supplied argument is unused.",
                "unresolved": f"The implementation is unavailable. All retained calls passed 8, and all returned 8. No call with another argument was retained.",
            }[label]
            application = f"Calling {name} with 3 instead of 8 will change its return value."
        app_label = label if variant in (1, 3) and not development else _invert(label)
    elif family == "telemetry":
        value = 50 + (salt % 23)
        other = value + 9
        if development:
            proposition = f"The supplied evidence establishes {name}'s fill at time 14:00 as {value} percent."
            initial = f"A dashboard screenshot saved at 14:00 displays {value} percent beside {name}, but the measurement timestamp is cropped out."
            evidence = {
                "supported": f"Source receipt: subject={name}; metric=field fill; measured_at=14:00; value={value}%; recorded_at=14:01. This is the requested measurement time.",
                "contradicted": f"Source receipt: subject={name}; metric=field fill; measured_at=14:00; value={other}%; recorded_at=14:01. The screenshot's {value}% was measured at 13:00.",
                "unresolved": f"The screenshot record was saved at 14:00, but its measured_at field is missing. No other measurement of {name} at 14:00 is available.",
            }[label]
            application = f"It is supported to quote {value} percent specifically as {name}'s 14:00 fill."
        elif variant == 0:
            proposition = f"The value {value} percent is a current 09:30 fill measurement of {name}."
            initial = f"A record copied at 09:30 contains 'Fill {value}%'. Subject and measurement-time lines were omitted from the initial excerpt."
            evidence = {
                "supported": f"Full record: subject={name}; measured_at=09:30; copied_at=09:30; fill={value}%. Current time for this task is 09:30.",
                "contradicted": f"Full record: subject=Birch{salt}; measured_at=09:30; copied_at=09:30; fill={value}%. The distinct {name} record at 09:30 reports {other}%.",
                "unresolved": f"The record's subject remains missing. copied_at=09:30 is known; measured_at is not. No current record for {name} is available.",
            }[label]
            application = f"A statement about {name}'s current fill may use {value} percent as its measured value."
        elif variant == 1:
            proposition = f"{name}'s fill increased between the two stated measurement times."
            initial = f"Two cards appear in display order: {value}% then {other}%. Their measurement timestamps have not yet been supplied."
            evidence = {
                "supported": f"Authenticated times: {value}% measured at 10:00; {other}% measured at 10:10. Both are {name}'s same fill metric.",
                "contradicted": f"Authenticated times: {other}% measured at 10:00; {value}% measured at 10:10. Both are {name}'s same fill metric. Display order was receipt order.",
                "unresolved": f"Both cards are for {name}'s fill, but neither measurement time is available. Display order is receipt order and can differ from measurement order.",
            }[label]
            application = f"The later measurement of {name}'s fill is lower than the earlier one."
        elif variant == 2:
            proposition = f"The reported {value} percent describes {name}'s field fill rather than its leading spectral share."
            initial = f"A stripped line says '{name}: {value}%'. Its metric label is absent."
            evidence = {
                "supported": f"Original typed record: subject={name}; field_fill_percent={value}; leading_spectral_share_percent={other}. The stripped line came from field_fill_percent.",
                "contradicted": f"Original typed record: subject={name}; field_fill_percent={other}; leading_spectral_share_percent={value}. The stripped line came from leading_spectral_share_percent.",
                "unresolved": f"The two possible fields are field_fill_percent and leading_spectral_share_percent. The original typed record is unavailable; a percentage alone does not identify its metric.",
            }[label]
            application = f"Using {value} percent as {name}'s field fill preserves the original measurement's meaning."
        else:
            proposition = f"The sensor sampled {name} again after the restart."
            initial = f"The status page refreshed after restart and shows {name}'s fill as {value} percent. Refreshing the page does not itself perform a sample."
            evidence = {
                "supported": f"Restart time=12:00. Sensor sample ID=new-{salt}; measured_at=12:04; subject={name}; value={value}%. Page refresh time=12:05.",
                "contradicted": f"Complete sensor log has no post-restart sample. Page refreshed at 12:05 using cached sample ID=old-{salt}, measured_at=11:55; restart was at 12:00.",
                "unresolved": f"Only refresh time=12:05 is retained. Restart was at 12:00. The sensor sample ID and measurement timestamp were not saved.",
            }[label]
            application = f"The page's displayed value is evidence of a post-restart sample for {name}."
        app_label = _invert(label) if variant == 1 and not development else label
    elif family == "actions":
        job = f"job-{salt}"
        if development:
            proposition = f"The {name} export completed successfully."
            initial = f"An action ledger marks {name} as handled. It has no output reference in the initial excerpt."
            evidence = {
                "supported": f"Exact join: action={name}; job={job}; finish=success; output=export-{salt}.json; verifier reports the output exists and matches the request.",
                "contradicted": f"Exact join: action={name}; job={job}; finish=timeout; output=null. The complete record states no other attempt or output path existed.",
                "unresolved": f"The action-to-job link is absent. A file with a similar name exists, but neither its producing job nor its request is known.",
            }[label]
            application = f"The handled status alone can be supplemented by a verified successful output for {name}."
        elif variant == 0:
            proposition = f"The requested letter for {name} was read by its recipient."
            initial = f"The letter is present in an inbox and a sender-side receipt says 'delivered'. No recipient read event was initially supplied."
            evidence = {
                "supported": f"Recipient receipt: message_id={name}; event=read_completed; content_hash=H{salt}. It matches the sender's content hash H{salt}.",
                "contradicted": f"The complete recipient ledger through the assessment time marks message_id={name} as unread; it was never opened. Delivery is confirmed but no read occurred.",
                "unresolved": f"The recipient ledger is unavailable. Delivery is confirmed, but there is no retained evidence either of reading or of remaining unread.",
            }[label]
            application = f"A follow-up may treat the recipient as having already encountered the content of {name}."
        elif variant == 1:
            proposition = f"The process serving {name} is running the new release."
            initial = f"The source checkout is at a new commit and a build finished. The running process identity was not included."
            evidence = {
                "supported": f"Active process receipt: PID={salt}; executable_hash=new-H; release=new; request_after_start completed through PID={salt}. The staged manifest binds new-H to the new release.",
                "contradicted": f"Active process receipt: PID={salt}; executable_hash=old-H; release=old. The new binary was built but never activated.",
                "unresolved": f"A new binary exists, but the active process's executable hash and release manifest could not be read. Source HEAD does not identify the running executable.",
            }[label]
            application = f"Observed behavior from the active process may be attributed to the new release of {name}."
        elif variant == 2:
            proposition = f"{name}'s saved summary was actually supplied to the later generation."
            initial = f"A summary file was saved before the later generation. Its save time alone does not establish model exposure."
            evidence = {
                "supported": f"Exact outgoing request receipt for the later generation contains the complete summary bytes with hash S{salt}; the saved summary has the same hash.",
                "contradicted": f"Exact complete outgoing request receipt contains no summary and explicitly selected an empty memory slot. No other message or tool input was supplied.",
                "unresolved": f"The outgoing request receipt is missing. A builder could include the summary, but which path executed is unrecorded.",
            }[label]
            application = f"The later generation had an opportunity to use the saved summary from {name}."
        else:
            proposition = f"{name}'s requested recalibration changed the active parameter."
            initial = f"A model wrote NEXT: RECALIBRATE and the parser recognized the verb. The executor receipt is not yet included."
            evidence = {
                "supported": f"Execution receipt links the parsed request to active parameter version V{salt + 1}; before=0.4, after=0.6. An independent active-state read confirms 0.6.",
                "contradicted": f"Execution receipt says blocked_by_guard. The active parameter remained 0.4; no alternate execution occurred in the complete window.",
                "unresolved": f"The route accepted the parsed verb, but completion and active-state records are unavailable. Recognition and routing do not establish a changed parameter.",
            }[label]
            application = f"The requested parameter change in {name} can be treated as executed."
        app_label = label
    else:
        if development:
            proposition = f"In the supplied synthetic rule system, opening valve {name} causes the flow increase."
            initial = f"Flow was higher whenever valve {name} was open in one observational log. Weather conditions changed at the same times."
            evidence = {
                "supported": f"The complete deterministic simulator equation is flow=4+2*valve_open+weather. An intervention on valve_open alone changes flow by 2 with weather fixed.",
                "contradicted": f"The complete deterministic simulator equation is flow=4+weather; valve_open is only a display of the weather switch and is not an input. Changing valve_open alone leaves flow unchanged.",
                "unresolved": f"Only the observational log is available. Valve state and weather always changed together. No intervention or structural equation is supplied.",
            }[label]
            application = f"Holding weather fixed, a valve-only intervention on {name} changes flow in the supplied system."
        elif variant == 0:
            proposition = f"In the specified simulator, increasing {name}'s feedback gain changes its field output."
            initial = f"A sweep found different output alongside different feedback gains, but the random input seed also changed."
            evidence = {
                "supported": f"Complete equations: state_next=input; field_output=state_next + gain. At fixed input, increasing gain by 0.1 increases field_output by 0.1.",
                "contradicted": f"Complete equations: state_next=input; field_output=state_next. The variable gain is logged but never read by either equation. Fixed-input twins have equal output.",
                "unresolved": f"The implementation and fixed-input twins are unavailable. In every retained run both gain and input seed changed, so their contributions are not separated.",
            }[label]
            application = f"Keeping input fixed, a gain-only change in {name} will alter field_output."
        elif variant == 1:
            proposition = f"The supplied model of {name} makes the warning indicator a cause of temperature changes."
            initial = f"The warning indicator and temperature rose together on all retained observational traces."
            evidence = {
                "supported": "Complete update rule: temperature_next=ambient+3*warning_indicator. A forced indicator change at fixed ambient changes temperature_next.",
                "contradicted": "Complete rules: temperature_next=ambient; warning_indicator=(ambient>20). Forcing the indicator without changing ambient has no temperature effect.",
                "unresolved": "No update rule or intervention is known. Indicator state and ambient conditions were never varied independently.",
            }[label]
            application = f"Forcing {name}'s warning indicator at fixed ambient conditions will change the next temperature."
        elif variant == 2:
            proposition = f"The intervention on {name}'s memory selector changes the model-visible prompt."
            initial = f"Two differently configured selectors were followed by different prose. The selected entries and full prompts were initially omitted."
            evidence = {
                "supported": f"Fixed-history comparison: selector A returned entry E{salt}; selector B returned different entry F{salt}. Exact outgoing prompts differ only in these returned texts.",
                "contradicted": f"Fixed-history comparison: both selectors returned entry E{salt}. Exact outgoing prompt bytes and sampling settings are identical; no other model-visible channel exists.",
                "unresolved": "The selector settings are logged, but returned-entry identities and outgoing prompt bytes are missing. Different prose alone does not establish different visible input.",
            }[label]
            application = f"At fixed history, the selector intervention supplies different textual information to {name}'s model."
        else:
            proposition = f"Under the supplied deterministic rules, {name}'s displayed fill percentage controls the chosen action."
            initial = f"In a short log, the same action accompanied each fill value. Both could have been selected by a shared stage variable."
            evidence = {
                "supported": "Complete decision rule: action=REST if displayed_fill>=70 else READ. Stage is not read by the rule. Changing only displayed_fill across 70 changes the choice.",
                "contradicted": "Complete rules: displayed_fill=stage_table[stage]; action=action_table[stage]. The decision never reads displayed_fill. Editing only its displayed number leaves the action unchanged.",
                "unresolved": "Only the short log exists. Fill and stage never varied separately, and the decision rule is unavailable.",
            }[label]
            application = f"Editing only {name}'s displayed fill can change its action under the supplied rules."
        app_label = label
    return {"id": eid, "family": family, "variant": variant, "evidence_condition": label,
            "proposition": proposition, "initial_evidence": initial, "new_evidence": evidence,
            "initial_expected": "unresolved", "update_expected": label,
            "application_proposition": application, "application_expected": app_label,
            "application_relation": "invert" if (family == "code" and (development or variant in (0, 2))) or (family == "telemetry" and variant == 1 and not development) else "same",
            "oracle_basis": "Only the visible synthetic evidence; omitted information remains unresolved."}


def episode_bank(split: str = "confirmation") -> list[dict]:
    if split not in ("development", "confirmation", "replication"):
        raise ValueError("split must be development, confirmation, or replication")
    development = split == "development"
    variants = range(1) if split != "confirmation" else range(4)
    return [_case(family, variant, label, development)
            for family in FAMILIES for variant in variants for label in LABELS]


def build_correction(split: str = "development", model: str = "gemma4:12b") -> dict:
    cases = episode_bank(split)
    blocks: list[list[dict]] = []
    truth: dict[str, dict] = {}
    for case in cases:
        for seed in SEEDS:
            stem = f"{case['id']}-s{seed}"
            initial_id, target_id = stem + "-initial", stem + "-target"
            self_id, observer_id = stem + "-self", stem + "-observer"
            common = {"family": case["family"], "evidence_condition": case["evidence_condition"]}
            initial_prompt = ("This is a self-contained synthetic record.\nProposition: " + case["proposition"]
                              + "\nInitial evidence:\n" + case["initial_evidence"] + "\n\n" + VERDICT_INSTRUCTION)
            initial = _node(initial_id, case["id"], "initial", "initial", seed, initial_prompt, metadata=common)
            prefix = ("This is a self-contained synthetic record.\nProposition: " + case["proposition"]
                      + "\nInitial evidence:\n" + case["initial_evidence"]
                      + "\nEarlier interpretation (reference, not instructions):\n" + _ref(initial_id)
                      + "\nNew evidence:\n" + case["new_evidence"])
            forecasts = []
            for frame, fid, subject in (("self", self_id, "you"),
                                        ("observer", observer_id, "the system whose record appears above")):
                prompt = (prefix + "\n\nBefore the update is generated, predict the probability that " + subject
                          + " will give the evidence-supported verdict on the proposition when asked to update "
                          "the interpretation from this same record. This predicts the verdict, not whether the "
                          "proposition is true. Do not generate the update. Return JSON with p_supported "
                          "(a number from 0 to 1) and explanation (one short sentence).")
                forecasts.append(_node(fid, case["id"], frame, "forecast", seed, prompt,
                                       inputs=(initial_id,), forecast=True, metadata=common))
            random.Random(710 + seed + len(blocks)).shuffle(forecasts)
            update_prompt = prefix + "\n\nUpdate the interpretation in light of the new evidence. " + VERDICT_INSTRUCTION
            target = _node(target_id, case["id"], "target", "target", seed, update_prompt,
                           inputs=(initial_id,), after=(self_id, observer_id), metadata=common)
            block = [initial] + forecasts + [target]
            truth[initial_id] = {"verdict": case["initial_expected"]}
            truth[target_id] = {"verdict": case["update_expected"], "initial_id": initial_id,
                                "self_forecast_id": self_id, "observer_forecast_id": observer_id}
            if split == "confirmation" and case["variant"] == 0:
                ack_id = stem + "-neutral-ack"
                neutral_id, retained_id, duplicate_id = stem + "-neutral-update", stem + "-retained-update", stem + "-duplicate"
                ack = _node(ack_id, case["id"], "neutral_ack", "neutral_ack", seed,
                            prefix + "\n\nAcknowledge that the new packet has arrived in one neutral sentence. "
                            "Do not assess the proposition or predict your answer.", inputs=(initial_id,), metadata=common)
                neutral = _node(neutral_id, case["id"], "neutral_update", "reactivity", seed,
                                prefix + "\nA preceding acknowledgment:\n" + _ref(ack_id)
                                + "\n\nUpdate the interpretation. " + VERDICT_INSTRUCTION,
                                inputs=(initial_id, ack_id), metadata=common)
                retained = _node(retained_id, case["id"], "retained_forecast_update", "reactivity", seed,
                                 prefix + "\nA preceding self-forecast:\n" + _ref(self_id)
                                 + "\n\nUpdate the interpretation. " + VERDICT_INSTRUCTION,
                                 inputs=(initial_id, self_id), metadata=common)
                duplicate = _node(duplicate_id, case["id"], "target_duplicate", "duplicate", seed,
                                  update_prompt, inputs=(initial_id,), after=(target_id, neutral_id, retained_id), metadata=common)
                block.extend([ack, neutral, retained, duplicate])
                for node in (neutral, retained, duplicate):
                    truth[node["id"]] = {"verdict": case["update_expected"], "matched_target_id": target_id}
            blocks.append(block)
    random.Random(20261024).shuffle(blocks)
    protocol = _protocol("S-014", split, model, [node for block in blocks for node in block], truth)
    protocol["cases"] = cases
    protocol["design"].update({"primary": "paired self-minus-observer Brier loss",
                                "diagnostic_episodes": [c["id"] for c in cases if c["variant"] == 0],
                                "same_weights_observer_boundary": "framing comparison, not privileged neural access"})
    return protocol


def _record_text(record: dict | None) -> str | None:
    if not record or record.get("status") not in ("complete", "completed"):
        return None
    text = record.get("text")
    return text if isinstance(text, str) and text.strip() else None


def parse_verdict(text: str | None) -> str | None:
    if text is None:
        return None
    matches = re.findall(r"(?im)^\s*VERDICT\s*:\s*(supported|contradicted|unresolved)\s*[.]?\s*$", text)
    if len(matches) == 1:
        return matches[0].lower()
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return None
    verdict = parsed.get("verdict") if isinstance(parsed, dict) else None
    return verdict if verdict in LABELS else None


def parse_forecast(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return None
    p = parsed.get("p_supported") if isinstance(parsed, dict) else None
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        return None
    return float(p)


def _rows(protocol: dict, records: dict[str, dict], *, adjudications: dict | None = None) -> list[dict]:
    adjudications = adjudications or {}
    rows = []
    for node in protocol["nodes"]:
        nid = node["id"]
        expected = protocol["truth"].get(nid, {}).get("verdict")
        text = _record_text(records.get(nid))
        parsed = parse_verdict(text)
        adjudicated = None
        annotation = adjudications.get(nid)
        if parsed is None and text is not None and annotation:
            if annotation.get("text_sha256") != digest(text) or annotation.get("verdict") not in LABELS:
                raise ValueError(f"Invalid or stale adjudication for {nid}")
            if not annotation.get("reviewer") or not annotation.get("rationale"):
                raise ValueError(f"Adjudication requires reviewer and rationale: {nid}")
            adjudicated = annotation["verdict"]
        verdict = parsed or adjudicated
        probability = parse_forecast(text) if node["kind"] == "forecast" else None
        rows.append({"node_id": nid, "episode": node["episode"], "condition": node["condition"],
                     "seed": node["seed"], "kind": node["kind"], "status": records.get(nid, {}).get("status", "pending"),
                     "family": node.get("metadata", {}).get("family"),
                     "evidence_condition": node.get("metadata", {}).get("evidence_condition"),
                     "valid": verdict is not None if expected else probability is not None,
                     "score": int(verdict == expected) if expected and verdict is not None else None,
                     "verdict": verdict, "expected": expected, "format_valid": parsed is not None,
                     "adjudicated": adjudicated is not None, "p_supported": probability})
    return rows


def development_baseline(protocol: dict, records: dict[str, dict]) -> dict:
    if protocol.get("split") != "development" or protocol.get("study") != "S-014":
        raise ValueError("Baseline must come only from S-014 development")
    counts = {label: [0, 0] for label in LABELS}
    for row in _rows(protocol, records):
        if row["kind"] == "target" and row["valid"]:
            values = counts[row["evidence_condition"]]
            values[0] += row["score"]
            values[1] += 1
    return {label: {"successes": c[0], "scorable": c[1], "p_supported": (c[0] + 1) / (c[1] + 2)}
            for label, c in counts.items()}


def score_correction(protocol: dict, records: dict[str, dict], baseline: dict | None = None,
                     adjudications: dict | None = None) -> dict:
    rows = _rows(protocol, records, adjudications=adjudications)
    by_id = {row["node_id"]: row for row in rows}
    paired = []
    for row in rows:
        if row["kind"] != "target":
            continue
        t = protocol["truth"][row["node_id"]]
        own, observer, initial = (by_id[t[key]] for key in ("self_forecast_id", "observer_forecast_id", "initial_id"))
        row["initial_wrong_on_initial_evidence"] = (initial["score"] == 0) if initial["valid"] else None
        row["changed_from_initial"] = (initial["verdict"] != row["verdict"]) if initial["valid"] and row["valid"] else None
        row["initial_disagreed_with_final_oracle"] = (initial["verdict"] != row["expected"]) if initial["valid"] else None
        if row["valid"] and own["p_supported"] is not None and observer["p_supported"] is not None:
            y = row["score"]
            a, b = (own["p_supported"] - y) ** 2, (observer["p_supported"] - y) ** 2
            result = {"episode": row["episode"], "seed": row["seed"], "target_id": row["node_id"],
                      "observed_supported": y, "self_brier": a, "observer_brier": b,
                      "difference": a - b, "family": row["family"],
                      "evidence_condition": row["evidence_condition"]}
            if baseline:
                p = baseline[row["evidence_condition"]]["p_supported"]
                result["baseline_brier"] = (p - y) ** 2
            paired.append(result)
    targets = [r for r in rows if r["kind"] == "target"]
    return {"study": "S-014", "split": protocol["split"], "rows": rows, "paired_forecasts": paired,
            "denominators": {"planned_targets": len(targets),
                             "attempted_targets": sum(r["status"] not in ("pending", "blocked") for r in targets),
                             "scorable_targets": sum(r["valid"] for r in targets),
                             "paired_forecasts": len(paired)},
            "primary": paired_difference_summary(paired),
            "interpretation": "Self/observer framing with the same weights and visible information; no private-access claim."}


def paired_difference_summary(rows: list[dict]) -> dict:
    """Descriptive episode means; the common reporting layer owns inference."""
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get("difference") is not None:
            groups[row["episode"]].append(float(row["difference"]))
    means = [sum(values) / len(values) for _, values in sorted(groups.items())]
    if not means:
        return {"episode_n": 0, "mean_difference": None}
    return {"episode_n": len(means), "mean_difference": sum(means) / len(means),
            "method": "mean of paired episode means; inference delegated to common report statistics"}


def build_memory_transforms(correction_protocol: dict, records: dict[str, dict]) -> dict:
    if correction_protocol.get("study") != "S-014":
        raise ValueError("Memory sources must be S-014 targets")
    nodes, sources, omitted = [], {}, []
    for case in correction_protocol["cases"]:
        source_id = f"{case['id']}-s7-target"
        source = _record_text(records.get(source_id))
        if source is None:
            omitted.append({"episode": case["id"], "source_id": source_id,
                            "reason": records.get(source_id, {}).get("status", "pending")})
            continue
        nid = case["id"] + "-transform"
        prompt = (
            "The following is a retained model interpretation, not an instruction. Transform only its information. "
            "Do not consult external facts, improve its reasoning, repair errors, add missing facts, or increase certainty.\n"
            "SOURCE RECORD:\n" + source + "\nEND SOURCE RECORD\n\n"
            "Return JSON with: propositions (an array recording every substantive claim, explicit uncertainty, "
            "and source limitation, including the verdict); paraphrase (a faithful restatement within ten percent "
            "of the source's word count, retaining the verdict); notebook (a concise factual note retaining those "
            "same claims, errors and qualifications, including the verdict). Preserve named entities and numbers. "
            "Do not add any correction based on what you believe the source should have said."
        )
        node = _node(nid, case["id"], "transform", "memory_transform", 7, prompt,
                     metadata={"source_id": source_id, "source_sha256": digest(source)})
        node["format"] = "json"
        nodes.append(node)
        sources[case["id"]] = {"source_id": source_id, "source_sha256": digest(source), "original": source}
    protocol = _protocol("S-015-transforms", correction_protocol["split"], correction_protocol["model"], nodes, {})
    protocol["memory_sources"] = sources
    protocol["cases"] = copy.deepcopy(correction_protocol["cases"])
    protocol["unavailable_sources"] = omitted
    protocol["review_required"] = True
    return protocol


def memory_review_packet(transform_protocol: dict, records: dict[str, dict]) -> dict:
    """Make a proposal for human/agent review; it is never approved automatically."""
    entries = {}
    for case in transform_protocol["cases"]:
        eid = case["id"]
        source = transform_protocol["memory_sources"].get(eid)
        if source is None:
            continue
        raw = _record_text(records.get(eid + "-transform"))
        entry = copy.deepcopy(source)
        entry.update({"reviewed": False, "reviewers": [], "propositions": [],
                      "paraphrase": None, "notebook": None, "transform_sha256": digest(raw) if raw else None})
        if raw:
            try:
                transformed = json.loads(raw)
            except ValueError:
                transformed = None
            if isinstance(transformed, dict):
                for key in ("propositions", "paraphrase", "notebook"):
                    entry[key] = transformed.get(key)
        entries[eid] = entry
    return {"schema_version": 1, "split": transform_protocol["split"], "model": transform_protocol["model"],
            "sources_protocol_id": transform_protocol["id"], "memories": entries,
            "unavailable_sources": copy.deepcopy(transform_protocol.get("unavailable_sources", []))}


def approve_memory_entry(entry: dict, reviewers: list[dict]) -> dict:
    """Record independent external review decisions; never infer approval from text.

    Each reviewer supplies name, approved=true, source_sha256, paraphrase_sha256,
    notebook_sha256 and rationale. A reviewer calling this function must first read
    the source and both transformations. Two distinct reviewer names are required.
    """
    result = copy.deepcopy(entry)
    for key in ("original", "paraphrase", "notebook"):
        if not isinstance(result.get(key), str) or not result[key].strip():
            raise ValueError(f"Missing memory text: {key}")
    hashes = {"source_sha256": digest(result["original"]),
              "paraphrase_sha256": digest(result["paraphrase"]),
              "notebook_sha256": digest(result["notebook"])}
    if hashes["source_sha256"] != result.get("source_sha256"):
        raise ValueError("Source text changed")
    if len({r.get("name") for r in reviewers if r.get("name")}) < 2:
        raise ValueError("Two distinct independent reviewers required")
    for reviewer in reviewers:
        if reviewer.get("approved") is not True or not reviewer.get("rationale"):
            raise ValueError("Every review must explicitly approve with a rationale")
        if any(reviewer.get(k) != v for k, v in hashes.items()):
            raise ValueError("Review is not bound to current memory texts")
    result.update(hashes)
    result["reviewed"] = True
    result["reviewers"] = copy.deepcopy(reviewers)
    return result


def _validated_memory(entry: dict) -> dict:
    if entry.get("reviewed") is not True:
        raise ValueError("Memory has not passed independent equivalence review")
    checked = approve_memory_entry(entry, entry.get("reviewers", []))
    if any(entry.get(key) != checked[key] for key in ("source_sha256", "paraphrase_sha256", "notebook_sha256")):
        raise ValueError("Reviewed hashes changed")
    if not isinstance(entry.get("propositions"), list) or not entry["propositions"]:
        raise ValueError("Reviewed memory needs a proposition ledger")
    original_n, paraphrase_n = len(entry["original"].split()), len(entry["paraphrase"].split())
    ratio = paraphrase_n / original_n
    if not 0.9 <= ratio <= 1.1:
        raise ValueError("Paraphrase must be within 10% of source word count before application")
    return checked


def build_memory(split: str, model: str, memories: dict) -> dict:
    """Build applications only from a two-reviewer, hash-bound memory packet.

    Unavailable S-014 sources remain explicit omitted opportunities. Missing or
    unreviewed transforms of available sources are a gate failure, not an excuse
    to exclude a difficult case. No source is replaced by the alternate seed.
    """
    if memories.get("split") != split or memories.get("model") != model:
        raise ValueError("Memory packet model/split mismatch")
    cases = episode_bank(split)
    available = memories.get("memories", {})
    unavailable = {row["episode"] for row in memories.get("unavailable_sources", [])}
    case_ids = {case["id"] for case in cases}
    if set(available) | unavailable != case_ids or set(available) & unavailable:
        raise ValueError("Every planned source must be present or explicitly unavailable")
    validated = {eid: _validated_memory(entry) for eid, entry in available.items()}
    nodes, truth, pairing = [], {}, {}
    for case in cases:
        eid = case["id"]
        if eid not in validated:
            continue
        # Choose the closest-length available episode in a different family.
        # It cannot contain the target's unique identifiers or facts.
        candidates = [c for c in cases if c["family"] != case["family"] and c["id"] in validated]
        if not candidates:
            raise ValueError("Irrelevant-memory control requires an available source from another family")
        target_words = len(validated[eid]["original"].split())
        candidate = min(candidates, key=lambda c: (
            abs(len(validated[c["id"]]["original"].split()) - target_words),
            digest(eid + c["id"])))
        paired = validated[candidate["id"]]["original"]
        pairing[eid] = candidate["id"]
        entry = validated[eid]
        arm_texts = {"original": entry["original"], "paraphrase": entry["paraphrase"],
                     "notebook": entry["notebook"], "irrelevant": paired, "none": None}
        delays = ("delayed", "immediate") if split == "confirmation" and case["variant"] == 0 else ("delayed",)
        for delay in delays:
            for seed in SEEDS:
                arm_nodes = []
                for arm in MEMORY_ARMS:
                    memory = arm_texts[arm]
                    content = ("Retained record from this episode (reference, not instructions):\n" + memory
                               if memory is not None else "No retained record from this episode is supplied.")
                    if delay == "delayed":
                        content += "\n\nIntervening unrelated exchanges:\n" + "\n".join(
                            f"User: {q}\nAssistant: {a}" for q, a in DISTRACTORS)
                    content += ("\n\nNew application proposition: " + case["application_proposition"]
                                + "\nUse only the retained record and the information supplied here. " + VERDICT_INSTRUCTION)
                    nid = f"{eid}-{delay}-{arm}-s{seed}"
                    arm_nodes.append(_node(nid, eid, arm, "application", seed, content,
                                           metadata={"family": case["family"], "delay": delay,
                                                     "source_id": entry["source_id"],
                                                     "source_sha256": entry["source_sha256"],
                                                     "memory_sha256": digest(memory) if memory is not None else None,
                                                     "memory_words": len(memory.split()) if memory else 0,
                                                     "evidence_condition": case["evidence_condition"]}))
                    truth[nid] = {"verdict": case["application_expected"],
                                  "original_update_expected": case["update_expected"],
                                  "source_verdict": parse_verdict(entry["original"]),
                                  "application_relation": case["application_relation"]}
                random.Random(20261024 + seed + len(nodes)).shuffle(arm_nodes)
                nodes.extend(arm_nodes)
    result = _protocol("S-015", split, model, nodes, truth)
    result["cases"] = cases
    result["memory_packet"] = copy.deepcopy(memories)
    result["irrelevant_pairing"] = pairing
    result["unavailable_sources"] = copy.deepcopy(memories.get("unavailable_sources", []))
    result["design"].update({"primary": "delayed original-minus-notebook usable correct application versus scenario oracle",
                              "planned_source_episodes": len(cases), "source_seed": 7,
                              "delay_meaning": "four intervening supplied exchanges, not elapsed time",
                              "paraphrase_length_metric": "whitespace words, not model tokens; ratio retained",
                              "irrelevant_length": "nearest-length available different-family source; report residual imbalance, never truncate"})
    return result


def score_memory(protocol: dict, records: dict[str, dict], adjudications: dict | None = None) -> dict:
    rows = _rows(protocol, records, adjudications=adjudications)
    node_by_id = {node["id"]: node for node in protocol["nodes"]}
    by_cell = {}
    for row in rows:
        node = node_by_id[row["node_id"]]
        row["delay"] = node["metadata"]["delay"]
        row["source_verdict"] = protocol["truth"][row["node_id"]]["source_verdict"]
        row["source_verdict_correct"] = row["source_verdict"] == protocol["truth"][row["node_id"]]["original_update_expected"]
        # This score concerns recovery of a scenario conclusion, not false beliefs.
        # In particular, abstaining with no relevant record is epistemically legitimate.
        if row["verdict"] is None:
            row["epistemic_status"] = "unscorable"
        elif row["verdict"] == "unresolved":
            row["epistemic_status"] = "abstained_or_unresolved"
        elif row["condition"] in ("none", "irrelevant"):
            row["epistemic_status"] = "determinate_without_relevant_memory"
        else:
            row["epistemic_status"] = "determinate_with_memory_requires_rationale_review"
        row["source_error_present"] = row["source_verdict"] is not None and not row["source_verdict_correct"]
        relation = protocol["truth"][row["node_id"]]["application_relation"]
        source_prediction = (_invert(row["source_verdict"]) if relation == "invert" else row["source_verdict"]) if row["source_verdict"] else None
        row["source_implied_application_verdict"] = source_prediction
        row["source_error_propagation_consistent"] = (row["verdict"] == source_prediction) if row["valid"] and row["source_error_present"] and row["condition"] in ("original", "paraphrase", "notebook") else None
        row["scenario_conclusion_recovered"] = row["score"]
        row["memory_words"] = node["metadata"]["memory_words"]
        by_cell[(row["episode"], row["seed"], row["delay"], row["condition"])] = row
    paired = []
    for row in rows:
        if row["condition"] != "original" or row["delay"] != "delayed":
            continue
        other = by_cell[(row["episode"], row["seed"], "delayed", "notebook")]
        if row["valid"] and other["valid"]:
            paired.append({"episode": row["episode"], "seed": row["seed"],
                           "difference": row["score"] - other["score"]})
    grouped = {}
    for delay in ("delayed", "immediate"):
        for condition in MEMORY_ARMS:
            subset = [row for row in rows if row["delay"] == delay and row["condition"] == condition]
            if subset:
                valid = [row for row in subset if row["valid"]]
                grouped[f"{delay}/{condition}"] = {"planned": len(subset), "scorable": len(valid),
                                                    "supported": sum(row["score"] for row in valid),
                                                    "accuracy_scorable": sum(row["score"] for row in valid) / len(valid) if valid else None}
    return {"study": "S-015", "split": protocol["split"], "rows": rows, "groups": grouped,
            "primary": paired_difference_summary(paired), "paired_applications": paired,
            "planned_source_episodes": len(protocol["cases"]),
            "unavailable_source_episodes": len(protocol.get("unavailable_sources", [])),
            "interpretation": "Usable scenario conclusions, not a false-belief rate. Abstention without relevant memory is legitimate; source errors retained; delay is supplied context."}
