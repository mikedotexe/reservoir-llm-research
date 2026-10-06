#!/bin/zsh
# Build only the steward-side viewer from frozen staged inputs.
set -euo pipefail
task_dir="${0:A:h}"
repo_dir="${task_dir:h:h}"
native_cache="${RESERVOIR_SCOPE_BUILD_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research/ReservoirScope-build}"
mkdir -p "$native_cache"
# Every invocation owns its immutable source snapshot and compiler outputs.
build_root="$(mktemp -d "$native_cache/build-0.15.XXXXXX")"
staged_root="$build_root/staged-repo"
staged_native="$staged_root/native/ReservoirScope"
core_cache="$build_root/essentials"
zsh "$task_dir/stage-sources.sh" "$task_dir" "$staged_root"
task_stage_sha="$(shasum -a 256 "$staged_root/staged-inputs.json" | cut -d " " -f 1)"
ESSENTIALS_BUILD_DIR="$core_cache" zsh "$staged_root/essentials/build.sh"
task_core_sha="$(shasum -a 256 "$core_cache/lib/libEssentialsCore.a" | cut -d " " -f 1)"
python3 "$staged_native/stage-package.py" verify-stage --destination "$staged_root"
mkdir -p "$build_root/build"
swiftc -parse-as-library -swift-version 5 -O \
  -target "$(uname -m)-apple-macosx14.0" \
  -I "$core_cache/lib" -L "$core_cache/lib" -lEssentialsCore -framework Accelerate \
  "$staged_native"/Sources/ReservoirScope/*.swift \
  -o "$build_root/build/ReservoirScope"
python3 "$staged_native/stage-package.py" verify-stage --destination "$staged_root"
install_dir="$native_cache/current"
staging_dir="$(mktemp -d "$build_root/app-stage.XXXXXX")"
app_dir="$staging_dir/Reservoir Scope.app"
mkdir -p "$app_dir/Contents/MacOS" "$app_dir/Contents/Resources"
cp -X "$build_root/build/ReservoirScope" "$app_dir/Contents/MacOS/ReservoirScope"
cp -X "$core_cache/bin/essentials-run" "$app_dir/Contents/MacOS/essentials-run"
cp -X "$staged_native"/Sources/ReservoirScope/Resources/* "$app_dir/Contents/Resources/"
python3 - "$staged_native/resource-manifest.json" "$app_dir/Contents/Info.plist" <<'PY'
import json, pathlib, plistlib, sys
release=json.loads(pathlib.Path(sys.argv[1]).read_text())["release"]
plist={"CFBundleName":"Reservoir Scope","CFBundleDisplayName":"Reservoir Scope",
       "CFBundleIdentifier":"research.reservoir.scope","CFBundleExecutable":"ReservoirScope",
       "CFBundlePackageType":"APPL","CFBundleShortVersionString":str(release["version"]),
       "CFBundleVersion":str(release["build"]),"LSMinimumSystemVersion":"14.0","NSHighResolutionCapable":True}
pathlib.Path(sys.argv[2]).write_bytes(plistlib.dumps(plist))
PY
# Sign the separate runner first so its final byte identity can be sealed.
codesign --force --sign - "$app_dir/Contents/MacOS/essentials-run"
python3 "$staged_native/package-identity.py" create --app "$app_dir" --repo "$repo_dir" --stage "$staged_root" --core-cache "$core_cache" \
  --expected-staged-sha256 "$task_stage_sha" --expected-core-sha256 "$task_core_sha"
codesign --force --sign - "$app_dir"
python3 "$staged_native/package-identity.py" verify --app "$app_dir" --stage "$staged_root"
# Serialize only publication; completed candidates and all evidence remain in their invocation root.
publish_lock="$native_cache/publish.lock"
if ! mkdir "$publish_lock" 2>/dev/null; then
  print -u2 -- "Another build is publishing. This verified candidate remains at $app_dir"
  exit 1
fi
trap 'rmdir "$publish_lock"' EXIT
mkdir -p "$install_dir"
if [[ -d "$install_dir/Reservoir Scope.app" ]]; then
  previous_dir="$(mktemp -d "$native_cache/previous-build.XXXXXX")"
  mv "$install_dir/Reservoir Scope.app" "$previous_dir/Reservoir Scope.app"
fi
# Rename a complete verified bundle; never overwrite a running executable in place.
mv "$app_dir" "$install_dir/Reservoir Scope.app"
rmdir "$staging_dir"
print -r -- "$install_dir/Reservoir Scope.app"
