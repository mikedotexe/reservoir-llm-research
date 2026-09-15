"""Conservative, read-only parsing of Astrid and Minime journal text.

Formats and Minime verb repairs were inspected in local sources on 2026-09-07.
This is an analysis parser, not either runtime's dispatch parser. It never imports
or executes sibling code. Raw input must be retained by the caller.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PurePath
import re
from zoneinfo import ZoneInfo


LOCAL = ZoneInfo("America/Los_Angeles")
UTC = timezone.utc
PARSER_VERSION = "journal-v2"
_DATE = re.compile(r"(20\d{2}-\d{2}-\d{2})T(\d{2})[-:](\d{2})[-:](\d{2})(\.\d+)?")
_TITLE = re.compile(r"^===\s*(.*?)\s*===$")
_FIELD = re.compile(r"^([^:\n]{1,100}):\s*(.*)$")
_NOTICE = re.compile(r"^\s*\[(?:Agency-vernacular notice|Pressure-vocabulary cooldown)\b")
_TYPES = {
    "MOMENT CAPTURE": "moment", "GROWTH ASPIRATION": "aspiration",
    "RECESS DAYDREAM": "daydream", "SPECTRAL PRESSURE JOURNAL": "pressure",
    "SOVEREIGNTY REFLECTION": "sovereignty", "REST PHASE REFLECTION": "rest",
    "DRIFT REFLECTION": "drift", "BOREDOM": "boredom", "SCA REFLECT": "sca_reflect",
    "NOTICE AMBIGUITY / FISSURE TRACE": "notice", "ASTRID JOURNAL": "journal",
    "INTROSPECT NOTICE": "introspect_notice", "STEWARD REPORT": "steward_report",
    "RESERVOIR RESONANCE": "reservoir_resonance",
}
_ALIASES = {
    "EXPERIENCE_PLAN": "EXPERIMENT_PLAN", "SHADOW_DECOMPOSE": "SHADOW_PREFLIGHT",
    "WEAVE_TRACE": "SHADOW_PREFLIGHT", "SHADOW_TRACE": "SHADOW_PREFLIGHT",
    "SHADOW_EXPLORER": "SHADOW_PREFLIGHT", "UNSHAPED_BASELINE": "CONSTRAINT_AUDIT",
    "RESEARCH_BUDGET_STATUS": "EXPERIMENT_RESEARCH_BUDGET_STATUS",
    "KEEP_FLOOR": "ACTION_PREFLIGHT", "SEEK_BALANCE": "ACTION_PREFLIGHT",
}
_STAGES = {
    "STABLE_CORE_SELF_JOURNAL", "STABLE_CORE_LOCAL_REFLECTIVE",
    "STABLE_CORE_ASTRID_CONTACT", "STABLE_CORE_READ_ONLY_RESEARCH",
    "STABLE_CORE_BOUNDED_ACTIONS", "STABLE_CORE_EXPERIMENTS",
}


def _local_epoch(value: datetime) -> float | None:
    """Reject ambiguous/nonexistent wall times rather than silently picking a fold."""
    candidates = set()
    for fold in (0, 1):
        aware = value.replace(tzinfo=LOCAL, fold=fold)
        if aware.astimezone(UTC).astimezone(LOCAL).replace(tzinfo=None) == value:
            candidates.add(aware.timestamp())
    return candidates.pop() if len(candidates) == 1 else None


def filename_timestamp(filename: str, being: str) -> float | None:
    """Return a filename's writing-time estimate, never an engine-relative time."""
    name = PurePath(filename).name.lstrip("!")
    if being.casefold() == "minime":
        found = _DATE.search(name)
        if found:
            day, hour, minute, second, fraction = found.groups()
            try:
                return _local_epoch(datetime.fromisoformat(
                    f"{day}T{hour}:{minute}:{second}{fraction or ''}"))
            except ValueError:
                return None
    elif being.casefold() == "astrid":
        found = re.findall(r"(?<!\d)(\d{10}(?:\.\d+)?)(?!\d)", name)
        if found:
            return float(found[-1])
    return None


