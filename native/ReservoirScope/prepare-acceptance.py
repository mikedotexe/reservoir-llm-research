#!/usr/bin/env python3
"""Prepare a copied, disconnected candidate and blank human worksheet; never claims acceptance."""
import argparse
import hashlib
import json
import pathlib
import shlex
import shutil
import subprocess
import uuid

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--app',required=True,type=pathlib.Path)
p.add_argument('--out',required=True,type=pathlib.Path)
a=p.parse_args();app=a.app.resolve();out=a.out.resolve()
if not (app/'Contents/MacOS/ReservoirScope').is_file():p.error('Expected a built Reservoir Scope app')
if out.exists():p.error('Choose a new acceptance directory')
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
out.mkdir(parents=True,mode=0o700)
copy=out/app.name;shutil.copytree(app,copy)
subprocess.run(['codesign','--verify','--deep','--strict',str(copy)],check=True)
root=pathlib.Path(__file__).resolve().parent
shutil.copyfile(root/'docs/NEWCOMER-WORKSHEET.md',out/'NEWCOMER-WORKSHEET.md')
shutil.copyfile(root/'docs/GUIDED-TOUR.md',out/'GUIDED-TOUR.md')
suite='org.reservoir-scope.acceptance.'+uuid.uuid4().hex
library=out/'Library';library.mkdir(mode=0o700)
profile='(version 1)(allow default)(deny network*)(deny file-read* (subpath "/Volumes") (subpath "/Users/v/other") (subpath "/Users/mikepurvis/.cache/reservoir-research"))'
(out/'disconnected.sb').write_text(profile+'\n')
command=['env','RESERVOIR_SCOPE_PREFERENCES='+suite,'RESERVOIR_SCOPE_GUIDED_PREFS='+suite,'RESERVOIR_SCOPE_LIBRARY='+str(library),'/usr/bin/sandbox-exec','-f',str(out/'disconnected.sb'),str(copy/'Contents/MacOS/ReservoirScope')]
(out/'Start offline session.command').write_text('#!/bin/zsh\nset -eu\nexec '+shlex.join(command)+'\n')
(out/'Start offline session.command').chmod(0o700)
identity=json.loads((copy/'Contents/Resources/release-identity.json').read_bytes())
receipt=dict(schema='reservoir-scope-human-session-preparation-v1',status='prepared_not_started',human_acceptance='pending',app=str(copy),app_executable_sha256=hashlib.sha256((copy/'Contents/MacOS/ReservoirScope').read_bytes()).hexdigest(),release_identity=identity,preferences_suite=suite,library=str(library),network='denied by launcher sandbox',original_paths='denied by launcher sandbox',instructions='Have an actual first-time participant open Start offline session.command. Record answers, shown evidence, assistance and time in the blank worksheet. Do not substitute agent checks.')
(out/'session-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status='prepared_not_started',directory=str(out),human_acceptance='pending')))
