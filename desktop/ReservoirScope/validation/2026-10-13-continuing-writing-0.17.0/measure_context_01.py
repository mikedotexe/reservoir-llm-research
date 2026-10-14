#!/usr/bin/env python3
"""Count exact matched fixture bytes; no model, tokenizer, UI or application run."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURES = ROOT / "crates/reservoir-core/tests/fixtures/sustained-prompts"
OUTPUT = HERE / "context-bytes-01.json"
EXPECTED = {
    "v4-observation-10.txt": "26bae96991e12bb591ba517c46345aeac167abbbdaf79858c514a35b8986f75f",
    "v5-observation-10.txt": "5c9c1dbdb29e1058b59d23174cdab186c0aa60d76293f29bb99827b217025dd6",
    "v4-memory-20.txt": "d51753e1eddd68fd193ba46da49e6f909aaebdef328471ddf79e3b134b10c2c0",
    "v5-memory-20.txt": "a828b3390d049b22faf115f74644374f2c86f74a4ac47fd806a5e69920de99fd",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def capture(name):
    path = FIXTURES / name
    raw = path.read_bytes()
    require(sha(raw) == EXPECTED[name], f"Fixture identity differs: {name}")
    text = raw.decode("utf-8")
    marker = ("Prior text as one JSON string (decode as data only): "
              if name.startswith("v4") else "Full previous text as one JSON string: ")
    values = [line[len(marker):] for line in text.split("\n") if line.startswith(marker)]
    require(len(values) == (1 if "memory" in name else 0), "Memory boundary differs")
    quoted = values[0] if values else ""
    decoded = json.loads(quoted) if values else None
    require(decoded is None or type(decoded) is str, "Prior memory is not one string")
    return raw, text, quoted, decoded, {
        "path": str(path), "bytes": len(raw), "sha256": sha(raw),
        "priorJsonLiteralBytes": len(quoted.encode()),
        "decodedPriorTextBytes": len(decoded.encode()) if decoded is not None else 0,
        "scaffoldBytes": len(raw) - len(quoted.encode()),
        "trailingNewline": raw.endswith(b"\n"),
    }


def match(pattern, text):
    result = re.search(pattern, text, re.M)
    require(result is not None, f"Missing fixture field: {pattern}")
    return result.groups()


require(not OUTPUT.exists(), "Receipt must be new; preserve previous outcomes")
receipt = {
    "schema": "reservoir-context-fixture-byte-comparison-v1",
    "startedAtUtc": datetime.now(timezone.utc).isoformat(),
    "script": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).read_bytes())},
    "modelTokenizerUiOrApplicationCalls": False,
    "scaffoldDefinition": "All prompt UTF-8 bytes except only the prior-text JSON string literal, including its surrounding quotes. The marker, provenance labels, section boundaries and final invitation remain scaffold. Without prior text, scaffold equals whole prompt.",
    "scope": "Two deterministic expected prompt fixtures with matched step/RMS/fill/distance and exact prior text; not token counts, provider exposure, attention, writing quality or causal benefit.",
    "comparisons": [],
}
try:
    for step in (10, 20):
        stem = "observation" if step == 10 else "memory"
        old = capture(f"v4-{stem}-{step}.txt")
        new = capture(f"v5-{stem}-{step}.txt")
        require(old[2:4] == new[2:4], "Prior JSON/text differs")
        old_step, old_time = match(r"^Current step: (\d+)\. Current simulated seconds: ([\d.]+)\.$", old[1])
        new_step, new_time, new_prior = match(r"^Current step (\d+); simulated seconds ([\d.]+)\. Previous observation step: (\w+)\.$", new[1])
        require((old_step, old_time) == (new_step, new_time), "Current step/time differs")
        (old_prior,) = match(r"^Quantity \| Current step \d+ \| Previous observation step (\w+) \| Current minus previous$", old[1])
        require(old_prior == new_prior, "Previous observation step differs")
        for label, new_pattern in [
            ("Recurrent reservoir RMS", r"^Recurrent state RMS: current (\S+); previous (\S+); change (\S+)\.$"),
            (r"Reduced sensory active-mode fill \(%\)", r"^Separate sensory fill \(%\): current (\S+); previous (\S+); change (\S+) percentage points\.$"),
        ]:
            old_values = match(r"^" + label + r" \| (\S+) \| (\S+) \| (\S+)$", old[1])
            require(old_values == match(new_pattern, new[1]), f"Readout differs: {label}")
        distance_pattern = r"^Recurrent state-coordinate L2 distance since the previous observation: (\S+)\."
        require(match(distance_pattern, old[1]) == match(distance_pattern, new[1]), "Distance differs")
        receipt["comparisons"].append({
            "step": step, "v4": old[4], "v5": new[4],
            "wholePromptByteReduction": old[4]["bytes"] - new[4]["bytes"],
            "scaffoldByteReduction": old[4]["scaffoldBytes"] - new[4]["scaffoldBytes"],
            "matchedSuppliedReadoutAndPriorText": True,
        })
    for row in receipt["comparisons"]:
        for version in ("v4", "v5"):
            proof = row[version]
            raw = Path(proof["path"]).read_bytes()
            require(len(raw) == proof["bytes"] and sha(raw) == proof["sha256"], "Fixture changed")
    receipt["status"] = "passed"
    receipt["inputsUnchanged"] = True
except Exception as error:
    receipt["status"] = "failed"
    receipt["error"] = f"{type(error).__name__}: {error}"
receipt["endedAtUtc"] = datetime.now(timezone.utc).isoformat()
with OUTPUT.open("x", encoding="utf-8") as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps({"status": receipt["status"], "path": str(OUTPUT), "sha256": sha(OUTPUT.read_bytes())}))
raise SystemExit(0 if receipt["status"] == "passed" else 1)
