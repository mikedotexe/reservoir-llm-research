#!/usr/bin/env bash
# Production offscreen renderer correctness and PNG fixtures; no live sources/windows.
# Usage: check-topographic-renderer.sh OUTPUT_DIR [PRISTINE_SOURCE_DIR]
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_output_dir="${1:-${TMPDIR:-/tmp}/reservoir-topographic-renderer}"
task_previous_dir="${2:-}"
task_build_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-topographic-build.XXXXXX")"
trap 'rm -rf -- "$task_build_dir"' EXIT
mkdir -p "$task_output_dir"
if [[ -n "$task_previous_dir" ]]; then
  mkdir -p "$task_output_dir/pristine"
  cat "$task_source_dir/ResourceBundle.swift" \
      "$task_source_dir/Evidence.swift" \
      "$task_previous_dir/StateSurface.swift" \
      "$task_previous_dir/StateSurfaceScene.swift" \
      "$task_source_dir/StateSurfaceProfiling.swift" \
      "$task_native_dir/Tests/TopographicRendererChecks.swift" > "$task_build_dir/pristine.swift"
  xcrun swiftc -O -swift-version 6 -D TOPOGRAPHY_BASELINE "$task_build_dir/pristine.swift" -o "$task_build_dir/pristine"
  "$task_build_dir/pristine" "$task_source_dir/Resources" "$task_output_dir/pristine"
fi
cat "$task_source_dir/ResourceBundle.swift" \
    "$task_source_dir/Evidence.swift" \
    "$task_source_dir/StateSurface.swift" \
    "$task_source_dir/StateSurfaceScene.swift" \
    "$task_source_dir/StateSurfaceProfiling.swift" \
    "$task_native_dir/Tests/TopographicRendererChecks.swift" > "$task_build_dir/checks.swift"
xcrun swiftc -O -swift-version 6 "$task_build_dir/checks.swift" -o "$task_build_dir/checks"
if [[ -n "$task_previous_dir" ]]; then
  "$task_build_dir/checks" "$task_source_dir/Resources" "$task_output_dir" "$task_output_dir/pristine"
else
  "$task_build_dir/checks" "$task_source_dir/Resources" "$task_output_dir"
fi
python3 - "$task_native_dir" "$task_build_dir/checks.swift" "$task_output_dir/receipt.json" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
native, checked, receipt_path = map(Path, sys.argv[1:])
receipt = json.loads(receipt_path.read_text())
receipt['compiled_source_sha256'] = hashlib.sha256(checked.read_bytes()).hexdigest()
receipt['source_sha256'] = {
    str(path): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in [native / 'Sources/ReservoirScope/StateSurface.swift',
                 native / 'Sources/ReservoirScope/StateSurfaceScene.swift',
                 native / 'Tests/TopographicRendererChecks.swift',
                 native / 'check-topographic-renderer.sh']
}
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
PY
