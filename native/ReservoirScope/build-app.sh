#!/bin/zsh
# Build only the steward-side viewer. Never writes into a live-system directory.
set -euo pipefail
task_dir="${0:A:h}"
repo_dir="${task_dir:h:h}"
native_cache="${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/ReservoirScope-build"
resource_dir="$task_dir/Sources/ReservoirScope/Resources"
mkdir -p "$resource_dir"
cp "$repo_dir/visualizations/reservoir-3d/data.json" "$resource_dir/data.json"
cp "$repo_dir/visualizations/reservoir-3d/state-geometry.json" "$resource_dir/state-geometry.json"
native_response="$repo_dir/research/outputs/2026-09-07-native-state-actions/native-action-response.json"
if [[ -f "$native_response" ]]; then
  cp "$native_response" "$resource_dir/native-action-response.json"
fi
staged_package="$native_cache/package"
mkdir -p "$staged_package/Sources"
cp "$task_dir/Package.swift" "$staged_package/Package.swift"
cp -R "$task_dir/Sources/ReservoirScope" "$staged_package/Sources/"
cd "$native_cache"
mkdir -p "$native_cache/build"
swiftc -parse-as-library -swift-version 5 -O \
  -target "$(uname -m)-apple-macosx14.0" \
  "$staged_package"/Sources/ReservoirScope/*.swift \
  -o "$native_cache/build/ReservoirScope"
install_dir="$native_cache/current"
staging_dir="$(mktemp -d "$native_cache/app-stage.XXXXXX")"
app_dir="$staging_dir/Reservoir Scope.app"
mkdir -p "$app_dir/Contents/MacOS" "$app_dir/Contents/Resources"
cp -X "$native_cache/build/ReservoirScope" "$app_dir/Contents/MacOS/ReservoirScope"
cp -X "$resource_dir/data.json" "$resource_dir/state-geometry.json" "$resource_dir/state-replay.json" "$resource_dir/state-replay.bin" "$resource_dir/state-response.json" "$app_dir/Contents/Resources/"
if [[ -f "$resource_dir/native-action-response.json" ]]; then
  cp -X "$resource_dir/native-action-response.json" "$app_dir/Contents/Resources/"
fi
cat > "$app_dir/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Reservoir Scope</string>
<key>CFBundleDisplayName</key><string>Reservoir Scope</string>
<key>CFBundleIdentifier</key><string>research.reservoir.scope</string>
<key>CFBundleExecutable</key><string>ReservoirScope</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.7.1</string>
<key>CFBundleVersion</key><string>10</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --deep --sign - "$app_dir"
codesign --verify --deep --strict "$app_dir"
mkdir -p "$install_dir"
if [[ -d "$install_dir/Reservoir Scope.app" ]]; then
  previous_dir="$(mktemp -d "$native_cache/previous-build.XXXXXX")"
  mv "$install_dir/Reservoir Scope.app" "$previous_dir/Reservoir Scope.app"
fi
# Rename complete bundles; never overwrite a running executable in place.
mv "$app_dir" "$install_dir/Reservoir Scope.app"
rmdir "$staging_dir"
print -r -- "$install_dir/Reservoir Scope.app"
