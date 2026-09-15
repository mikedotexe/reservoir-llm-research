#!/usr/bin/env python3
"""Read-only summary of the Tranche 1 generation records for both beings.

Reads (never writes):
  minime : <minime>/workspace/generations/<day>/gen_*.json
  astrid : <bridge>/workspace/generations/<day>/gen_*.json
  baseline: <minime>/workspace/diagnostics/llm_timing.jsonl (the pre-tranche
            diagnostic; same fields minus the text) for the window before the
            records started.

Per lane x backend: n, status mix, timeout rate, elapsed p50/p90, response
chars, fallback share, and the persona-drop rate on `response_text` using the
five signal families from exercise 3 (assistant openers, bold task headers,
bulleted rationale, third-person "Minime's", "I will now execute"; two or more
families = drop). Also store size and the system-prompt dedup ratio.

Usage: python3 probes/generation_records_24h.py [--hours 24] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MINIME_ROOT = Path("/Users/v/other/minime/workspace")
ASTRID_ROOT = Path("/Users/v/other/astrid/capsules/spectral-bridge/workspace")

# Exercise 3's persona-drop families, re-implemented (the originals were an
# ad-hoc session snippet). A record "drops" when >= 2 families fire.
_OPENERS = re.compile(
    r"^\s*(okay|ok|sure|certainly|of course|absolutely|here'?s|here is|as an ai|"
    r"i can help|let me know if|i'd be happy)\b",
    re.IGNORECASE | re.MULTILINE,
)
_BOLD_HEADER = re.compile(r"^\s*\*\*[^*\n]{3,80}\*\*:?\s*$", re.MULTILINE)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+\S", re.MULTILINE)
_THIRD_PERSON = re.compile(r"\bminime(?:'s| is| has| will| should)\b", re.IGNORECASE)
_EXECUTE = re.compile(r"\bI will now (?:execute|proceed|perform)\b|\bexecuting (?:the )?(?:action|task)\b", re.IGNORECASE)


def persona_drop_families(text: str) -> List[str]:
    families = []
    if _OPENERS.search(text):
        families.append("opener")
    if _BOLD_HEADER.search(text):
        families.append("bold_header")
    if len(_BULLET.findall(text)) >= 3:
        families.append("bullets")
    if _THIRD_PERSON.search(text):
        families.append("third_person")
    if _EXECUTE.search(text):
        families.append("execute")
    return families


def is_persona_drop(text: Optional[str]) -> bool:
    return bool(text) and len(persona_drop_families(text)) >= 2


def load_records(root: Path, since_ms: int, until_ms: int) -> Tuple[List[Dict[str, Any]], int]:
    records: List[Dict[str, Any]] = []
    bad = 0
    if not root.is_dir():
        return records, bad
    for day_dir in sorted(root.iterdir()):
        if not day_dir.is_dir() or day_dir.name == "system_prompts":
            continue
        for path in sorted(day_dir.glob("gen_*.json")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    record = json.load(handle)
            except Exception:
                bad += 1
                continue
            created = record.get("created_at_unix_ms")
            if not isinstance(created, (int, float)):
                bad += 1
                continue
            if since_ms <= created < until_ms:
                record["_path"] = str(path)
                records.append(record)
    return records, bad


def pct(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return round(ordered[index], 1)


def dir_size_bytes(root: Path) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            try:
                total += os.stat(os.path.join(dirpath, name)).st_size
            except OSError:
                pass
    return total


def dedup_ratio(root: Path, records: Iterable[Dict[str, Any]]) -> Optional[float]:
    """chars of system prompts referenced by records / bytes stored once."""
    referenced = 0
    for record in records:
        for message in record.get("messages") or []:
            if message.get("role") == "system" and message.get("content_sha256"):
                referenced += int(message.get("chars") or 0)
    stored = dir_size_bytes(root / "system_prompts") if (root / "system_prompts").is_dir() else 0
    if stored == 0:
        return None
    return round(referenced / stored, 1)


def summarize_minime(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(str(record.get("lane")), str(record.get("backend")))].append(record)
    rows = []
    for (lane, backend), items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        statuses = Counter(str(item.get("status")) for item in items)
        elapsed = [float(item["elapsed_s"]) for item in items if isinstance(item.get("elapsed_s"), (int, float))]
        ok_items = [item for item in items if item.get("status") == "ok"]
        chars = [int(item.get("response_chars") or 0) for item in ok_items]
        drops = sum(1 for item in ok_items if is_persona_drop(item.get("response_text")))
        rows.append({
            "lane": lane,
            "backend": backend,
            "n": len(items),
            "status": dict(statuses),
            "timeout_rate": round(statuses.get("timeout", 0) / len(items), 3),
            "elapsed_p50": pct(elapsed, 0.5),
            "elapsed_p90": pct(elapsed, 0.9),
            "response_chars_p50": pct([float(c) for c in chars], 0.5),
            "fallback_used": sum(1 for item in items if item.get("fallback_used")),
            "persona_drop_rate": round(drops / len(ok_items), 3) if ok_items else None,
            "linked_journal": sum(
                1 for item in items if any(link.get("kind") == "journal" for link in item.get("linked_artifacts") or [])
            ),
            "models": sorted({str(item.get("model")) for item in items}),
        })
    generations = {record.get("generation_id") for record in records}
    lanes_unknown = sum(1 for record in records if record.get("lane") == "unknown")
    return {
        "records": len(records),
        "generations": len(generations),
        "lane_unknown": lanes_unknown,
        "context_modes": dict(Counter(str(record.get("context_mode")) for record in records)),
        "kinds": dict(Counter(str(record.get("kind")) for record in records)),
        "next_action_parsed": dict(Counter(str(record.get("next_action_parsed")) for record in records if record.get("status") == "ok").most_common(12)),
        "rows": rows,
    }


def summarize_astrid(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record.get("backend"))].append(record)
    rows = []
    for backend, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        statuses = Counter(str(item.get("status")) for item in items)
        elapsed = [float(item["elapsed_s"]) for item in items if isinstance(item.get("elapsed_s"), (int, float))]
        ok_items = [item for item in items if item.get("status") == "ok"]
        rows.append({
            "backend": backend,
            "n": len(items),
            "status": dict(statuses),
            "elapsed_p50": pct(elapsed, 0.5),
            "elapsed_p90": pct(elapsed, 0.9),
            "response_chars_p50": pct([float(item.get("response_chars") or 0) for item in ok_items], 0.5),
            "persona_drop_rate": round(sum(1 for item in ok_items if is_persona_drop(item.get("response_text"))) / len(ok_items), 3) if ok_items else None,
            "models": sorted({str(item.get("model")) for item in items}),
            "timeouts_s": sorted({int(item.get("timeout_s") or 0) for item in items}),
        })
    own_body = [record.get("own_body") or {} for record in records if record.get("attempt_index") == 0]
    return {
        "records": len(records),
        "generations": len({record.get("generation_id") for record in records}),
        "contract_versions": dict(Counter(str(record.get("contract_version")) for record in records)),
        "own_body_present_rate": round(sum(1 for item in own_body if item.get("present")) / len(own_body), 3) if own_body else None,
        "own_body_status": dict(Counter(str(item.get("status")) for item in own_body)),
        "own_body_trimmed": sum(1 for item in own_body if item.get("trimmed")),
        "prompt_chars_p50": pct([float((record.get("prompt") or {}).get("final_prompt_chars") or 0) for record in records if record.get("attempt_index") == 0], 0.5),
        "rows": rows,
    }


def baseline_from_timing(path: Path, since_s: float, until_s: float) -> Dict[str, Any]:
    if not path.is_file():
        return {"note": f"missing {path}"}
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    parsed_total = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except Exception:
                continue
            stamp = item.get("timestamp")
            if not isinstance(stamp, str):
                continue
            try:
                from datetime import datetime
                when = datetime.fromisoformat(stamp).timestamp()
            except Exception:
                continue
            if since_s <= when < until_s:
                parsed_total += 1
                groups[(str(item.get("prompt_class")), str(item.get("backend")))].append(item)
    rows = []
    for (prompt_class, backend), items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        statuses = Counter(str(item.get("status")) for item in items)
        errors = Counter(str(item.get("error")) for item in items if item.get("error"))
        elapsed = [float(item["elapsed_s"]) for item in items if isinstance(item.get("elapsed_s"), (int, float))]
        rows.append({
            "prompt_class": prompt_class,
            "backend": backend,
            "n": len(items),
            "status": dict(statuses),
            "timeout_rate": round(sum(count for name, count in errors.items() if "timeout" in name.lower()) / len(items), 3),
            "elapsed_p50": pct(elapsed, 0.5),
            "elapsed_p90": pct(elapsed, 0.9),
        })
    return {"calls": parsed_total, "rows": rows}


def render(report: Dict[str, Any]) -> str:
    out: List[str] = []
    window = report["window"]
    out.append(f"Generation records, last {window['hours']} h ({window['since']} → {window['until']})")
    out.append("")
    m = report["minime"]
    out.append(f"minime: {m['records']} records / {m['generations']} generations, lane unknown: {m['lane_unknown']}, "
               f"store {report['stores']['minime']['size_mb']} MB, system-prompt dedup x{report['stores']['minime']['dedup_ratio']}")
    out.append(f"  kinds {m['kinds']}  context_modes {m['context_modes']}")
    out.append(f"  NEXT parsed (ok records): {m['next_action_parsed']}")
    out.append("  lane                    backend      n   timeout  p50s   p90s  chars  fallback  drop   journal  models")
    for row in m["rows"]:
        out.append(f"  {row['lane']:<23} {row['backend']:<11} {row['n']:>3}  {row['timeout_rate']:>6.1%}  {row['elapsed_p50'] or 0:>5}  {row['elapsed_p90'] or 0:>5}  "
                   f"{int(row['response_chars_p50'] or 0):>5}  {row['fallback_used']:>8}  {('' if row['persona_drop_rate'] is None else f'{row['persona_drop_rate']:.1%}'):>5}  "
                   f"{row['linked_journal']:>7}  {','.join(row['models'])}")
    out.append("")
    a = report["astrid"]
    out.append(f"astrid: {a['records']} records / {a['generations']} generations, contracts {a['contract_versions']}, "
               f"store {report['stores']['astrid']['size_mb']} MB, dedup x{report['stores']['astrid']['dedup_ratio']}")
    out.append(f"  own_body present {a['own_body_present_rate']}, status {a['own_body_status']}, trimmed {a['own_body_trimmed']}, prompt chars p50 {a['prompt_chars_p50']}")
    out.append("  backend           n   status                                   p50s   p90s  chars  drop   models / timeouts")
    for row in a["rows"]:
        out.append(f"  {row['backend']:<15} {row['n']:>3}   {str(row['status']):<40} {row['elapsed_p50'] or 0:>5}  {row['elapsed_p90'] or 0:>5}  "
                   f"{int(row['response_chars_p50'] or 0):>5}  {('' if row['persona_drop_rate'] is None else f'{row['persona_drop_rate']:.1%}'):>5}  {','.join(row['models'])} / {row['timeouts_s']}")
    out.append("")
    b = report["baseline_minime_timing"]
    if "rows" in b:
        out.append(f"baseline (minime llm_timing.jsonl, the {window['hours']} h before the window): {b['calls']} calls")
        out.append("  prompt_class            backend      n   timeout  p50s   p90s  status")
        for row in b["rows"][:16]:
            out.append(f"  {row['prompt_class']:<23} {row['backend']:<11} {row['n']:>3}  {row['timeout_rate']:>6.1%}  {row['elapsed_p50'] or 0:>5}  {row['elapsed_p90'] or 0:>5}  {row['status']}")
    else:
        out.append(f"baseline: {b.get('note')}")
    if report["bad_files"]:
        out.append("")
        out.append(f"unreadable record files: {report['bad_files']}")
    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--until", type=float, default=None, help="unix seconds; default now")
    parser.add_argument("--minime-root", type=Path, default=MINIME_ROOT)
    parser.add_argument("--astrid-root", type=Path, default=ASTRID_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    until_s = args.until or time.time()
    since_s = until_s - args.hours * 3600.0
    minime_dir = args.minime_root / "generations"
    astrid_dir = args.astrid_root / "generations"
    minime_records, bad_m = load_records(minime_dir, int(since_s * 1000), int(until_s * 1000))
    astrid_records, bad_a = load_records(astrid_dir, int(since_s * 1000), int(until_s * 1000))
    report = {
        "window": {
            "hours": args.hours,
            "since": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(since_s)),
            "until": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(until_s)),
        },
        "minime": summarize_minime(minime_records),
        "astrid": summarize_astrid(astrid_records),
        "stores": {
            "minime": {"size_mb": round(dir_size_bytes(minime_dir) / 1e6, 1) if minime_dir.is_dir() else 0.0, "dedup_ratio": dedup_ratio(minime_dir, minime_records)},
            "astrid": {"size_mb": round(dir_size_bytes(astrid_dir) / 1e6, 1) if astrid_dir.is_dir() else 0.0, "dedup_ratio": dedup_ratio(astrid_dir, astrid_records)},
        },
        "baseline_minime_timing": baseline_from_timing(args.minime_root / "diagnostics" / "llm_timing.jsonl", since_s - args.hours * 3600.0, since_s),
        "bad_files": {"minime": bad_m, "astrid": bad_a},
    }
    if args.json:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
