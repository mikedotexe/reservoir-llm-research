#!/usr/bin/env bash
# Focused guided presentation and model invariants in an unpresented native host.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
python3 - "$task_native_dir" "$1" "$2" "${3:-$task_native_dir/../../essentials/examples/portable}" <<'PY'
from pathlib import Path
import hashlib, json, os, plistlib, shutil, subprocess, sys, time, uuid
native, lib, out, resources = (Path(value).resolve() for value in sys.argv[1:])
out.mkdir(parents=True, exist_ok=False)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
names = ['ResourceBundle.swift', 'ExperimentStore.swift', 'StateSurface.swift', 'StateSurfaceScene.swift',
         'ActionComparisonViewModel.swift', 'GuidedLessons.swift', 'GuidedTourModel.swift', 'GuidedCharts.swift',
         'RegulationExampleView.swift', 'LocalModelReadiness.swift', 'ActionComparisonExperience.swift']
paths = [native / 'Sources/ReservoirScope' / name for name in names]
paths.append(native / 'Tests/GuidedPlaybackPresentationChecks.swift')
sources = {str(path): path.read_bytes() for path in paths}
assembled = out / 'checks.swift'
assembled.write_bytes(b'\n'.join(sources.values()))
app = out / 'GuidedPlaybackChecks.app'
binary = app / 'Contents/MacOS/GuidedPlaybackChecks'
binary.parent.mkdir(parents=True)
destination = app / 'Contents/Resources'
destination.mkdir()
catalog = json.loads((resources / 'guided-lessons.json').read_text())
filenames = {'guided-lessons.json', 'example-observation-active-scripted.json'}
for lesson in catalog['lessons']:
    filenames.add(lesson['scriptedFile'])
resource_hashes = {}
for name in sorted(filenames):
    if Path(name).name != name: raise ValueError('Unsafe fixture filename')
    original = resources / name
    resource_hashes[str(original)] = sha(original)
    # The production importer requires regular files. APFS clones keep these
    # independent fixture copies cheap without weakening that boundary.
    copied = subprocess.run(['/bin/cp', '-c', str(original), str(destination / name)], capture_output=True)
    if copied.returncode: shutil.copyfile(original, destination / name)
(app / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': binary.name,
    'CFBundleIdentifier': 'org.reservoir-scope.guided-check', 'CFBundlePackageType': 'APPL'}))
core = lib / 'libEssentialsCore.a'
core_sha = sha(core)
command = ['xcrun', 'swiftc', '-parse-as-library', '-O', '-swift-version', '5', '-I', str(lib),
           '-L', str(lib), '-lEssentialsCore', '-framework', 'Accelerate', str(assembled), '-o', str(binary)]
build = subprocess.run(command, capture_output=True, text=True)
(out / 'build.log').write_text(build.stdout + build.stderr)
if build.returncode:
    print(build.stderr); raise SystemExit(build.returncode)
if sha(core) != core_sha: raise SystemExit('Core archive changed during linking')
preferences = 'org.reservoir-scope.guided-check.' + uuid.uuid4().hex
env = dict(os.environ, RESERVOIR_SCOPE_PREFERENCES=preferences, RESERVOIR_SCOPE_GUIDED_PREFS=preferences,
           RESERVOIR_SCOPE_LIBRARY=str(out / 'Library'))
assert env['RESERVOIR_SCOPE_PREFERENCES'] == env['RESERVOIR_SCOPE_GUIDED_PREFS']
run_command = ['/usr/bin/sandbox-exec', '-p', '(version 1) (allow default) (deny network*)', str(binary), str(out)]
started = time.monotonic()
try:
    run = subprocess.run(run_command, capture_output=True, text=True, env=env, timeout=40)
    log = run.stdout + run.stderr; code = run.returncode
except subprocess.TimeoutExpired as error:
    log = (error.stdout or b'').decode() + (error.stderr or b'').decode(); code = 124
(out / 'run.log').write_text(log)
unchanged = all(sha(Path(path)) == digest for path, digest in resource_hashes.items()) and sha(core) == core_sha
receipt = {'sources': {path: hashlib.sha256(raw).hexdigest() for path, raw in sources.items()},
    'resources': resource_hashes, 'core_library_sha256': core_sha, 'executable_sha256': sha(binary),
    'build_command': command, 'run_command': run_command, 'exit_code': code,
    'elapsed_seconds': time.monotonic() - started, 'inputs_unchanged': unchanged,
    'preferences_suite': env['RESERVOIR_SCOPE_PREFERENCES'], 'library': env['RESERVOIR_SCOPE_LIBRARY'],
    'guided_preferences_suite': env['RESERVOIR_SCOPE_GUIDED_PREFS'],
    'toolchain_environment': {key: env.get(key) for key in ('DEVELOPER_DIR', 'SDKROOT')},
    'scope': 'Separate unpresented harness; model-driven checks only, no actual control presses, candidate app build or user-review interaction'}
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(log); print(out)
raise SystemExit(code if unchanged else 1)
PY
