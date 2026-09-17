#!/usr/bin/env bash
# Synthetic action comparison in the actual SwiftUI view and AppKit event loop.
set -euo pipefail
task_native_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
task_cache="${XDG_CACHE_HOME:-$HOME/.cache}/reservoir-research"
task_core_lib="${1:-$task_cache/ReservoirScope-build/essentials/lib}"
task_output="${2:-$task_cache/ReservoirScope-validation/action-inspector-layout}"
python3 - "$task_native_dir" "$task_core_lib" "$task_output" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys,time
native,lib,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
core_path=lib/'libEssentialsCore.a'
core_sha=sha(core_path)
source=native/'Sources/ReservoirScope'
paths=[source/name for name in ['ResourceBundle.swift','ExperimentStore.swift','StateSurface.swift','StateSurfaceScene.swift',
    'ActionComparisonViewModel.swift','GuidedLessons.swift','GuidedTourModel.swift','GuidedCharts.swift','RegulationExampleView.swift','LocalModelReadiness.swift','ActionComparisonExperience.swift']]
paths.append(native/'Tests/ActionInspectorLayoutChecks.swift')
assembled=out/'checks.swift'
source_bytes={str(path):path.read_bytes() for path in paths}
context_path=source/'ScopeWorkspace.swift'
context_bytes=context_path.read_bytes()
context_snapshot=out/'reviewed-ScopeWorkspace.swift'
context_snapshot.write_bytes(context_bytes)
assembled.write_bytes(b'\n'.join(source_bytes.values()))
binary=out/'checks'
command=['xcrun','swiftc','-O','-swift-version','5','-I',str(lib),'-L',str(lib),
    '-lEssentialsCore','-framework','Accelerate',str(assembled),'-o',str(binary)]
build=subprocess.run(command,capture_output=True,text=True)
(out/'build.log').write_text(build.stdout+build.stderr)
if build.returncode:
    print(build.stderr); raise SystemExit(build.returncode)
if sha(core_path)!=core_sha:
    raise SystemExit('Core archive changed while linking the harness; rerun after the app build completes.')
identity={'sources':{path:hashlib.sha256(data).hexdigest() for path,data in source_bytes.items()},
    'reviewed_context_sources':{str(context_path):hashlib.sha256(context_bytes).hexdigest()},
    'core_library_sha256':core_sha,'executable_sha256':sha(binary)}
start=time.monotonic()
try:
    run=subprocess.run([str(binary),str(out)],capture_output=True,text=True,timeout=30)
    log=run.stdout+run.stderr
    status={'exit_code':run.returncode,'timed_out':False,'elapsed_seconds':time.monotonic()-start}
except subprocess.TimeoutExpired as error:
    log=(error.stdout or b'').decode()+(error.stderr or b'').decode()
    status={'exit_code':124,'timed_out':True,'elapsed_seconds':time.monotonic()-start}
(out/'run.log').write_text(log)
(out/'receipt.json').write_text(json.dumps({'identity':identity,'status':status},indent=2,sort_keys=True)+'\n')
print(log); print(json.dumps(status)); print(out)
raise SystemExit(status['exit_code'])
PY