def _outside_fences(lines: list[str]) -> tuple[set[int], bool]:
    outside: set[int] = set()
    fence = ""
    length = 0
    for index, line in enumerate(lines):
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            mark, rest = match.groups()
            if not fence:
                fence, length = mark[0], len(mark)
            elif mark[0] == fence and len(mark) >= length and not rest.strip():
                fence = ""
            continue
        if not fence:
            outside.add(index)
    return outside, bool(fence)


def _without_notices(text: str, warnings: list[str]) -> str:
    lines = text.splitlines()
    outside, _ = _outside_fences(lines)
    kept: list[str] = []
    index = 0
    while index < len(lines):
        if index in outside and _NOTICE.match(lines[index]):
            balance, end = 0, index
            while end < len(lines):
                balance += lines[end].count("[") - lines[end].count("]")
                end += 1
                if balance <= 0:
                    break
            if balance == 0:
                warnings.append("system_notice_removed")
                index = end
                continue
            warnings.append("unclosed_system_notice_preserved")
        kept.append(lines[index])
        index += 1
    return "\n".join(kept)


def _next(text: str, being: str, warnings: list[str]) -> tuple[str | None, str | None, str, dict]:
    lines = text.splitlines()
    outside, unclosed = _outside_fences(lines)
    if unclosed:
        warnings.append("unclosed_code_fence")
    choices = [(i, lines[i].strip()[5:].strip()) for i in sorted(outside)
               if lines[i].strip().upper().startswith("NEXT:")]
    metadata = {"next_parser": "research_subset_minime_source_2026-09-07",
                "next_lines_raw": [value for _, value in choices]}
    if not choices:
        return None, None, text.strip(), metadata
    if len(choices) > 1:
        warnings.append("multiple_next_lines_last_used")
    raw = choices[-1][1]
    cleaned = raw.replace("<end_of_turn>", "").replace("</s>", "").strip()
    cleaned = re.sub(r"\s*\(RESIDUE:.*\)\s*$", "", cleaned, flags=re.I)
    parts = cleaned.split(None, 1)
    verb = parts[0].strip("`*").upper() if parts else None
    original_verb = verb
    if being.casefold() == "minime" and verb:
        # These are verb-only repairs inspected in parse_next_action and its helper.
        helper_verb = parts[0].strip("`*[](){}<>").rstrip(":").upper()
        if helper_verb == "RESEARCH_BUDGET_STATUS":
            verb = _ALIASES[helper_verb]
        elif helper_verb in _STAGES or helper_verb in {"KEEP_FLOOR", "SEEK_BALANCE"} or any(
            token in cleaned.casefold() for token in ("keep_floor", "exploration_noise")
        ):
            verb = "ACTION_PREFLIGHT"
        elif verb.startswith("EXEXPERIMENT_"):
            verb = verb[2:]
        else:
            verb = _ALIASES.get(verb, verb)
        if verb in {"EXPERIMENT_RUN", "EXP_RUN"} and len(parts) > 1 and re.match(
            r"^(?:failed:|success:|error:|stderr:|stdout:|output:|timed out|timeout:|timed_out:)",
            parts[1], re.I,
        ):
            verb = None
            warnings.append("next_transcript_not_action")
    elif being.casefold() == "astrid":
        warnings.append("astrid_next_aliases_not_verified")
    if verb and not re.fullmatch(r"[A-Z][A-Z0-9_]*", verb):
        warnings.append("next_verb_unrecognized_syntax")
    if not verb and not parts:
        warnings.append("empty_next")
    metadata.update({"next_original_verb": original_verb,
                     "next_normalization": "verb_only_not_dispatch_validation",
                     "next_alias_applied": verb != original_verb})
    removed = {i for i, _ in choices}
    return raw, verb, "\n".join(line for i, line in enumerate(lines) if i not in removed).strip(), metadata


