#!/bin/zsh
# Mirror viewer sources into the selected build cache; no compilation or install.
set -euo pipefail
task_source_dir="${1:?Pass the native source directory}"
task_staged_dir="${2:?Pass the staged package directory}"
mkdir -p "$task_staged_dir/Sources/ReservoirScope"
cp "$task_source_dir/Package.swift" "$task_staged_dir/Package.swift"
# A reused cache must not compile Swift files removed from the source checkout.
rsync -a --delete "$task_source_dir/Sources/ReservoirScope/" \
    "$task_staged_dir/Sources/ReservoirScope/"
