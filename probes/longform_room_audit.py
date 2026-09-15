"""Read-only bounded generation/limit audit; no model, action or live write."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/outputs/2026-09-09-longform-room"
MINIME = Path("/Users/v/other/minime")
ASTRID = Path("/Users/v/other/astrid")
END = datetime.fromisoformat("2026-09-10T00:18:00+00:00").timestamp()
START = END - 3600


def main():
    OUT.mkdir(exist_ok=False)
    (OUT / "records").mkdir()
    rows, errors, counts = [], [], {}
    for day in ["2026-09-09", "2026-09-10"]:
        folder = MINIME / "workspace/generations" / day
        with os.scandir(folder) as entries:
            names = []
            for i, entry in enumerate(entries):
                if i >= 50000:
                    raise ValueError("Enumeration ceiling")
                names.append(entry.name)
        counts[day] = len(names)
        for name in sorted(names):
            match = re.fullmatch(r"gen_(\d+)_.+_a\d+\.json", name)
            if not match or not START <= int(match[1]) / 1000 < END:
                continue
            if len(rows) >= 500:
                raise ValueError("Selected-record ceiling")
            p = folder / name
            try:
                before = p.stat()
                if p.is_symlink() or before.st_size > 4*1024*1024:
                    raise ValueError("Nonregular/oversized record")
                raw = p.read_bytes()
                after = p.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError("Record changed during capture")
                d = json.loads(raw)
                (OUT / "records" / name).write_bytes(raw)
                timing = d.get("backend_timing") or {}
                rows.append(dict(path=str(p), retained="records/" + name,
                    sha256=hashlib.sha256(raw).hexdigest(), lane=d.get("lane"),
                    status=d.get("status"), pid=d.get("pid"),
                    ceiling=timing.get("effective_num_predict"),
                    generated_tokens=timing.get("eval_count"),
                    finish=timing.get("native_finish"), response_chars=d.get("response_chars"),
                    journal_links=sum(a.get("kind") == "journal" for a in d.get("linked_artifacts", [])),
                    adapter=d.get("adapter")))
            except (OSError, ValueError) as error:
                errors.append(dict(path=str(p), error=str(error)))
    groups = defaultdict(list)
    for row in rows:
        groups[row["lane"]].append(row)
    summary = {}
    for lane, group in groups.items():
        numbers = [r["generated_tokens"] for r in group if isinstance(r["generated_tokens"], int)]
        summary[lane] = dict(n=len(group), statuses=dict(Counter(r["status"] for r in group)),
            ceilings=dict(Counter(str(r["ceiling"]) for r in group)),
            native_finish=dict(Counter(str(r["finish"]) for r in group)),
            tokens_min=min(numbers) if numbers else None,
            tokens_median=statistics.median(numbers) if numbers else None,
            tokens_max=max(numbers) if numbers else None,
            journal_linked=sum(r["journal_links"] > 0 for r in group))
    raw = (ASTRID / "capsules/spectral-bridge/workspace/self_control_v2/astrid/state.json").read_bytes()
    (OUT / "astrid-self-control.json").write_bytes(raw)
    state = json.loads(raw)
    result = dict(captured_at=datetime.now(timezone.utc).isoformat(),
        since=datetime.fromtimestamp(START, timezone.utc).isoformat(),
        until_exclusive=datetime.fromtimestamp(END, timezone.utc).isoformat(),
        scope="Minime generation-file completion clock, current UTC day folders; linked journals distinguished. Multiple process eras and shared-hardware trial contention; descriptive, no effect estimate. Astrid preference is a separate current-state observation.",
        enumeration=counts, errors=errors, n=len(rows), summary=summary, records=rows,
        astrid_preference=state["state"]["preferences"]["response_token_limit"],
        astrid_state_sha256=hashlib.sha256(raw).hexdigest())
    (OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "probe.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
