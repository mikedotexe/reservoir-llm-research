#!/usr/bin/env python3
"""Independent source-clock interval expectations for Reference zones QA."""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "visualizations/reservoir-3d/data.json"
samples = json.loads(source.read_bytes())["samples"]
times = [datetime.fromisoformat(s["t_utc"].replace("Z", "+00:00")).timestamp() for s in samples]
origin = times[0]
result = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "collection_source_seconds": 30, "lifetime_source_seconds": 60,
          "scope": "Inclusive measured prefix, fixed source-time generations, first tied timestamp retained",
          "cases": []}
for index in [0, 5, 13, 20, 26, 50, 250, len(samples) - 1]:
    now = max(times[index], origin + samples[index]["t_s"])
    buckets = {}
    for j in range(index + 1):
        start = origin + math.floor((times[j] - origin) / 30) * 30
        if now - start < 60:
            buckets.setdefault(start, []).append(samples[j])
    ranges = [{"start_time": start, "age": now - start, "opacity": 1 - (now-start)/60,
               "collecting": now-start < 30, "count": len(rows),
               "high": max(rows, key=lambda s: s["fill_pct"]),
               "low": min(rows, key=lambda s: s["fill_pct"])}
              for start, rows in sorted(buckets.items())]
    result["cases"].append({"cursor_index": index, "source_time": now, "ranges": ranges})
print(json.dumps(result, indent=2))
