#!/usr/bin/env python3
"""Independent measured-prefix expectations for native Reference zones UI QA."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "visualizations/reservoir-3d/data.json"
samples = json.loads(source.read_bytes())["samples"]
result = {
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "scope": "Inclusive prefix of retained measured fill; all intervening rows, earliest tie wins",
    "cases": [],
}
for index in [0, 5, 20, 50, 250, len(samples) - 1]:
    prefix = samples[:index + 1]
    result["cases"].append({
        "cursor_index": index, "count": len(prefix), "current": prefix[-1]["fill_pct"],
        "high": max(prefix, key=lambda sample: sample["fill_pct"]),
        "low": min(prefix, key=lambda sample: sample["fill_pct"]),
    })
print(json.dumps(result, indent=2))
