#!/usr/bin/env python3
"""Launch the pinned patch package with a fresh, isolated QA Library."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

V = Path(__file__).resolve().parent
D = V.parents[1]
sys.path.insert(0, str(D / 'scripts'))
from qualification_receipt import package_inventory

plan = json.loads((V / 'ui-plan-01.json').read_bytes())
identity = json.loads((V / 'package-identity-01.json').read_bytes())
app = Path(identity['app'])
assert package_inventory(app) == identity['package']
assert identity['package']['version'] == plan['version'] == '0.27.1'
check = subprocess.run(['/usr/bin/pgrep', '-fl', 'reservoir-scope-desktop'], capture_output=True, text=True)
assert check.returncode == 1 and not check.stdout.strip(), 'Another preview is running; do not interfere'
library = Path(plan['library'])
assert library == D / 'target/qa/0.27.1-completion-ui01/library'
library.parent.mkdir()
library.mkdir()
env = os.environ.copy()
env['RESERVOIR_SCOPE_TAURI_LIBRARY'] = str(library)
exe = app / 'Contents/MacOS/reservoir-scope-desktop'
with (library.parent / 'stdout.log').open('x') as out, (library.parent / 'stderr.log').open('x') as err:
    child = subprocess.Popen([str(exe)], cwd=library.parent, env=env, stdout=out, stderr=err, start_new_session=True)
receipt = dict(startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(), pid=child.pid,
               app=str(app), executable=str(exe), library=str(library),
               executableSha256=identity['package']['binary']['sha256'],
               planSha256=hashlib.sha256((V / 'ui-plan-01.json').read_bytes()).hexdigest(),
               scope='Spawn only. Confirm exact process and native window before controls. No model service.')
with (V / 'ui-launch-01.json').open('x') as f:
    json.dump(receipt, f, indent=2)
    f.write('\n')
print(json.dumps(receipt))
