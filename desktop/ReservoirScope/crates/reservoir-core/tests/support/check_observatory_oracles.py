"""Compare frozen Observatory readers against unchanged native Evidence.swift.

Reads only this repository's bundled captures. Local temporary mutations exercise
rejection paths. No engine regeneration, live data, model or app-store access.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(command):
    result = subprocess.run([str(x) for x in command], capture_output=True, timeout=60)
    return result, {"command": [str(x) for x in command], "exitCode": result.returncode,
                    "stdoutSHA256": sha(result.stdout), "stderr": result.stderr.decode(errors="replace")[:2000]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("swift-oracle", "rust-oracle", "receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.exists():
        raise SystemExit("Refusing to replace an existing qualification receipt.")
    crate = Path(__file__).resolve().parents[2]
    repo = crate.parents[3]
    resources = repo / "desktop/ReservoirScope/src-tauri/resources"
    sources = [repo / "native/ReservoirScope/Sources/ReservoirScope/Evidence.swift", crate / "src/observatory.rs",
               crate / "examples/observatory_oracle.rs", Path(__file__), crate / "tests/support/observatory_oracle.swift"]
    names = ["data.json", "state-replay.json", "state-replay.bin", "state-geometry.json"]
    receipt = {"schema": "reservoir-observatory-native-reader-oracle-v1", "createdAtUTC": datetime.now(timezone.utc).isoformat(),
               "scope": "Frozen retained evidence structure, all decoded numeric values and row identities; no historical engine regeneration or cross-track clock join",
               "modelsContacted": False, "liveSourcesRead": False, "outcome": "incomplete", "checks": [],
               "sources": [{"path": str(p.relative_to(repo)), "sha256": sha(p.read_bytes())} for p in sources],
               "resources": [{"name": n, "sha256": sha((resources / n).read_bytes()), "bytes": (resources / n).stat().st_size} for n in names],
               "executables": [{"path": str(p.resolve()), "sha256": sha(p.read_bytes())} for p in (args.swift_oracle, args.rust_oracle)]}
    try:
        swift, sc = run([args.swift_oracle.resolve(), resources])
        rust, rc = run([args.rust_oracle.resolve(), resources])
        equal = swift.returncode == rust.returncode == 0 and json.loads(swift.stdout) == json.loads(rust.stdout)
        values = json.loads(rust.stdout) if rust.returncode == 0 else {}
        receipt["checks"].append({"name": "all-retained-values-and-identities", "passed": equal, "commands": [sc, rc],
                                  "counts": {k: values.get(k) for k in ("historyCount", "stateRows", "dimensions")},
                                  "numericDigests": {k: v for k, v in values.items() if k.endswith("NumericSHA256")}})
        for case in ("fill-outside-range", "elapsed-order", "missing-spectral-slot", "invented-node-layout", "binary-length", "rebound-nonfinite-state"):
            with tempfile.TemporaryDirectory(prefix="reservoir-observatory-oracle-") as temp:
                folder = Path(temp)
                for name in names:
                    shutil.copyfile(resources / name, folder / name)
                history = json.loads((folder / "data.json").read_bytes())
                manifest = json.loads((folder / "state-replay.json").read_bytes())
                geometry = json.loads((folder / "state-geometry.json").read_bytes())
                if case == "fill-outside-range":
                    history["samples"][0]["fill_pct"] = 101
                elif case == "elapsed-order":
                    history["samples"][1]["t_s"] = history["samples"][0]["t_s"]
                elif case == "missing-spectral-slot":
                    history["samples"][0]["cascade"].pop()
                elif case == "invented-node-layout":
                    manifest["node_layout_id"] = "unretained-layout"
                elif case == "binary-length":
                    raw = (folder / "state-replay.bin").read_bytes()
                    (folder / "state-replay.bin").write_bytes(raw[:-1])
                elif case == "rebound-nonfinite-state":
                    raw = bytearray((folder / "state-replay.bin").read_bytes())
                    raw[:4] = bytes.fromhex("0000c07f")
                    (folder / "state-replay.bin").write_bytes(raw)
                    manifest["source_sha256"] = sha(raw)
                    geometry["source"]["files"]["states"]["sha256"] = sha(raw)
                    encoded = json.dumps(geometry).encode()
                    (folder / "state-geometry.json").write_bytes(encoded)
                    manifest["geometry_sha256"] = sha(encoded)
                (folder / "data.json").write_text(json.dumps(history))
                (folder / "state-replay.json").write_text(json.dumps(manifest))
                swift, sc = run([args.swift_oracle.resolve(), folder])
                rust, rc = run([args.rust_oracle.resolve(), folder])
                receipt["checks"].append({"name": case, "passed": swift.returncode == rust.returncode == 1, "commands": [sc, rc]})
        receipt["outcome"] = "passed" if all(c["passed"] for c in receipt["checks"]) else "failed"
    finally:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x") as out:
            json.dump(receipt, out, indent=2)
            out.write("\n")
    print(json.dumps({"outcome": receipt["outcome"], "checks": len(receipt["checks"]), "receipt": str(args.receipt)}))
    raise SystemExit(0 if receipt["outcome"] == "passed" else 1)


if __name__ == "__main__":
    main()
