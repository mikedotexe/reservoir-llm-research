"""Read-only source/metadata audit; no generation, model load or live-state writes.

Writes a bounded research packet below research/outputs. HTTP reads are limited to
version, loaded-model metadata, model description and cached service readiness.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TRIPLE = Path("/Users/v/other/neural-triple-reservoir")
MINIME = Path("/Users/v/other/minime")
OUT = ROOT / "research/outputs/2026-09-09-activation-knobs-audit"
SOURCES = {
    "coupled_server": (TRIPLE / "coupled_astrid_server.py", [(1016, 1036), (1088, 1167)]),
    "coupled_gateway": (TRIPLE / "coupled_http_gateway.py", [(435, 454)]),
    "embedding_and_feedback": (TRIPLE / "mlx_reservoir.py", [(164, 190), (268, 337)]),
    "installed_model": (TRIPLE / ".venv/lib/python3.12/site-packages/mlx_lm/models/gemma4_text.py", [(517, 608)]),
    "installed_generator": (TRIPLE / ".venv/lib/python3.12/site-packages/mlx_lm/generate.py", [(385, 470)]),
    "installed_sampler": (TRIPLE / ".venv/lib/python3.12/site-packages/mlx_lm/sample_utils.py", [(1, 125)]),
    "minime_provider": (MINIME / "minime_autonomy/runtime.py", [(54804, 54816), (54947, 54964)]),
    "previous_proposal": (ROOT / "proposals/2026-09-06-tranche1-generation-record-and-own-body.md", [(156, 164)]),
    "existing_timing_account": (TRIPLE / "docs/offline-coupling-replay.md", [(63, 75)]),
}

def read_http(url, body=None):
    try:
        request = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)
    except Exception as error:
        return {"unavailable": type(error).__name__}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "sources": {}}
    for name, (path, ranges) in SOURCES.items():
        raw = path.read_bytes()
        lines = raw.decode().splitlines()
        excerpt = "\n\n".join("\n".join(f"{i + 1}: {lines[i]}" for i in range(start - 1, min(end, len(lines)))) for start, end in ranges)
        destination = OUT / (name + ".txt")
        destination.write_text(excerpt + "\n")
        evidence["sources"][name] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                                    "excerpt": destination.name, "ranges": ranges}
    evidence["ollama_version"] = read_http("http://localhost:11434/api/version")
    described = read_http("http://localhost:11434/api/show", {"model": "gemma4:12b"})
    evidence["ollama_model"] = {k: described.get(k) for k in ("capabilities", "parameters", "details", "unavailable")}
    evidence["ollama_model"]["architecture"] = {k: v for k, v in described.get("model_info", {}).items()
                                                if any(s in k for s in ("context_length", "embedding_length", "block_count"))}
    evidence["coupled_readiness"] = read_http("http://localhost:8090/readyz")
    evidence["coupled_process"] = subprocess.run(["ps", "-p", "60333", "-o", "lstart=,args="],
                                                capture_output=True, text=True, timeout=5).stdout.strip()
    evidence["installed_mlx_lm"] = "0.31.3"
    metadata = TRIPLE / ".venv/lib/python3.12/site-packages/mlx_lm-0.31.3.dist-info/METADATA"
    assert "Version: 0.31.3" in metadata.read_text()
    evidence["metadata_sha256"] = hashlib.sha256(metadata.read_bytes()).hexdigest()
    evidence["scope"] = "Inspected source and installed dependency mechanics, read-only running-service metadata. No claim of activation-hook implementation, no generated responses, no mutated live state."
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "source_files": len(SOURCES),
                      "ollama_version": evidence["ollama_version"], "installed_mlx_lm": evidence["installed_mlx_lm"]}, indent=2))

if __name__ == "__main__":
    main()
