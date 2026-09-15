#!/usr/bin/env python3
"""Replay the exact historical marker scanner before/after 6344ba25e9d3.

Research-only synthetic correctness comparison, not a full provider replay or
natural incidence estimate. Extracts contiguous unchanged source spans from Git;
never imports a runtime or writes to a sibling repository. Needs installed rustc.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "6344ba25e9d33ea051034a866f04d3fba25b3d6a"
SOURCE = "capsules/spectral-bridge/src/llm/provider/dialogue_runtime.rs"
CONSTANTS = "capsules/spectral-bridge/src/llm/provider/fallback_contracts.rs"
MARKER = "<end_of_turn>"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=ROOT.parent / "astrid")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--replay", type=Path, help="Use retained before/after source files without Git access")
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / "research" / "outputs") or out.exists():
        p.error("Choose a new directory beneath research/outputs")
    rustc = shutil.which("rustc")
    if not rustc:
        p.error("An installed Rust compiler is required")
    out.mkdir(parents=True, mode=0o700)
    pairs = [("﹁", "﹂"), ("﹃", "﹄"), ("《", "》"), ("〖", "〗"),
             ("〘", "〙"), ("（", "）"), ("［", "］"), ("｛", "｝")]
    cases = [{"id": f"added_pair_{i+1}", "group": "targeted", "input": l+MARKER+r,
              "expected_after": l+MARKER+r} for i, (l, r) in enumerate(pairs)]
    cases.append({"id": "nested_three", "group": "targeted", "input": "﹁《（"+MARKER+"）》﹂",
                  "expected_after": "﹁《（"+MARKER+"）》﹂"})
    controls = [("ascii_quote", '"'+MARKER+'"', '"'+MARKER+'"'),
                ("curly_quote", "“"+MARKER+"”", "“"+MARKER+"”"),
                ("ascii_group", "["+MARKER+"]", "["+MARKER+"]"),
                ("relation", MARKER+" manifests", MARKER+" manifests"),
                ("bare", MARKER, ""),
                ("mismatched", "《"+MARKER+"）", "《）"),
                ("unlisted_pair", "⦃"+MARKER+"⦄", "⦃⦄"),
                ("ordinary_unicode", "A plain λ and 日本語", "A plain λ and 日本語")]
    cases.extend({"id": name, "group": "control", "input": text, "expected_after": expected}
                 for name, text, expected in controls)
    (out / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2)+"\n")
    source_receipts = {}
    results = {}
    for label, revision in [("before", COMMIT+"^"), ("after", COMMIT)]:
        def source(path, suffix):
            if a.replay:
                raw = (a.replay / f"{label}-{suffix}.rs").read_bytes()
            else:
                raw = subprocess.check_output(["git", "--no-optional-locks", "-C", str(a.repo),
                                               "show", revision+":"+path], timeout=60)
            (out / f"{label}-{suffix}.rs").write_bytes(raw)
            return raw
        raw = source(SOURCE, "full")
        constant_raw = source(CONSTANTS, "constants")
        expected = {"before":"f7c0570ce495b1978d9b6f588cba6ecb00a93b1573316bc22752e6e10d47f20a",
                    "after":"8f3c16091b532cba5879726de058ba16af2469f3cea8698d4ece1016fc04f2af"}
        assert digest(raw) == expected[label], "Historical source identity mismatch"
        assert digest(constant_raw) == "7f4cf2038ef66086a4c33279ebd84116d3a7aa1d34cc1f4202576fd47d03039f"
        text = raw.decode()
        start = text.index("#[derive(Debug, Clone, Copy)]\nstruct KnownModelControlMarkerMatch")
        end = text.index("fn control_marker_placement_counts(", start)
        span = text[start:end]
        c = constant_raw.decode()
        cs = c.index("const KNOWN_MODEL_CONTROL_MARKERS:")
        ce = c.index("];", cs)+2
        constant = c[cs:ce]
        source_receipts[label] = {"revision": revision, "full_sha256": digest(raw),
            "constant_file_sha256": digest(constant_raw), "scanner_span_sha256": digest(span.encode()),
            "scanner_start_line": text[:start].count("\n")+1,
            "scanner_end_line": text[:end].count("\n"),
            "constant_span_sha256": digest(constant.encode())}
        inputs = ",\n".join(json.dumps(x["input"], ensure_ascii=False) for x in cases)
        harness = '#![allow(dead_code)]\n'+constant+'\n'+span+'\nfn main() {\n'
        harness += 'for (i, text) in ['+inputs+'].iter().enumerate() {\n'
        harness += 'let (out, matches) = scan_known_model_control_markers(text);\n'
        harness += 'let hex: String = out.as_bytes().iter().map(|b| format!("{:02x}", b)).collect();\n'
        harness += 'println!("{}\\t{}\\t{}", i, matches.len(), hex);\n}\n}\n'
        src = out / f"{label}-harness.rs"
        binary = out / f"{label}-scanner"
        src.write_text(harness)
        # macOS may stall launching an executable from the SMB-mounted research
        # volume. Execute only our temporary local copy; retain and hash its bytes.
        with tempfile.TemporaryDirectory(prefix="flywheel-scanner-") as tmp:
            local_src = Path(tmp) / "harness.rs"
            local_binary = Path(tmp) / "scanner"
            local_src.write_text(harness)
            build = subprocess.run([rustc, "--edition=2021", str(local_src), "-o", str(local_binary)],
                                   capture_output=True, text=True, timeout=60)
            (out / f"{label}-build.txt").write_text(build.stdout+build.stderr)
            build.check_returncode()
            executable_bytes = local_binary.read_bytes()
            binary.write_bytes(executable_bytes)
            output = subprocess.check_output([str(local_binary)], cwd=tmp, timeout=180).decode()
            assert local_binary.read_bytes() == executable_bytes == binary.read_bytes()
        (out / f"{label}-output.tsv").write_text(output)
        rows = []
        for line in output.splitlines():
            i, count, hex_value = line.split("\t")
            rows.append({"id": cases[int(i)]["id"], "matches": int(count),
                         "output": bytes.fromhex(hex_value).decode()})
        assert len(rows) == len(cases)
        results[label] = rows
        source_receipts[label]["binary_sha256"] = digest(binary.read_bytes())
    assert source_receipts["before"]["constant_span_sha256"] == source_receipts["after"]["constant_span_sha256"]
    summary = {"targeted_n": 9, "control_n": 8,
        "targeted_exact_preserved_before": sum(results["before"][i]["output"] == cases[i]["input"] for i in range(9)),
        "targeted_exact_preserved_after": sum(results["after"][i]["output"] == cases[i]["input"] for i in range(9)),
        "controls_identical": sum(results["before"][i] == results["after"][i] for i in range(9,17)),
        "all_after_match_expected": all(results["after"][i]["output"] == c["expected_after"] for i,c in enumerate(cases))}
    assert summary == {"targeted_n":9, "control_n":8, "targeted_exact_preserved_before":0,
                       "targeted_exact_preserved_after":9, "controls_identical":8,
                       "all_after_match_expected":True}, summary
    data = {"commit":COMMIT, "source":SOURCE, "rustc":subprocess.check_output([rustc,"--version"]).decode().strip(),
            "scope":"Exact contiguous scanner + exact unchanged marker constant; synthetic cases selected after reading the diff; excludes receipt assembly, full provider, deployment and natural incidence",
            "source_receipts":source_receipts,"cases":cases,"results":results,"summary":summary}
    (out / "result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
    for f in out.iterdir():
        f.chmod(0o700 if f.name.endswith("-scanner") else 0o600)
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
