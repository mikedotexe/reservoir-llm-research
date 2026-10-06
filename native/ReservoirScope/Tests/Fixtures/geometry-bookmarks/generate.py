#!/usr/bin/env python3
"""Build deterministic synthetic viewer fixtures without any producer or live input.

This is a wire-format fixture constructor, not an interoperability test. It does
not invoke the shared reader, a Minime adapter, a model, or any external process.
"""

import argparse
import hashlib
import json
from pathlib import Path


FORMAT = "question-geometry-v1"
OWNERS = ("astrid", "minime")
EPOCH_MS = 1_790_000_000_000
SOURCE_LABEL = "minime/workspace/runtime/esn_activation_trace_v1.json"
LIMITS = (
    "GENERATED SYNTHETIC TEST DATA. No live source was read and no producer or "
    "adapter was executed. Owner and source fields are schema labels. Hashes "
    "check bytes, not origin; these fixtures are not interoperability evidence. "
    "Mean-state RMS compares coordinates, not experience or mechanism. Recorder "
    "gaps are explicit; boot and node-layout identity remain unverified."
)


def compact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":"))


def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def document(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                       indent=2) + "\n").encode("utf-8")


def capture(second):
    # Small rational coordinates avoid platform-dependent transcendental math.
    # Every observation coordinate is 0.1 above its baseline coordinate.
    values = [((node % 17) - 8 + (2 if second else 0)) / 20 for node in range(128)]
    start = 20_000 if second else 10_000
    frames = [dict(t_ms=start + offset, wall_clock_unix_ms=EPOCH_MS + start + offset,
                   activations=values) for offset in (0, 1_000, 3_000)]
    # The digest binds an in-memory synthetic trace; SOURCE_LABEL is never opened.
    trace = dict(policy="esn_activation_trace_v1", reservoir_dim=128,
                 sample_interval_ms=1_000, retained_secs=180,
                 updated_at_unix_ms=frames[-1]["wall_clock_unix_ms"],
                 frames=[dict(frame, summary=dict(finite_fraction=1.0)) for frame in frames])
    return dict(source_sha256=sha(compact(trace)),
                captured_at_unix_ms=frames[-1]["wall_clock_unix_ms"] + 1_000,
                requested_seconds=10, source=SOURCE_LABEL,
                scope="native_esn_128_activations",
                identity="boot_and_node_layout_unverified", frames=frames)


def packet(owner):
    records = []

    def append(request_id, operation, entry):
        previous = records[-1]["id"] if records else "empty"
        request_id = "synthetic-" + owner + "-" + request_id
        request = dict(being=owner, question="q1", expected_head=previous,
                       request_id=request_id, operation=operation)
        body_json = compact(entry)
        request_sha256 = sha(compact(request))
        identity = sha("\n".join((previous, sha(request_id), request_sha256, sha(body_json))))
        records.append(dict(id=identity, previous=previous, request_id=request_id,
                            request_sha256=request_sha256, body_json=body_json))
        return identity

    note = "Synthetic chosen interval A."
    baseline = append("a", dict(kind="capture", seconds=10, note=note),
                      dict(kind="capture", snapshot=capture(False), note=note))
    expectation = "Synthetic expectation: mean-state RMS distance at most 0.05."
    prediction = append("prediction",
                        dict(kind="predict", baseline=baseline, maximum_rms_distance=0.05,
                             expectation=expectation),
                        dict(kind="prediction", baseline=baseline, maximum_rms_distance=0.05,
                             expectation=expectation))
    note = "Synthetic chosen interval B."
    observation = append("b", dict(kind="capture", seconds=10, note=note),
                         dict(kind="capture", snapshot=capture(True), note=note))
    comparison = append("comparison", dict(kind="compare", prediction=prediction,
                                           observation=observation),
                        dict(kind="comparison", prediction=prediction, observation=observation,
                             recipe="mean-state-rms-distance-v1", rms_distance=0.1,
                             threshold_met=False))
    revision = ("Synthetic revision: the numerical threshold was not met; "
                "mechanism and experience remain unknown.")
    append("revision", dict(kind="revise", target=comparison, text=revision),
           dict(kind="revision", target=comparison, text=revision))
    body_json = compact(dict(format=FORMAT, owner=owner, question_id="q1",
                             question="Synthetic question: will the mean state remain nearby?",
                             history=dict(owner=owner, records=records), limits=LIMITS))
    return document(dict(format=FORMAT, body_sha256=sha(body_json), body_json=body_json))


def outputs():
    files = {owner + "-synthetic-geometry.json": packet(owner) for owner in OWNERS}
    provenance = dict(
        format="reservoir-scope.synthetic-geometry-fixtures.v1",
        evidence_kind="generated synthetic viewer fixtures; not producer interoperability",
        generator=dict(file="generate.py", sha256=sha(Path(__file__).read_bytes()),
                       dependencies="Python 3 standard library only; no external inputs"),
        design_references=[
            "native/ReservoirScope/Sources/ReservoirScope/GeometryBookmark.swift",
            "native/ReservoirScope/Tests/geometry_bookmark_workflow.py",
        ],
        wire_format=FORMAT,
        recipe=dict(records_per_owner=5, captures_per_owner=2, frames_per_capture=3,
                    coordinates_per_frame=128, frame_offsets_ms=[0, 1_000, 3_000],
                    recorder_start_ms=[10_000, 20_000], wall_clock_epoch_ms=EPOCH_MS,
                    gaps_per_capture=1, requested_seconds=10,
                    baseline_coordinate="((node_index % 17) - 8) / 20",
                    observation_coordinate="((node_index % 17) - 6) / 20",
                    expected_rms_distance=0.1, maximum_rms_distance=0.05,
                    expected_threshold_met=False),
        hash_scope=dict(
            file="SHA-256 of exact UTF-8 file bytes, including final newline",
            canonical_json="UTF-8, sorted keys, compact separators, no NaN",
            source="SHA-256 of the synthetic trace built by capture(); source label is never opened",
            request="SHA-256 of the synthetic request built by append(); no operation is executed",
            record="SHA-256 of previous, request-ID hash, request hash and body hash joined by LF",
        ),
        fixtures={name: dict(owner=owner, bytes=len(files[name]), sha256=sha(files[name]))
                  for owner in OWNERS for name in [owner + "-synthetic-geometry.json"]},
    )
    files["provenance.json"] = document(provenance)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Verify adjacent retained fixtures and provenance without writing")
    mode.add_argument("--out", type=Path,
                      help="Create fixtures and provenance in a new directory")
    args = parser.parse_args()
    files = outputs()
    if args.check:
        directory = Path(__file__).resolve().parent
        for name, expected in files.items():
            path = directory / name
            if not path.is_file() or path.read_bytes() != expected:
                parser.exit(1, "Synthetic fixture differs or is missing: " + str(path) + "\n")
        status = "verified"
    else:
        directory = args.out
        directory.mkdir(parents=True, exist_ok=False)
        for name, data in files.items():
            (directory / name).write_bytes(data)
        status = "generated"
    print(json.dumps(dict(status=status, evidence_kind="synthetic viewer fixtures",
                          fixtures=2, records=10,
                          sha256={name: sha(data) for name, data in files.items()}), sort_keys=True))


if __name__ == "__main__":
    main()
