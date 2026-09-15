#!/usr/bin/env python3
"""Package the already-retained activation capture for the native state surface.

No live capture and no sibling reads: verifies the existing geometry export,
metadata and raw SHA-256 inside this research repository. Float32 bytes remain
unchanged. Rows retain their captured order; no row times or fill are assigned.
Uses only the Python standard library. --check verifies without writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import tempfile

REPO = Path(__file__).resolve().parents[1]
DEFAULT_GEOMETRY = REPO / "visualizations/reservoir-3d/state-geometry.json"
DEFAULT_OUTPUT = REPO / "native/ReservoirScope/Sources/ReservoirScope/Resources"


def local_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO.resolve()):
        raise ValueError(f"Only retained research files may be read or written: {path}")
    return resolved


def read_bounded(path: Path, maximum: int) -> bytes:
    with local_path(path).open("rb") as handle:
        data = handle.read(maximum + 1)
    if not data or len(data) > maximum:
        raise ValueError(f"Empty or oversized retained input: {path}")
    return data


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(geometry_path: Path) -> tuple[bytes, bytes]:
    geometry_raw = read_bounded(geometry_path, 2 * 1024 * 1024)
    geometry = json.loads(geometry_raw)
    if geometry["schema"] != "reservoir.state_geometry.v1":
        raise ValueError("Unsupported retained geometry schema")
    rows, dimensions = geometry["pca"]["rows"], geometry["pca"]["dimensions"]
    if type(rows) is not int or not 2 <= rows <= 1024 or dimensions != 128:
        raise ValueError("Expected 2–1024 retained rows of 128 coordinates")
    source = geometry["source"]
    raw = read_bounded(Path(source["files"]["states"]["snapshot_path"]), 1024 * 128 * 4)
    metadata_raw = read_bounded(Path(source["files"]["metadata"]["snapshot_path"]), 16 * 1024)
    metadata = json.loads(metadata_raw)
    if (digest(raw) != source["files"]["states"]["sha256"] or
            digest(metadata_raw) != source["files"]["metadata"]["sha256"] or metadata != source["meta"]):
        raise ValueError("Retained state or metadata hash/content mismatch")
    if (metadata["dtype"] != "<f4" or metadata["layout"] != "row_major" or
            metadata["esn_window_rows"] != rows or metadata["esn_window_cols"] != dimensions or
            len(raw) != rows * dimensions * 4):
        raise ValueError("Retained dimensions or encoding mismatch")
    if not all(math.isfinite(value) and -1 <= value <= 1 for (value,) in struct.iter_unpack("<f", raw)):
        raise ValueError("Retained state has non-finite or out-of-range activations")
    if (geometry["timing"]["row_order"] != "oldest_to_newest" or
            geometry["timing"]["per_row_timestamps_available"] is not False):
        raise ValueError("Unexpected retained timing contract")
    manifest = {
        "schema": "reservoir.state_replay.v1",
        "subject": "Minime native ESN retained activation coordinates",
        "dtype": "<f4", "layout": "row_major", "binary_file": "state-replay.bin",
        "rows": rows, "dimensions": dimensions, "byte_count": len(raw),
        "source_sha256": digest(raw), "geometry_sha256": digest(geometry_raw),
        "captured_at_utc": source.get("captured_at_utc"),
        "row_order": "oldest_to_newest", "per_row_timestamps_available": False,
        "paired_fill_available": False, "node_layout_id": None,
        "source_geometry": str(local_path(geometry_path).relative_to(REPO.resolve())),
        "source_snapshot": str(local_path(Path(source["files"]["states"]["snapshot_path"])).relative_to(REPO.resolve())),
        "provenance": "Same original bytes used to fit the frozen basis; capture time is an observation of the file, not a timestamp for any row.",
        "identity_limit": "Coordinate positions preserve recorded order. No authenticated node-layout, boot/session, successful-step identifier or per-row fill/controller join exists.",
        "reproduction": "python3 probes/reservoir_state_surface_replay.py",
    }
    return raw, (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode()


def atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw, manifest = prepare(args.geometry)
    output = local_path(args.output_dir)
    packaged_geometry = read_bounded(output / "state-geometry.json", 2 * 1024 * 1024)
    if digest(packaged_geometry) != json.loads(manifest)["geometry_sha256"]:
        raise ValueError("Packaged frozen geometry differs from the export being bound")
    files = {"state-replay.bin": raw, "state-replay.json": manifest}
    for name, data in files.items():
        if args.check:
            if read_bounded(output / name, max(len(data), 16 * 1024)) != data:
                raise ValueError(f"Packaged replay differs from retained input: {name}")
        else:
            atomic_write(output / name, data)
    print(json.dumps({"status": "verified" if args.check else "exported", "n_rows": len(raw) // (128 * 4),
                      "n_coordinates": 128, "raw_bytes": len(raw), "source_sha256": digest(raw),
                      "manifest_sha256": digest(manifest), "output_dir": str(output),
                      "per_row_time_available": False, "paired_fill_available": False}))


if __name__ == "__main__":
    main()
