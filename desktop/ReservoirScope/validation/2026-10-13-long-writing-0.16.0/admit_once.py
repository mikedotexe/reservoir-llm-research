#!/usr/bin/env python3
"""One passive admission; never start a service or retry a refused sample."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess


def main():
    root = Path(__file__).resolve().parent
    destination = root / "host-admission-01.json"
    # Exclusivity precedes all probes; a partial receipt also forbids a rerun.
    with destination.open("x") as stream:
        freeze = root / "evaluation-freeze-01.json"
        raw = freeze.read_bytes()
        frozen = json.loads(raw)
        for item in frozen["files"]:
            if hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"Frozen file changed: {item['path']}")
        results = []
        for command in (
            ["/usr/sbin/sysctl", "-n", "hw.memsize"],
            ["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
            ["/usr/bin/memory_pressure"],
        ):
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                results.append({"command": command, "exit": result.returncode,
                                "stdout": result.stdout, "stderr": result.stderr})
            except (OSError, subprocess.TimeoutExpired) as error:
                results.append({"command": command, "error": str(error)})
        pressure = free = None
        if results[1].get("exit") == 0:
            value = results[1]["stdout"].strip()
            if re.fullmatch(r"\d+", value):
                pressure = int(value)
        if results[2].get("exit") == 0:
            found = re.search(r"System-wide memory free percentage:\s*(\d+)%", results[2]["stdout"])
            if found:
                free = int(found.group(1))
        disk = shutil.disk_usage(root).free
        admitted = (all(x.get("exit") == 0 for x in results) and pressure == 1
                    and free is not None and free >= 35 and disk >= 8 * 1024**3)
        receipt = {"capturedUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "episodeId": "long-writing-0.16.0-episode01",
                   "scope": "One passive pre-launch admission. No service/Being inspection or process changes. No retry.",
                   "freezeSha256": hashlib.sha256(raw).hexdigest(), "results": results,
                   "pressureLevel": pressure, "freePercent": free, "diskFreeBytes": disk,
                   "admitted": admitted}
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
        stream.flush()
    print(json.dumps({"admitted": admitted, "pressureLevel": pressure,
                      "freePercent": free, "diskFreeBytes": disk}))


if __name__ == "__main__":
    main()
