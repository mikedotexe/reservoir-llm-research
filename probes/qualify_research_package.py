#!/usr/bin/env python3
"""Verify our local package against its source app; exercise its CLI without models.

Extracts only an explicitly selected locally built archive into a new output
directory. Starts its binary headlessly with a new data root, never an app profile.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'desktop/ReservoirScope/scripts'))
from qualification_receipt import package_inventory
from probes.qualify_research_api import until


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive', type=Path)
    p.add_argument('--source-app', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = a.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    subprocess.run(['ditto', '-x', '-k', str(a.archive.resolve()), str(root / 'extracted')], check=True)
    package = root / 'extracted/Reservoir-Research-0.54.0-macos-arm64'
    app = package / 'Reservoir Research Integration.app'
    original = package_inventory(a.source_app.resolve())
    extracted = package_inventory(app)
    assert original == extracted, 'Extracted file bytes, modes or symlinks changed'
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    cli = [sys.executable, str(package / 'reservoirctl.pyz')]
    subprocess.run(cli + ['--help'], check=True, capture_output=True)
    descriptor = root / 'data/automation-v1/endpoint.json'
    missing = subprocess.run(cli + ['--endpoint-file', str(descriptor), 'capabilities'], capture_output=True)
    assert missing.returncode == 1
    with (root / 'app.log').open('w') as log:
        proc = subprocess.Popen([str(app / 'Contents/MacOS/reservoir-scope-desktop'), '--research-api', '--data-root', str(root / 'data')], stdout=log, stderr=log)
        try:
            until(lambda: descriptor.exists() or proc.poll() is not None)
            assert proc.poll() is None
            cli += ['--endpoint-file', str(descriptor)]
            capabilities = subprocess.run(cli + ['capabilities'], check=True, text=True, capture_output=True)
            assert json.loads(capabilities.stdout)['experimentCommandExample']
            for config, valid in [({}, True), ({'reservoirNodes': 1}, False)]:
                path = root / ('valid.json' if valid else 'invalid.json')
                path.write_text(json.dumps(config))
                result = subprocess.run(cli + ['validate', 'configuration', str(path)], text=True, capture_output=True)
                assert result.returncode == (0 if valid else 1)
                assert json.loads(result.stdout)['valid'] == valid
            runs = subprocess.run(cli + ['runs', 'list'], check=True, text=True, capture_output=True)
            assert json.loads(runs.stdout)['runs'] == []
        finally:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
    assert proc.returncode == 0 and not descriptor.exists()
    report = {'status': 'passed', 'archiveSha256': hashlib.sha256(a.archive.read_bytes()).hexdigest(),
              'inventorySha256': extracted['inventorySha256'], 'appFiles': len(extracted['files']),
              'signatureVerified': True, 'extractedInventoryMatches': True,
              'packagedCli': {'capabilities': True, 'preflightExitCodes': [0, 1], 'missingInstanceExitCode': 1},
              'runsCreated': 0, 'modelRequests': 0, 'cleanShutdown': True}
    (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
