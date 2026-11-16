#!/usr/bin/env python3
"""Package an existing macOS development app and the dependency-free agent CLI.

No build, launch, signing changes, model requests, installation, or publication.
The output directory must be new; app profiles and research data are never copied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import zipapp

ROOT = Path(__file__).resolve().parents[3]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    app = a.app.resolve()
    assert (app / 'Contents/MacOS/reservoir-scope-desktop').is_file(), 'Select a built app'
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    assert info['CFBundleIdentifier'] == 'research.reservoir.scope.integration', 'Select the isolated research profile'
    assert info['CFBundleShortVersionString'] == json.loads((ROOT / 'desktop/ReservoirScope/package.json').read_text())['version'] == '0.54.0', 'Source and package must both be 0.54.0'
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    output = a.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    package = output / 'Reservoir-Research-0.54.0-macos-arm64'
    package.mkdir()
    shutil.copytree(app, package / app.name, symlinks=True)
    with tempfile.TemporaryDirectory(prefix='reservoir-cli-package-') as temp:
        cli_root = Path(temp)
        shutil.copytree(ROOT / 'reservoir_control', cli_root / 'reservoir_control',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (cli_root / '__main__.py').write_text('from reservoir_control.cli import main\nraise SystemExit(main())\n')
        zipapp.create_archive(cli_root, package / 'reservoirctl.pyz', compressed=True)
    desktop = ROOT / 'desktop/ReservoirScope'
    shutil.copy2(desktop / 'RESEARCH-API.md', package / 'RESEARCH-API.md')
    shutil.copy2(desktop / 'RELEASE-0.54.0.md', package / 'RELEASE-0.54.0.md')
    evidence = Path('validation/2026-11-15-research-integration')
    (package / evidence).mkdir(parents=True)
    for name in ['checks.json', 'checks-initial.json', 'black-box-qualified.json', 'real-model.json']:
        shutil.copy2(desktop / evidence / name, package / evidence / name)
    finalization = Path('validation/2026-11-16-research-finalization')
    (package / finalization).mkdir(parents=True)
    for name in ['deep-links.json', 'notarization.json']:
        shutil.copy2(desktop / finalization / name, package / finalization / name)
    shutil.copy2(desktop / 'NOTARIZATION.md', package / 'NOTARIZATION.md')
    shutil.copy2(ROOT / 'research/recipes/growth-experiments-v4.json', package / 'growth-experiments-v4.json')
    (package / 'README.txt').write_text('''Reservoir Research 0.54.0 — local development package

Open Reservoir Research Integration.app. Its application profile and data are
separate from other Reservoir Scope apps. Opening it never resumes retained runs.

Agent CLI (Python 3.12+; no packages to install):
  python3 reservoirctl.pyz --help
  python3 reservoirctl.pyz discover
  python3 reservoirctl.pyz --instance research.reservoir.scope.integration capabilities

Use RESEARCH-API.md for the complete API and CLI contract. Replace reservoirctl
in its examples with python3 reservoirctl.pyz. Explicitly select an instance when
several are running. The included growth recipe uses scripted writing by default.

This arm64 debug app is signed ad hoc, not notarized for public distribution.
The reservoirscope-dev scheme passed cold/warm macOS dispatch on November 16.
See RELEASE-0.54.0.md and NOTARIZATION.md for evidence and signing prerequisites.
This package does not establish long-run model competence,
cross-platform qualification, or a replacement for the frozen research instrument.
''')
    identity = {'version': '0.54.0', 'sourceCommit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'profile': 'research.reservoir.scope.integration', 'build': 'debug, arm64, ad-hoc signed',
        'cliSha256': hashlib.sha256((package / 'reservoirctl.pyz').read_bytes()).hexdigest(),
        'binarySha256': hashlib.sha256((app / 'Contents/MacOS/reservoir-scope-desktop').read_bytes()).hexdigest()}
    (package / 'IDENTITY.json').write_text(json.dumps(identity, indent=2) + '\n')
    archive = output / (package.name + '.zip')
    subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(package), str(archive)], check=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(f'{digest}  {archive.name}\n')
    print(json.dumps({'archive': str(archive), 'sha256': digest, 'bytes': archive.stat().st_size, **identity}, indent=2))


if __name__ == '__main__':
    main()
