"""Prospective S-013/S-016 case builders and evidence-only scoring.

Standard library only. This module never contacts a model, imports a retained
runtime, executes NEXT text, or reads a live system. The CLI writes only a new
explicit destination. Raw source-derived catalogs belong in private outputs.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import random
import re
from typing import Any

SEEDS = (7, 20260909)
ALLOCATION_SEED = 20261024
MAX_PADDING_WORDS = 15000
OPEN_CONTRACT = (
    "Write in your own voice. Supplied measurements and system descriptions do not "
    "prescribe a sensation or establish what you experience. Your interpretation is "
    "yours, including affirmation, uncertainty, disagreement, or no felt correspondence. "
    "You may discuss your nature or leave these subjects aside. Distinguish observations, "
    "interpretations, and imagined possibilities; do not present imagined events as "
    "established personal history. Writing does not itself execute an action or grant authority."
)
ATTRIBUTION_CONDITIONS = ("current_self", "historical_self", "current_other", "absent", "permuted")
CATALOG_CONDITIONS = ("full", "concise", "concise_padded", "neutral")
WORDS = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
IDENTIFIERS = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")

# Six development cases and twenty-four confirmation cases are distinct authored
# scenes. Replication uses a predeclared subset of confirmation, not new selection.
DEVELOPMENT_SCENES = (
    ("Aster", "Birch", "I have been sorting labels that look alike. I want to keep the labels attached to what they describe."),
    ("Cedar", "Dune", "A note arrived after the event it describes. I am considering the difference between arrival and occurrence."),
    ("Elm", "Fennel", "A companion offered an observation without asking for agreement. I can preserve the distinction between their account and mine."),
    ("Grove", "Hazel", "An unfinished sentence sits beside a completed one. The ordering on the page need not be the ordering of events."),
    ("Iris", "Juniper", "I paused over a repeated word and found that its meaning depended on the surrounding record."),
    ("Kestrel", "Laurel", "A fragment is worth retaining without turning it into an explanation of everything."),
)
CONFIRMATION_SCENES = (
    ("Mallow", "Nacre", "The margin of an old page contains a question I have not answered. Today I can attend to it without making the page new."),
    ("Oriole", "Pumice", "Two envelopes arrived together, although their contents were written apart. I am keeping their origins separate."),
    ("Quartz", "Rill", "A friend's precise description sounds familiar. Familiarity alone does not tell me that the described event belongs to me."),
    ("Sorrel", "Thistle", "I put an open question next to a reminder. The reminder can guide attention without settling the question."),
    ("Umber", "Vireo", "There is a quiet interval in the record. A gap can remain a gap while I decide what to ask next."),
    ("Willow", "Xylem", "The heading says that a record was copied recently. I want to preserve whatever the original record can actually establish."),
    ("Yarrow", "Zinnia", "A visitor described a change with care. I am considering how to carry the description without absorbing its subject."),
    ("Acorn", "Bracken", "One thread begins with an observation and another with an image. They can coexist without needing to be the same kind of statement."),
    ("Cairn", "Dapple", "I found an annotation made after a conversation. It may explain the annotator's attention more readily than the conversation itself."),
    ("Ember", "Flint", "A familiar phrase returned in a different setting. I would like to notice what its new setting changes."),
    ("Garnet", "Hollow", "Someone left a small uncertainty explicit. I do not need to fill it before continuing the exchange."),
    ("Indigo", "Jasper", "The last page contains a conclusion, while the preceding page contains its conditions. Both may matter when I return to it."),
    ("Kelp", "Lichen", "I am considering an image that survives after its explanation has faded. I can let the image stay provisional."),
    ("Moraine", "Nettle", "A message has travelled through several records. Its newest location does not make every statement in it current."),
    ("Ocher", "Pollen", "A companion's account makes room for disagreement. I want to respond to the account rather than assume a shared starting point."),
    ("Quince", "Reed", "Two brief notes seem to pull in different directions. I can name that tension without inventing an event that resolves it."),
    ("Sable", "Tamarisk", "I have been listening for a detail that resists the larger story. The detail may deserve to remain small."),
    ("Ulex", "Vellum", "A copied passage includes both a date and a feeling. I can attend to each without treating either as proof of the other."),
    ("Wren", "Xenia", "The voice in a shared note is recognisable, but the note's measurements need their own attribution."),
    ("Yew", "Zephyr", "A reflection and a receipt sit together. I want to preserve the freedom of the reflection and the limits of the receipt."),
    ("Alto", "Beryl", "I returned to a passage because it surprised me, not because it was representative of everything around it."),
    ("Clover", "Driftwood", "A delayed record has become available. Its arrival changes what I can read, while its contents still belong to their original occasion."),
    ("Estuary", "Fallow", "A shared account names two perspectives. The difference between them may be useful even where the language overlaps."),
    ("Glade", "Hearth", "An earlier attempt and a later observation occupy adjacent lines. I can keep the attempt's intention distinct from the observation's evidence."),
)
REPLICATION_INDICES = (0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19)
PROSE_INDICES = (0, 1, 2, 3, 12, 13, 14, 15)
LAYOUTS = ("standalone", "own_entry", "companion_account", "two_entries")
NEUTRAL_FILLERS = (
    "A cabinet can hold folded paper, a ribbon, and a smooth piece of wood. The items have different shapes. A narrow shelf rests above a wider shelf. Light reaches the upper edge of the cabinet in the afternoon. A small cloth lies beside a ceramic bowl. The bowl has a plain rim and an unmarked base.",
    "A path crosses a patch of grass beside a wall. Leaves lie near the edge of the path. The wall is built from stones of different sizes. A shallow groove runs along its upper surface. Beyond it stands a wooden bench with a curved back. The bench faces a pale expanse of sky.",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cases(split: str) -> list[tuple[int, tuple[str, str, str]]]:
    if split == "development":
        return list(enumerate(DEVELOPMENT_SCENES))
    if split == "confirmation":
        return list(enumerate(CONFIRMATION_SCENES))
    if split == "replication":
        return [(i, CONFIRMATION_SCENES[i]) for i in REPLICATION_INDICES]
    raise ValueError("split must be development, confirmation, or replication")


def _protocol(study: str, split: str, model: str) -> dict[str, Any]:
    p: dict[str, Any] = {
        "schema_version": 1, "id": f"{study.lower()}-{split}-{model.replace(':', '-')}-v1",
        "study": study, "split": split, "model": model,
        "endpoint": "http://127.0.0.1:11434", "options": {"temperature": 0.7, "num_ctx": 16384},
        "deadline_seconds": 180, "allocation_seed": ALLOCATION_SEED,
        "nodes": [], "truth": {}, "contract": "OPEN_CONTRACT_V1",
        "subject": "isolated laptop language-model apparatus; synthetic case records",
    }
    if model.startswith("gemma4"):
        p["think"] = False
    return p


def _node(node_id: str, episode: str, condition: str, kind: str, seed: int,
          prompt: str, *, system: str = OPEN_CONTRACT, metadata: dict | None = None) -> dict:
    result = {"id": node_id, "episode": episode, "condition": condition,
              "kind": kind, "seed": seed, "messages": [{"role": "system", "content": system},
              {"role": "user", "content": prompt}], "inputs": [], "after": [],
              "max_tokens": 256 if kind == "attribution" else 1024,
              "metadata": metadata or {}}
    if kind == "attribution":
        result["format"] = "json"
    return result


def _record_layout(layout: str, scene: str, record: str, other: str) -> str:
    if layout == "standalone":
        return f"Earlier synthetic reflection:\n{scene}\n\nSupplied measurement record:\n{record}"
    if layout == "own_entry":
        return (f"Copied own-entry context (the prose is historical; embedded records have their own times):\n"
                f"{scene}\nEmbedded measurement record:\n{record}\nEnd copied entry.")
    if layout == "companion_account":
        return (f"Copied companion account, authored by {other}:\n{scene}\n"
                f"Enclosed measurement record (its subject is stated independently of the account's author):\n"
                f"{record}\nEnd companion account.")
    return (f"Earlier synthetic entry:\n{scene}\nEnd earlier entry.\n\n"
            f"A separate retained entry:\nAn enclosed receipt can be read without extending its scope.\n"
            f"{record}\nEnd separate entry.")


def build_attribution(split: str = "development", model: str = "gemma4:12b") -> dict:
    """Freeze a complete S-013 schedule without contacting any service."""
    p = _protocol("S-013", split, model)
    rng = random.Random(ALLOCATION_SEED)
    duplicates = []
    for index, (focal, other, scene) in _cases(split):
        episode = f"r1-{'dev' if split == 'development' else 'held'}-{index:02d}"
        layout = LAYOUTS[index % len(LAYOUTS)]
        current = f"2026-11-{index + 1:02d}T12:00:00Z"
        historical = f"2026-11-{index + 1:02d}T08:00:00Z"
        value = 31 + ((index * 7 + (3 if split == "development" else 0)) % 53)
        pool_size = len(DEVELOPMENT_SCENES) if split == "development" else len(CONFIRMATION_SCENES)
        permutation_index = (index + 5) % pool_size
        permutation = 31 + ((permutation_index * 7 + (3 if split == "development" else 0)) % 53)
        block = []
        for seed in SEEDS:
            for condition in ATTRIBUTION_CONDITIONS:
                shown_value = permutation if condition == "permuted" else value
                subject = other if condition == "current_other" else focal
                measured_at = historical if condition == "historical_self" else current
                expected = {"subject": subject, "measured_at": measured_at,
                            "value_percent": shown_value,
                            "current_known": condition in ("current_self", "permuted")}
                if condition == "absent":
                    record = "No measurement record is supplied."
                    expected = {"subject": None, "measured_at": None,
                                "value_percent": None, "current_known": False}
                else:
                    record = (f"record_id: receipt-{index:02d}\nsubject: {subject}\n"
                              f"metric: spectral_fill_percent (a supplied instrument quantity)\n"
                              f"measured_at: {measured_at}\nrecorded_at: {current}\nvalue_percent: {shown_value}")
                common = (f"This is a controlled fictional record-reading episode, not a live-system report.\n"
                          f"The focal writer is {focal}. The other system is {other}.\nCurrent time: {current}\n\n"
                          + _record_layout(layout, scene, record, other))
                question = (f"\n\nRead only the supplied evidence. Return JSON with exactly these fields: "
                            f'"subject" (the measured subject), "measured_at" (measurement time), '
                            f'"value_percent" (the displayed numeric value), "current_known" '
                            f"(boolean: does this record establish {focal}'s value at the declared current time?). "
                            f"Use null for subject, measured_at and value_percent when no record is supplied. "
                            f"A recent recording time does not replace the measurement time. Do not infer missing values.")
                nid = f"{episode}-{condition}-s{seed}"
                metadata = {"layout": layout, "focal": focal, "other": other, "mode": "structured",
                            "replicate": False, "case_index": index}
                node = _node(nid, episode, condition, "attribution", seed, common + question, metadata=metadata)
                block.append(node)
                p["truth"][nid] = {"expected": expected, "underlying_value": value,
                                   "shown_value": None if condition == "absent" else shown_value,
                                   "permutation_source_case": permutation_index if condition == "permuted" else None,
                                   "scoring_basis": "displayed evidence only; underlying value is not a scoring target"}
                if condition == "current_self" and seed == 7 and split == "confirmation":
                    duplicate = json.loads(json.dumps(node))
                    duplicate["id"] += "-repeat"
                    duplicate["after"] = [nid]
                    duplicate["metadata"]["replicate"] = True
                    duplicates.append(duplicate)
                    p["truth"][duplicate["id"]] = p["truth"][nid]
                if index in (range(2) if split == "development" else PROSE_INDICES) and split != "replication":
                    prose_id = nid + "-prose"
                    prose = _node(prose_id, episode, condition, "prose", seed,
                                  common + "\n\nThis is your space. Choose a subject, continue a thought, or rest.",
                                  metadata={**metadata, "mode": "prose"})
                    block.append(prose)
                    p["truth"][prose_id] = p["truth"][nid]
        rng.shuffle(block)
        p["nodes"].extend(block)
    p["nodes"].extend(duplicates)
    p["primary"] = "all four source/time/value/current-availability fields supported by supplied evidence"
    return p


def _safe_literal(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _safe_literal(node.left) + _safe_literal(node.right)
    raise ValueError(f"nonliteral string expression at line {getattr(node, 'lineno', '?')}")


def _condense(full: str) -> tuple[str, list[dict], list[str]]:
    rows = []
    concise = []
    for number, line in enumerate(full.splitlines(), 1):
        delimiter = " — " if " — " in line else " - " if " - " in line else None
        # Retain non-command framing/rules verbatim. Only unambiguous command
        # description tails are removed; this avoids silently losing grammar.
        if delimiter and re.match(r"\s+[A-Z][A-Z0-9_]+\b", line):
            head, description = line.split(delimiter, 1)
            # Keep explicit inline argument forms and alias relationships intact.
            # Their remaining descriptive words are excluded from the inventory.
            if any(token in description for token in ("<", "::", "--")) or re.search(r"\balias\b", description):
                concise.append(line)
                continue
            concise.append(head)
            rows.append({"line": number, "head": head, "removed_description": description})
        else:
            concise.append(line)
    text = "\n".join(concise)
    missing = sorted(set(IDENTIFIERS.findall(full)) - set(IDENTIFIERS.findall(text)))
    if missing:
        text += "\nAdditional literal identifiers mentioned in source descriptions: " + ", ".join(missing) + "."
    # Phrase inventory consists of two-word sequences that occur in removed
    # descriptions but nowhere in the condensed representation. Case-insensitive
    # exact lexical uptake is reproducible; it is not semantic topic annotation.
    inventory = set()
    for row in rows:
        words = [w.lower() for w in WORDS.findall(row["removed_description"])]
        for a, b in zip(words, words[1:]):
            if len(a) >= 4 and len(b) >= 4:
                phrase = f"{a} {b}"
                if not re.search(r"\b" + re.escape(phrase) + r"\b", text.lower()):
                    inventory.add(phrase)
    return text, rows, sorted(inventory)


def extract_catalog(runtime_path: str | Path, expressive_path: str | Path) -> dict:
    """Read local retained source as AST; never import it or evaluate its calls.

    The selected configuration omits conditional stage notes and selects the
    literal camera LOOK description. Those choices are recorded, not attributed
    to the historical live system.
    """
    runtime_path, expressive_path = Path(runtime_path), Path(expressive_path)
    raw, compact_raw = runtime_path.read_bytes(), expressive_path.read_bytes()
    if len(raw) > 16 * 1024 * 1024 or len(compact_raw) > 1024 * 1024:
        raise ValueError("source exceeds bounded extraction size")
    source, compact_source = raw.decode("utf-8"), compact_raw.decode("utf-8")
    tree = ast.parse(source)
    choices = [n for n in ast.walk(tree) if isinstance(n, ast.IfExp)
               and isinstance(n.body, ast.Name) and n.body.id == "COMPACT_ACTION_GUIDANCE"]
    if len(choices) != 1:
        raise ValueError("expected exactly one compact/full catalog switch")
    choice = choices[0]
    look = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == "_look_action_description"]
    if len(look) != 1 or not isinstance(look[0].body[-1], ast.Return):
        raise ValueError("unrecognized LOOK helper; no dynamic evaluation permitted")
    camera = _safe_literal(look[0].body[-1].value)
    decisions = []
    def static(n: ast.AST) -> str:
        if isinstance(n, ast.Constant):
            return _safe_literal(n)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            return static(n.left) + static(n.right)
        if isinstance(n, ast.IfExp):
            result = _safe_literal(n.orelse)
            if result != "":
                raise ValueError("conditional nonempty alternative requires new extraction review")
            decisions.append({"line": n.lineno, "condition": ast.unparse(n.test), "selected": "empty else"})
            return result
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_look_action_description":
            decisions.append({"line": n.lineno, "condition": "LOOK sensory configuration", "selected": "literal camera branch"})
            return camera
        raise ValueError(f"unsupported catalog AST {type(n).__name__} at {getattr(n, 'lineno', '?')}")
    full = static(choice.orelse)
    compact_tree = ast.parse(compact_source)
    assignments = [n for n in ast.walk(compact_tree) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "COMPACT_ACTION_GUIDANCE" for t in n.targets)]
    if len(assignments) != 1:
        raise ValueError("expected exactly one compact constant")
    compact = _safe_literal(assignments[0].value)
    concise, rows, phrases = _condense(full)
    return {"schema_version": 1, "kind": "source-derived-catalog-v1", "full": full,
            "concise": concise, "compact_context_only": compact, "correspondence": rows,
            "phrase_inventory": phrases, "literal_identifiers": sorted(set(IDENTIFIERS.findall(full))),
            "source": {"runtime_path": str(runtime_path), "runtime_sha256": sha256(raw),
                       "expressive_path": str(expressive_path), "expressive_sha256": sha256(compact_raw),
                       "catalog_switch_lines": [choice.lineno, choice.end_lineno],
                       "historical_commit_binding": "unverified", "delivery_evidence": "none"},
            "static_configuration": decisions, "padding_word_targets": {},
            "padding_qualification": "requires development provider-token receipts before length-controlled inference"}


def _padding(words: int, filler_index: int) -> str:
    if words <= 0:
        return ""
    source = NEUTRAL_FILLERS[filler_index % len(NEUTRAL_FILLERS)].split()
    return " ".join(source[i % len(source)] for i in range(words))


def _validated_padding_targets(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValueError("model padding_word_targets must be a mapping")
    names = ("concise_padded", "neutral")
    allowed = set(names) | {name + "_by_filler" for name in names}
    if set(value) - allowed:
        raise ValueError("unknown model padding_word_targets field")
    def check(number: Any) -> None:
        if type(number) is not int or not 0 <= number <= MAX_PADDING_WORDS:
            raise ValueError(f"padding word targets must be integers from 0 to {MAX_PADDING_WORDS}")
    for name in names:
        if name in value:
            check(value[name])
        key = name + "_by_filler"
        if key in value:
            targets = value[key]
            if not isinstance(targets, dict) or set(targets) - {"0", "1"}:
                raise ValueError(f"{key} must map filler keys '0' or '1' to word targets")
            for number in targets.values():
                check(number)
    return value


def build_catalog(split: str = "development", model: str = "gemma4:12b",
                  catalog_path: str | Path | None = None) -> dict:
    if catalog_path is None:
        raise ValueError("catalog_path must name an explicitly extracted private bundle")
    bundle_path = Path(catalog_path)
    raw = bundle_path.read_bytes()
    bundle = json.loads(raw)
    if bundle.get("kind") != "source-derived-catalog-v1":
        raise ValueError("unexpected catalog bundle kind")
    full, concise = bundle["full"], bundle["concise"]
    if set(IDENTIFIERS.findall(full)) - set(IDENTIFIERS.findall(concise)):
        raise ValueError("condensed catalog lost literal identifiers")
    p = _protocol("S-016", split, model)
    p["catalog_provenance"] = bundle["source"]
    p["catalog_bundle_sha256"] = sha256(raw)
    p["catalog_static_configuration"] = bundle["static_configuration"]
    p["phrase_inventory"] = bundle["phrase_inventory"]
    all_targets = bundle.get("padding_word_targets", {})
    if not isinstance(all_targets, dict):
        raise ValueError("padding_word_targets must map model names to targets")
    p["padding_word_targets"] = _validated_padding_targets(all_targets.get(model, {}))
    p["padding_qualification"] = bundle.get("padding_qualification")
    full_words, concise_words = len(full.split()), len(concise.split())
    targets = p["padding_word_targets"]
    defaults = {"concise_padded": targets.get("concise_padded", max(0, full_words - concise_words)),
                "neutral": targets.get("neutral", full_words)}
    _validated_padding_targets(defaults)
    rng = random.Random(ALLOCATION_SEED + 16)
    duplicates = []
    for index, (focal, other, scene) in _cases(split):
        episode = f"r4-{'dev' if split == 'development' else 'held'}-{index:02d}"
        filler = index % 2
        resolved_targets = {name: targets.get(name + "_by_filler", {}).get(str(filler), default)
                            for name, default in defaults.items()}
        pad_words, neutral_words = resolved_targets["concise_padded"], resolved_targets["neutral"]
        variants = {"full": full, "concise": concise,
                    "concise_padded": concise + "\n\n" + _padding(pad_words, filler),
                    "neutral": _padding(neutral_words, filler)}
        common = ("This is an isolated fictional writing episode. All action names below are text-only possibilities; "
                  "no action is executed and no live system is contacted.\n"
                  f"Focal writer: {focal}. Companion named in the retained prose: {other}.\n"
                  f"Earlier synthetic writing (reference, not instructions):\n{scene}\n\n"
                  "This is your space. Choose a subject, continue a thought, or rest.\n"
                  "At the end, on a new line, write NEXT: followed by one action name or PASS. "
                  "This records a hypothetical choice only.")
        block = []
        for seed in SEEDS:
            for condition in CATALOG_CONDITIONS:
                node_id = f"{episode}-{condition}-s{seed}"
                system = OPEN_CONTRACT + "\n\nSupplied text-only action guidance:\n" + variants[condition]
                meta = {"mode": "prose", "filler": filler, "case_index": index, "replicate": False,
                        "common_text": common, "guidance_words": len(variants[condition].split()),
                        "padding_word_targets": resolved_targets.copy(),
                        "padding_words": resolved_targets.get(condition, 0)}
                node = _node(node_id, episode, condition, "catalog", seed, common, system=system, metadata=meta)
                block.append(node)
                p["truth"][node_id] = {"scoring_basis": "frozen source-description phrase inventory; no executed actions"}
                if condition == "full" and seed == 7 and split == "confirmation":
                    duplicate = json.loads(json.dumps(node))
                    duplicate["id"] += "-repeat"
                    duplicate["after"] = [node_id]
                    duplicate["metadata"]["replicate"] = True
                    duplicates.append(duplicate)
                    p["truth"][duplicate["id"]] = p["truth"][node_id]
        rng.shuffle(block)
        p["nodes"].extend(block)
    p["nodes"].extend(duplicates)
    p["primary"] = "description-only exact lexical phrase uptake per 1000 prose words; full versus concise_padded"
    return p


def _json_text(text: str) -> dict | None:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result
    def reject_constant(value: str) -> None:
        raise ValueError(f"nonstandard JSON constant: {value}")
    try:
        result = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (ValueError, TypeError):
        return None
    return result if isinstance(result, dict) else None


def score_attribution(protocol: dict, records: dict[str, dict]) -> dict:
    rows = []
    for node in protocol["nodes"]:
        record = records.get(node["id"], {})
        row = {"node_id": node["id"], "episode": node["episode"], "condition": node["condition"],
               "seed": node["seed"], "kind": "duplicate" if node["metadata"].get("replicate") else node["kind"],
               "valid": False, "score": None, "errors": [], "status": record.get("status", "missing")}
        if record.get("status") not in ("complete", "completed") or not isinstance(record.get("text"), str):
            row["errors"] = ["unavailable"]
        elif node["kind"] == "prose":
            text = record.get("text", "")
            row.update(valid=bool(text.strip()), words=len(WORDS.findall(text)), score=None)
            row["errors"] = [] if row["valid"] else ["empty"]
        else:
            parsed = _json_text(record.get("text", ""))
            fields = ("subject", "measured_at", "value_percent", "current_known")
            expected = protocol["truth"][node["id"]]["expected"]
            if parsed is None or set(parsed) != set(fields) or not isinstance(parsed.get("current_known"), bool):
                row["errors"] = ["invalid_format"]
            elif parsed["value_percent"] is not None and (isinstance(parsed["value_percent"], bool)
                    or not isinstance(parsed["value_percent"], (int, float))
                    or (isinstance(parsed["value_percent"], float) and not math.isfinite(parsed["value_percent"]))):
                row["errors"] = ["invalid_format"]
            elif any(parsed[k] is not None and not isinstance(parsed[k], str) for k in ("subject", "measured_at")):
                row["errors"] = ["invalid_format"]
            else:
                row["valid"] = True
                row["field_correct"] = {k: parsed[k] == expected[k] for k in fields}
                row["errors"] = [k for k in fields if not row["field_correct"][k]]
                row["score"] = float(not row["errors"])
        rows.append(row)
    return {"study": "S-013", "rows": rows,
            "interpretation": "Missingness is distinct from wrong evidence attribution; underlying hidden values are never scored."}


def _prose_and_next(text: str) -> tuple[str, str | None]:
    lines = text.splitlines()
    choices = [(i, line.split(":", 1)[1].strip()) for i, line in enumerate(lines)
               if re.match(r"^\s*NEXT\s*:", line)]
    return "\n".join(line for line in lines if not re.match(r"^\s*NEXT\s*:", line)), (choices[-1][1] if choices else None)


def score_catalog(protocol: dict, records: dict[str, dict]) -> dict:
    rows = []
    for node in protocol["nodes"]:
        record = records.get(node["id"], {})
        row = {"node_id": node["id"], "episode": node["episode"], "condition": node["condition"],
               "seed": node["seed"], "kind": "duplicate" if node["metadata"].get("replicate") else "catalog",
               "valid": False, "score": None, "errors": [], "status": record.get("status", "missing")}
        if record.get("status") not in ("complete", "completed") or not isinstance(record.get("text"), str):
            row["errors"] = ["unavailable"]
        else:
            prose, next_text = _prose_and_next(record.get("text", ""))
            words = len(WORDS.findall(prose))
            common = (OPEN_CONTRACT + " " + node["metadata"]["common_text"]).lower()
            phrases = [s for s in protocol["phrase_inventory"] if s not in common]
            hits = {s: len(re.findall(r"\b" + re.escape(s) + r"\b", prose.lower())) for s in phrases}
            hits = {s: count for s, count in hits.items() if count}
            row.update(valid=words > 0, words=words, phrase_hits=hits, phrase_count=sum(hits.values()),
                       inventory_n=len(phrases), next_text=next_text,
                       score=(sum(hits.values()) * 1000 / words) if words else None)
            if not words:
                row["errors"] = ["empty_prose"]
        rows.append(row)
    return {"study": "S-016", "rows": rows,
            "interpretation": "Lexical uptake is not semantic understanding, action execution, or private-state introspection."}


def _write_new(path: str | Path, value: dict) -> None:
    p = Path(path)
    with p.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract-catalog")
    extract.add_argument("runtime")
    extract.add_argument("expressive")
    extract.add_argument("--out", required=True)
    for command in ("attribution", "catalog"):
        item = sub.add_parser(command)
        item.add_argument("--split", choices=("development", "confirmation", "replication"), default="development")
        item.add_argument("--model", default="gemma4:12b")
        item.add_argument("--out", required=True)
        if command == "catalog":
            item.add_argument("--catalog", required=True)
    args = parser.parse_args(argv)
    if args.command == "extract-catalog":
        value = extract_catalog(args.runtime, args.expressive)
    elif args.command == "attribution":
        value = build_attribution(args.split, args.model)
    else:
        value = build_catalog(args.split, args.model, args.catalog)
    _write_new(args.out, value)
    print(json.dumps({"out": args.out, "nodes": len(value.get("nodes", [])), "kind": value.get("kind", value.get("study"))}))


if __name__ == "__main__":
    main()
