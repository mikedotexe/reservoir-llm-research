#!/usr/bin/env bash
# Exercise the production staging helper using temporary files only.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
python3 - "$task_native_dir/stage-sources.sh" <<'PY'
from pathlib import Path
import subprocess
import sys
import tempfile

helper = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="reservoir-source-staging-") as folder:
    root = Path(folder)
    source, staged = root / "source", root / "staged"
    source_files = source / "Sources/ReservoirScope"
    staged_files = staged / "Sources/ReservoirScope"
    for path in [source_files / "Resources", staged_files / "Resources"]:
        path.mkdir(parents=True)
    (source / "Package.swift").write_text("// fixture manifest\n")
    (source_files / "Current.swift").write_text("// current source\n")
    (source_files / "Resources/example.json").write_text('{"fixture":1}\n')
    (staged_files / "Removed.swift").write_text("// stale compiled source\n")
    (staged_files / "Resources/removed.json").write_text("{}\n")
    (staged / "unrelated-output").write_text("preserve this\n")

    def snapshot(directory):
        return {str(path.relative_to(directory)): path.read_bytes()
                for path in directory.rglob("*") if path.is_file()}

    def stage():
        subprocess.run(["zsh", str(helper), str(source), str(staged)], check=True)

    stage()
    assert snapshot(source_files) == snapshot(staged_files), "Staged sources/resources differ"
    assert not (staged_files / "Removed.swift").exists(), "Removed Swift source survived"
    assert not (staged_files / "Resources/removed.json").exists(), "Removed resource survived"
    assert (staged / "Package.swift").read_bytes() == (source / "Package.swift").read_bytes()
    assert (staged / "unrelated-output").read_text() == "preserve this\n"

    (source_files / "Current.swift").unlink()
    (source_files / "Replacement.swift").write_text("// replacement source\n")
    stage()
    assert snapshot(source_files) == snapshot(staged_files), "Second stage retained old sources"
    stage()
    assert snapshot(source_files) == snapshot(staged_files), "Repeated stage changed contents"
    print("7 source-staging checks passed; temporary fixtures only, no build or install.")
PY
