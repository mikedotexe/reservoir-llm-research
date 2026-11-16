#!/usr/bin/env python3
"""Bounded, explicitly opted-in model qualification in a new, retained data root.

This is a software workflow check, not a comparison of model behavior. It starts
only the supplied app binary, never a model service or an existing app profile.
The model receives two ordinary experiment-v4 prompts and one exact custom prompt.
Three total attempts, a ten-minute active budget, and no automatic retries bound it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_control.cli import Client, read_descriptor
from probes.qualify_research_api import until


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--endpoint', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--allow-model-requests', action='store_true', required=True)
    a = p.parse_args()
    root = a.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    binary = a.binary.resolve()
    config = {'seed': '54', 'turnEvery': 3, 'paceMs': 5000,
              'maximumSteps': 9, 'maximumTurns': 3, 'maximumDurationSeconds': 600,
              'outputTokens': 1024, 'requestDeadlineSeconds': 180,
              'actionMode': 'authored-v3', 'promptVersion': 'reservoir-journal-actions-v3',
              'controlFeedback': 'diagnostic-v1',
              'sonar': {'version': 'experiments-v4', 'allowLiveProbe': False},
              'language': {'backend': 'ollama', 'endpoint': a.endpoint, 'model': a.model,
                           'contextTokens': 32768, 'temperature': 0.7, 'thinking': False}}
    prompt = 'Software qualification check: in one short sentence, describe what information this message gives you. This is a passive conversation; no action is requested.'
    (root / 'protocol.json').write_text(json.dumps({'config': config, 'customPrompt': prompt,
        'claim': 'API lifecycle, intervention, journal retrieval and export only; no model competence inference',
        'binarySha256': hashlib.sha256(binary.read_bytes()).hexdigest()}, indent=2) + '\n')
    descriptor = root / 'data/automation-v1/endpoint.json'
    log = (root / 'app.log').open('w')
    proc = subprocess.Popen([str(binary), '--research-api', '--data-root', str(root / 'data')], stdout=log, stderr=log)
    client = None
    run = None
    try:
        until(lambda: descriptor.exists() or proc.poll() is not None)
        assert proc.poll() is None, 'Owned API process exited'
        client = Client(read_descriptor(descriptor))

        def operation(method, path, body=None):
            op = client.request(method, path, body)
            result = client.wait(op['id'], 210)
            assert result['status'] == 'completed', result
            return result['result']

        checked = client.request('POST', '/v1/validate', {'kind': 'configuration', 'config': config})
        assert checked['valid'], checked
        inventory = operation('POST', '/v1/models/check', config['language'])
        run = operation('POST', '/v1/runs', {'config': config})['runId']
        route = f'/v1/runs/{run}'
        grow = client.request('POST', route + '/interventions',
            {'kind': 'configuration', 'at': {'step': 4}, 'patch': {'reservoirNodes': 48}})
        ask = client.request('POST', route + '/interventions',
            {'kind': 'prompt', 'at': {'step': 5}, 'prompt': prompt, 'includeTelemetry': False})
        operation('POST', route + '/actions/start')
        until(lambda: client.request('GET', route)['journalCount'] >= 1, 210)
        operation('POST', route + '/actions/pause')
        paused = client.request('GET', route)
        assert paused['phase'] == 'paused', paused
        growth_outcome = client.wait(grow['id'], 30)
        if growth_outcome['status'] == 'cancelled':
            # Pause deliberately supersedes an in-progress settings transition.
            # Resubmit the selected boundary explicitly; never retry model writing.
            assert client.request('GET', route + '/settings')['configurationRevision'] == 0
            grow = client.request('POST', route + '/interventions',
                {'kind': 'configuration', 'at': {'step': 4}, 'patch': {'reservoirNodes': 48}})
        else:
            assert growth_outcome['status'] == 'completed', growth_outcome
        first_page = client.request('GET', route + '/entries?limit=1')
        operation('POST', route + '/actions/resume')
        until(lambda: client.request('GET', route)['journalCount'] == 3, 420)
        for op in [grow, ask]:
            assert client.wait(op['id'], 30)['status'] == 'completed'
        operation('POST', route + '/actions/stop')
        settings = client.request('GET', route + '/settings')
        assert settings['configured']['reservoirNodes'] == 48 and settings['configurationRevision'] == 1
        command = [sys.executable, '-m', 'reservoir_control', '--endpoint-file', str(descriptor)]
        cli = subprocess.run(command + ['entries', 'list', run, '--all'], cwd=Path(__file__).resolve().parents[1], check=True, text=True, capture_output=True)
        page = json.loads(cli.stdout)
        assert page['total'] == 3, page
        journals = []
        for item in page['entries']:
            fetched = subprocess.run(command + ['entries', 'get', run, item['entryId']], cwd=Path(__file__).resolve().parents[1], check=True, text=True, capture_output=True)
            entry = json.loads(fetched.stdout)
            journal = entry['journal']
            pending = journal['evidence']['pending']
            assert journal['rawReply'] == pending['response']['text'] and pending['response']['complete']
            journals.append(journal)
        assert any(j['evidence']['pending']['prompt'] == prompt for j in journals)
        assert any(j['configurationRevision'] == 1 for j in journals)
        assert any(j['entryId'] == first_page['entries'][0]['entryId'] for j in journals)
        (root / 'journals.json').write_text(json.dumps(journals, indent=2) + '\n')
        exported = client.export(run, root / 'export', 'qualification-export')
        assert exported['status'] == 'completed', exported
        report = {'status': 'passed', 'model': inventory, 'runId': run, 'journals': 3,
                  'pauseResume': True, 'growthOutcomeAtPause': growth_outcome['status'],
                  'scheduledGrowth': {'from': 32, 'to': 48, 'revision': 1},
                  'exactCustomPrompt': True, 'cliListAndDetail': True,
                  'completeProviderResponses': 3, 'verifiedExport': exported['report'],
                  'finalPhase': client.request('GET', route)['phase']}
        (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)
    finally:
        if proc.poll() is None:
            if client and run:
                try:
                    op = client.request('POST', f'/v1/runs/{run}/actions/stop')
                    client.wait(op['id'], 30)
                except Exception as error:
                    print(f'Cleanup stop: {error}', file=sys.stderr)
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        log.close()


if __name__ == '__main__':
    main()
