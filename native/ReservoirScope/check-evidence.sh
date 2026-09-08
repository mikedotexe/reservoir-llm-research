#!/usr/bin/env bash
# Reproducible native evidence checks. Uses bundled telemetry and a temporary
# synthetic health fixture; never opens the beings' files or databases.
set -euo pipefail

task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_source_dir="$task_native_dir/Sources/ReservoirScope"
task_check_dir="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-native-checks.XXXXXX")"
trap 'rm -rf -- "$task_check_dir"' EXIT

task_bundle_dir="$task_check_dir/Fixture.bundle"
mkdir -p "$task_bundle_dir/Contents/Resources/Resources"
cp "$task_source_dir/Resources/data.json" "$task_bundle_dir/Contents/Resources/Resources/data.json"
cp "$task_source_dir/Resources/state-geometry.json" "$task_bundle_dir/Contents/Resources/Resources/state-geometry.json"
cat > "$task_bundle_dir/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>org.reservoir-research.evidence-fixture</string>
<key>CFBundleName</key><string>Reservoir evidence fixture</string>
<key>CFBundlePackageType</key><string>BNDL</string>
</dict></plist>
PLIST

# The interpreter avoids the long first-launch delay observed for newly linked
# local executables. It still checks Swift 6 isolation and runs the real models.
cat "$task_source_dir/Evidence.swift" \
    "$task_source_dir/LiveTelemetry.swift" \
    "$task_source_dir/LiveState.swift" \
    "$task_source_dir/ReferenceZones.swift" \
    "$task_source_dir/ReplayClock.swift" \
    "$task_native_dir/Tests/ReferenceZoneChecks.swift" \
    "$task_native_dir/Tests/LiveStateChecks.swift" \
    "$task_native_dir/Tests/EvidenceFixtureChecks.swift" > "$task_check_dir/checks.swift"
xcrun swift -swift-version 6 "$task_check_dir/checks.swift" \
    "$task_bundle_dir" "$task_check_dir/health.json"
