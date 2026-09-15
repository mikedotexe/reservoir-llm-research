#!/usr/bin/env python3
"""Independent, offline check of the S-006 provider observation qualification."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def framed(parts):
    encoded = len(parts).to_bytes(8, "big")
    for part in parts:
        encoded += len(part).to_bytes(8, "big") + part
    return sha(encoded)


def read(path):
    return json.loads(path.read_text())


def verify(root):
    declared = read(root / "summary.json")
    fixtures = {case["name"]: case for case in read(root / "fixtures.json")}
    total_attempts = 0
    total_events = 0
    raw_files = set()
    statuses = {}
    accepted = 0
    decisions_rejected = 0
    paired_overheads = []
    file_manifest = []
    assert declared["compared_with_exact_baseline"]
    for row in declared["cases"]:
        case = fixtures[row["case"]]
        prefix = f"{row['provider']}-{row['case']}"
        arms = {mode: read(root / f"{prefix}-{mode}" / "result.json")
                for mode in ("baseline", "disabled", "enabled", "fault")}
        for mode, result in arms.items():
            for key in ("provider_text", "accepted", "model"):
                assert result[key] == arms["baseline"][key], (prefix, mode, key)
        if not case.get("delay") and not case.get("verified"):
            paired_overheads.append(arms["enabled"]["elapsed_ms"] - arms["disabled"]["elapsed_ms"])
        enabled = root / f"{prefix}-enabled"
        evidence = enabled / "evidence"
        events = [read(p) for p in (evidence / "events").glob("*.json")]
        dispatches = {e["attempt_id"]: e for e in events if e["stage"] == "dispatch_started"}
        outcomes = {e["attempt_id"]: e for e in events if e["stage"] == "provider_outcome"}
        decisions = [e for e in events if e["stage"] == "dialogue_decision"]
        links = arms["enabled"]["observation"]["attempts"]
        assert len(decisions) == 1
        assert len(outcomes) == row["requests"] == len(links)
        assert set(dispatches) == set(outcomes) == {link["attempt_id"] for link in links}
        total_attempts += len(outcomes)
        total_events += len(events)
        for mode in arms:
            assert len(read(root / f"{prefix}-{mode}" / "requests.json")) == len(outcomes)
        for key, outcome in outcomes.items():
            assert outcome["generation_id"] == dispatches[key]["generation_id"] == decisions[0]["generation_id"]
            assert outcome["request_sha256"] == dispatches[key]["request_sha256"]
            assert outcome["release_before"] == outcome["release_after"] == dispatches[key]["release_before"]
            assert outcome["raw_response_stage"] == "parsed_message_content_before_cleanup"
            statuses[outcome["outcome"]] = statuses.get(outcome["outcome"], 0) + 1
            if "raw_response_sha256" in outcome:
                raw = case["raw"].encode()
                assert outcome["raw_response_sha256"] == sha(raw)
                if outcome.get("cleanup_report"):
                    report = outcome["cleanup_report"]
                    assert report["original_output_sha256"] == framed([raw])
                    assert report["observed_total"] == outcome["marker_observed_total"]
                    assert len(report["context_receipts"]) <= 32
                    assert len(report["context_receipts"]) + report["context_receipts_omitted"] == report["observed_total"]
                    for receipt in report["context_receipts"]:
                        assert raw[receipt["start_byte"]:receipt["end_byte"]].decode() == receipt["marker"]
                    if report["context_receipts_omitted"]:
                        # This frozen cap fixture contains forty bare identical markers.
                        assert row["case"] == "receipt_cap"
                        assert report["removed_total"] == 40
                        assert report["preserved_explicit_reference_total"] == 0
                        cleaned = raw.replace(b"<end_of_turn>", b"")
                    else:
                        cleaned = raw
                        for receipt in sorted(report["context_receipts"], key=lambda r: r["start_byte"], reverse=True):
                            if not receipt["preserved"]:
                                cleaned = cleaned[:receipt["start_byte"]] + cleaned[receipt["end_byte"]:]
                    assert report["sanitized_output_sha256"] == framed([cleaned])
                else:
                    assert outcome["marker_observed_total"] == 0
                    cleaned = raw
                assert outcome["normalized_output_sha256"] == sha(cleaned.decode().strip().encode())
                assert outcome["normalized_output_stage"] == "marker_cleanup_then_trim"
            else:
                assert outcome["marker_observed_total"] is None
            if "raw_artifact" in outcome:
                path = evidence / outcome["raw_artifact"]
                assert path.suffix == ".txt" and path.stem == sha(path.read_bytes())
                assert path.read_bytes() == case["raw"].encode()
                assert path.stat().st_size <= 262144
                raw_files.add(str(path.relative_to(root)))
            if outcome["outcome"] == "provider_returned":
                assert outcome["provider_output_sha256"] == sha(arms["enabled"]["provider_text"].encode())
        chosen = arms["enabled"]["accepted"]
        assert decisions[0]["decision"] == ("accepted" if chosen is not None else "not_accepted")
        expected_hash = sha(chosen.encode()) if chosen is not None else None
        assert decisions[0]["accepted_output_sha256"] == expected_hash
        if chosen is not None:
            accepted += 1
        else:
            decisions_rejected += 1
        assert not (root / f"{prefix}-disabled/evidence").exists()
        assert all(link["recording_status"] == "recording_failed" for link in arms["fault"]["observation"]["attempts"])
        for path in evidence.rglob("*"):
            assert not path.is_symlink()
            assert path.stat().st_mode & 0o777 == (0o700 if path.is_dir() else 0o600)
            if path.is_file():
                file_manifest.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())})
    assert total_attempts == sum(row["requests"] for row in declared["cases"])
    import statistics
    return {
        "schema": "provider_observation_independent_verification_v1",
        "verified": True, "comparison_cases": len(declared["cases"]),
        "arms_per_case": 4, "physical_attempts_per_arm": total_attempts,
        "enabled_events": total_events, "distinct_raw_artifacts": len(raw_files),
        "accepted_dialogue_cases": accepted, "nonaccepted_dialogue_cases": decisions_rejected,
        "outcomes": statuses, "source_report_sha256": sha((root / "summary.json").read_bytes()),
        "evidence_bytes": sum(item["bytes"] for item in file_manifest),
        "paired_enabled_minus_disabled_ms": {"n": len(paired_overheads), "median": statistics.median(paired_overheads), "max": max(paired_overheads)},
        "files": sorted(file_manifest, key=lambda item: item["path"]),
        "scope": "synthetic frozen HTTP fixtures; not natural frequency, action execution, production latency or live benefit",
    }


def verify_completion(path):
    receipt = read(path)
    counts = {}
    for name, declared in receipt["functional_tests"].items():
        log = path.parent / name
        if not log.exists():
            log = path.parent / "qualification" / name
        assert sha(log.read_bytes()) == declared["sha256"]
        result = re.findall(r"test result: ok\. (\d+) passed; (\d+) failed;", log.read_text())[-1]
        assert int(result[1]) == 0
        counts[name] = int(result[0])
        assert counts[name] == declared["passed"]
    library = sum(counts[name] for name in ("final-functional.log", "final-default-path.log", "final-os-lifecycle.log"))
    assert library == receipt["functional_library_passed"]
    return {"functional_library_passed": library, "public_interface_contract_passed": counts["facade-contract.log"], "completion_sha256": sha(path.read_bytes())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--completion", type=Path)
    args = parser.parse_args()
    result = verify(args.root)
    if args.completion:
        result.update(verify_completion(args.completion))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))
