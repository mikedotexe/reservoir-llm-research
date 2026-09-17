"""Explicit retained inputs for the maintained S-007 daily pipeline.

Only manifest-declared local files are read. Paths embedded in captured records
are provenance strings and are never followed. Historical packet code is not run.
"""
from __future__ import annotations
import copy
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from reservoir_research.study_capture import encoded, sha, epoch

class DailyError(ValueError):
    """Invalid or incomplete retained research evidence."""

def require(condition, message="Evidence validation failed"):
    if not condition:
        raise DailyError(str(message))

def checked_call(function, *args, **kwargs):
    # Historical shared evidence helpers use assertions. Never silently disable them.
    require(not sys.flags.optimize, "Daily evidence verification requires Python without -O.")
    try:
        return function(*args, **kwargs)
    except DailyError:
        raise
    except (AssertionError, KeyError, IndexError, TypeError, StopIteration, UnicodeError, json.JSONDecodeError) as exc:
        raise DailyError(f"{function.__name__}: invalid or missing evidence ({exc})") from exc

PACKET_NAMES = ("capture.json", "supplement.json", "era-supplement.json",
                "catchup-era.json", "catchup-activation.json", "new-era.json",
                "new-era-validation.json", "interface-era.json")
BINDING_NAMES = ("source-bindings.json", "catchup-bindings.json", "new-era-bindings.json")
REQUIRED_NAMES = PACKET_NAMES + BINDING_NAMES + ("protocol.json", "tracking-before.json")
LEGACY_HISTORY = ("2026-09-08-source-study-fidelity",
                  "2026-09-09-source-study-fidelity-day1",
                  "2026-09-10-source-study-fidelity-day2")
MAX_INPUT_BYTES = 512 * 1024 * 1024

def safe_file(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative, "Empty input path")
    parts = PurePosixPath(relative)
    require(not parts.is_absolute() and ".." not in parts.parts and "\\" not in relative,
            f"Input must be a relative path inside the declared data root: {relative}")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), f"Missing or escaping input: {relative}")
    return path

def checked_bytes(path: Path, definition: dict) -> bytes:
    require(path.stat().st_size <= MAX_INPUT_BYTES, f"Input exceeds 512 MiB: {path.name}")
    raw = path.read_bytes()
    require(isinstance(definition.get("sha256"), str) and re.fullmatch("[a-f0-9]{64}", definition["sha256"]),
            f"Invalid SHA-256: {path.name}")
    require(sha(raw) == definition["sha256"], f"Input hash differs: {path.name}")
    require(len(raw) == definition.get("bytes"), f"Input length differs: {path.name}")
    return raw

@dataclass
class Packet:
    manifest: dict
    root: Path
    documents: dict[str, bytes]
    manifest_sha256: str
    history_counts: dict[str, int]

    def raw(self, name: str) -> bytes:
        require(name in self.documents, f"Missing declared input: {name}")
        return self.documents[name]

    def json(self, name: str) -> Any:
        try:
            return json.loads(self.raw(name))
        except (ValueError, UnicodeError) as exc:
            raise DailyError(f"Invalid JSON in {name}: {exc}") from exc

    def replaced(self, name: str, value: Any) -> "Packet":
        """Memory-only evidence negative control; original files are untouched."""
        result = copy.copy(self)
        result.documents = dict(self.documents)
        result.documents[name] = encoded(value)
        return result

    @property
    def era_definitions(self):
        return self.manifest["era_definitions"]

    @property
    def legacy_history(self):
        return {name: self.history_counts[name] for name in LEGACY_HISTORY
                if name in self.history_counts}

def _load_packet(manifest_path: Path, data_root: Path | None = None) -> Packet:
    require(not sys.flags.optimize, "Daily evidence verification requires Python without -O.")
    raw = Path(manifest_path).read_bytes()
    manifest = json.loads(raw)
    require(manifest.get("schema") == "s007-daily-inputs-v1", "Unsupported daily input manifest")
    require(manifest.get("report_schema") == "source_study_fidelity_daily_v6", "Unsupported report semantics")
    root = (data_root or Path(manifest_path).parent).expanduser().resolve()
    inputs = manifest.get("inputs", {})
    require(isinstance(inputs, dict), "Manifest inputs must be an object")
    require(set(REQUIRED_NAMES) <= set(inputs), "Required daily inputs are missing")
    require(set(inputs) <= set(REQUIRED_NAMES) | {"claim-annotations.json"}, "Unknown daily input name")
    definitions = manifest.get("era_definitions")
    require(isinstance(definitions, list) and definitions, "Era definitions must be nonempty")
    require(sha(encoded(definitions)) == manifest.get("era_definitions_sha256"), "Era definition hash differs")
    documents = {name: checked_bytes(safe_file(root, item["path"]), item) for name, item in inputs.items()}
    protocol = json.loads(documents["protocol.json"])
    capture = json.loads(documents["capture.json"])
    require(epoch(protocol["since"]) == epoch(capture["selection"]["since"])
            and epoch(protocol["until_exclusive"]) == epoch(capture["selection"]["until_exclusive"]),
            "Capture window differs from the frozen protocol")
    require(epoch(protocol["since"]) < epoch(protocol["until_exclusive"]), "Empty or reversed protocol window")
    require(protocol.get("ledger_sha256") == sha(documents["tracking-before.json"]),
            "Ledger-before hash differs from the frozen protocol")
    history_counts = {}
    for history in manifest.get("history", []):
        name = history["id"]
        require(name not in history_counts, f"Duplicate historical packet: {name}")
        path = safe_file(root, history["path"])
        old_manifest = json.loads(checked_bytes(path, history))
        require(isinstance(old_manifest, dict), f"Invalid historical manifest: {name}")
        for relative, digest in old_manifest.items():
            retained = safe_file(path.parent, relative)
            require(sha(retained.read_bytes()) == digest, f"Historical evidence differs: {name}/{relative}")
        history_counts[name] = len(old_manifest)
    require(set(LEGACY_HISTORY) <= set(history_counts), "Baseline, day1 and day2 lineage must be declared")
    return Packet(manifest, root, documents, sha(raw), history_counts)

def make_manifest(packet_dir: Path, data_root: Path, history: list[Path], era_definitions: list[dict]) -> dict:
    root = data_root.expanduser().resolve()
    def describe(path):
        path = path.expanduser().resolve()
        require(path.is_relative_to(root) and path.is_file(), f"Input is outside data root: {path}")
        raw = path.read_bytes()
        return {"path": path.relative_to(root).as_posix(), "sha256": sha(raw), "bytes": len(raw)}
    inputs = {name: describe(packet_dir / name) for name in REQUIRED_NAMES}
    if (packet_dir / "claim-annotations.json").exists():
        inputs["claim-annotations.json"] = describe(packet_dir / "claim-annotations.json")
    lineage = [dict(id=p.name, **describe(p / "packet-manifest.json")) for p in history]
    return dict(schema="s007-daily-inputs-v1", report_schema="source_study_fidelity_daily_v6",
                inputs=inputs, history=lineage, era_definitions=era_definitions,
                era_definitions_sha256=sha(encoded(era_definitions)),
                limits="Explicit retained files only; source paths within records are provenance and are never read.")

def write_new_json(path: Path, value: Any):
    with path.open("xb") as stream:
        stream.write(encoded(value))
    path.chmod(0o600)

def load_packet(manifest_path: Path, data_root: Path | None = None) -> Packet:
    return checked_call(_load_packet, manifest_path, data_root)