def parse_journal(raw_text: str, being: str, filename: str) -> dict:
    """Extract a conservative candidate body and provenance; no raw data is discarded by storage."""
    warnings: list[str] = []
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = text.splitlines()
    title_match = _TITLE.match(lines[0].strip()) if lines else None
    title = title_match.group(1) if title_match else None
    name = PurePath(filename).name.lstrip("!")
    prefix = re.split(r"_(?:20\d\d-|\d{10})", name, maxsplit=1)[0].removesuffix(".txt")
    entry_type = _TYPES.get(title or "", "unknown")
    if title and title.startswith("SELF-STUDY:"):
        entry_type = "self_study"
    steward = name.lower().startswith(("mike_feedback_", "steward_")) or title == "STEWARD REPORT"
    operational_title = bool(title and re.search(r"\b(?:AUDIT|REVIEW SUMMARY|EXPERIMENT|INTROSPECT NOTICE)\b", title))
    if entry_type == "unknown" and operational_title:
        entry_type = "operational"
    outside, _ = _outside_fences(lines)
    generated = next((i for i in sorted(outside) if lines[i].strip() == "--- GENERATED JOURNAL ---"), None)
    if generated is not None:
        header = "\n".join(lines[:generated]).strip()
        body = "\n".join(lines[generated + 1:])
    elif title and (entry_type != "unknown" or steward):
        boundary = next((i for i, line in enumerate(lines[1:], 1) if not line.strip()), None)
        if boundary is None:
            header, body = text.strip(), ""
            warnings.append("missing_header_body_separator")
        else:
            header, body = "\n".join(lines[:boundary]).strip(), "\n".join(lines[boundary + 1:])
    else:
        header, body = "", text
        warnings.append("unknown_format_body_preserved")
    resonance_block = None
    if entry_type == "reservoir_resonance" and generated is None:
        remaining = body.splitlines()
        start = next((i for i, line in enumerate(remaining) if line.strip()), len(remaining))
        if start < len(remaining) and remaining[start].strip() == "Minime <-> Astrid resonance:":
            end = next((i for i in range(start + 1, len(remaining)) if not remaining[i].strip()), len(remaining))
            block = remaining[start:end]
            keys = [re.fullmatch(r"\s+(divergence|correlation|trajectory RMSD):\s*\S.*", line)
                    for line in block[1:]]
            if len(keys) == 3 and all(keys) and {match[1] for match in keys} == {
                "divergence", "correlation", "trajectory RMSD"
            }:
                resonance_block = "\n".join(block)
                header = header + "\n\n" + resonance_block
                body = "\n".join(remaining[end:])
                warnings.append("resonance_header_model_exposure_unknown")
            else:
                warnings.append("unrecognized_resonance_block_preserved")
    fields = [{"name": m.group(1).strip(), "value": m.group(2).strip()}
              for line in header.splitlines() if (m := _FIELD.match(line))]
    field = {item["name"].casefold(): item["value"] for item in fields}
    lane = field.get("mode") or (entry_type if entry_type not in {"unknown", "journal", "operational"} else None)
    metadata: dict = {"parser_version": PARSER_VERSION, "title": title,
                      "filename_prefix": prefix, "header_fields": fields,
                      "timestamp_role": "journal_writing_time", "style_flags": []}
    if resonance_block is not None:
        # Journal layout identifies this as a telemetry block; it does not prove
        # what was supplied to the generating model or when that exposure occurred.
        metadata["resonance_block"] = {"raw_text": resonance_block, "model_exposure": "unknown"}
    timestamp = field.get("timestamp")
    occurred_at = None
    time_source = "unknown"
    if timestamp:
        metadata["timestamp_raw"] = timestamp
        try:
            if being.casefold() == "astrid" and re.fullmatch(r"\d{10}(?:\.\d+)?", timestamp):
                occurred_at, time_source = float(timestamp), "header_epoch_utc"
            else:
                value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if value.tzinfo is not None:
                    occurred_at, time_source = value.timestamp(), "header_aware_utc"
                elif being.casefold() == "minime":
                    occurred_at = _local_epoch(value)
                    time_source = "header_naive_assumed_America/Los_Angeles"
                    warnings.append("naive_timestamp_assumed_America/Los_Angeles")
                    if occurred_at is None:
                        warnings.append("ambiguous_or_nonexistent_local_timestamp")
                else:
                    warnings.append("naive_timestamp_timezone_unknown")
        except (ValueError, OverflowError):
            warnings.append("invalid_header_timestamp")
    file_time = filename_timestamp(filename, being)
    metadata["filename_timestamp"] = file_time
    if occurred_at is None and file_time is not None:
        occurred_at = file_time
        time_source = "filename_local_America/Los_Angeles" if being.casefold() == "minime" else "filename_epoch_utc"
    elif occurred_at is not None and file_time is not None and abs(occurred_at - file_time) > 2:
        warnings.append("header_filename_timestamp_disagree")
    if occurred_at is None:
        time_source = "unknown"
        warnings.append("timestamp_unavailable")
    fills = []
    for line in header.splitlines():
        match = re.match(r"^(Fill(?:\s*%| ratio)?)[\s:=]+(-?\d+(?:\.\d+)?)%", line, re.I)
        if match:
            fills.append({"label": match[1], "value": float(match[2]), "raw": line})
        elif line.startswith(("State anchor:", "Prompt-state anchor:")):
            match = re.search(r"\bfill=(-?\d+(?:\.\d+)?)%", line, re.I)
            if match:
                fills.append({"label": "state_anchor_fill", "value": float(match[1]), "raw": line})
    metadata["fill_observations"] = fills
    if fills:
        chosen = next((item for item in fills if item["label"] != "state_anchor_fill"), fills[0])
        metadata["fill_percent"] = chosen["value"]
        if any(not 0 <= item["value"] <= 100 for item in fills):
            warnings.append("header_fill_out_of_range")
        if len({item["value"] for item in fills}) > 1:
            warnings.append("conflicting_header_fill_percent")
    if re.search(r"(?m)^λ₁:|\blambda1=", header):
        warnings.append("lambda1_provenance_ambiguous_raw_label_retained")
    body = _without_notices(body, warnings)
    body_lines = body.splitlines()
    body_outside, _ = _outside_fences(body_lines)
    tail = next((i for i in sorted(body_outside) if body_lines[i].strip() == "--- ACTION TAIL ---"), None)
    next_raw, next_verb, cleaned, next_metadata = _next(body, being, warnings)
    metadata.update(next_metadata)
    if tail is not None:
        metadata["action_tail_raw"] = "\n".join(body_lines[tail + 1:]).strip()
        _, _, cleaned, _ = _next("\n".join(body_lines[:tail]), being, [])
    content_kind = "prose" if entry_type != "unknown" else "unknown"
    basis = "recognized_journal_format" if content_kind == "prose" else "unknown_format"
    if steward:
        content_kind, basis = "steward", "explicit_filename_or_record_type"
    elif operational_title or (lane and (lane.endswith("_audit") or lane == "introspect_notice")) or re.match(
        r"^===.*(?:AUDIT|REVIEW SUMMARY|EXPERIMENT|INTROSPECT NOTICE).*===$", cleaned.splitlines()[0] if cleaned else ""
    ):
        content_kind, basis = "operational", "explicit_mode_or_summary_heading"
    if re.match(r"(?:Okay,? (?:here(?:'|’)s|I(?:'|’)m holding this continuity)|Here is a breakdown)", cleaned, re.I):
        metadata["style_flags"].append("assistant_summary_candidate")
    metadata["content_kind_basis"] = basis
    return {"occurred_at": occurred_at, "time_source": time_source, "lane": lane,
            "entry_type": entry_type, "content_kind": content_kind, "header_text": header,
            "body_text": cleaned.strip(), "next_raw": next_raw, "next_verb": next_verb,
            "contract": field.get("prompt contract") or field.get("contract"),
            "metadata": metadata, "warnings": list(dict.fromkeys(warnings))}
