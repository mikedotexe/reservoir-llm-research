"""Bounded S-007 day-2 supplement. Run on source host; writes only research packet.

Retains navigation, indexed actions, documented releases and explicit job/failure
links. Does not import sibling code or operate the live source reader.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from reservoir_research.study_capture import Collector, ROOT, WORKSPACES, encoded, epoch


def capture(folder):
    protocol = json.loads((folder / 'protocol.json').read_bytes())
    plan = json.loads((folder / 'supplement-protocol.json').read_bytes())
    base = json.loads((folder / 'capture.json').read_bytes())
    c = Collector(epoch(protocol['since']), epoch(protocol['until_exclusive']), 'study-choice')
    workspace = WORKSPACES['minime']
    nav = workspace / 'diagnostics/source_first_v3/shared_reader/navigation'
    count = 0
    for name in c.names(nav, 10000):
        if not re.fullmatch('[a-f0-9]{64}', name):
            continue
        for leaf in c.names(nav / name, 100):
            if not re.fullmatch('[a-f0-9]{64}\\.json', leaf):
                continue
            count += 1
            if count > 10000:
                raise ValueError('Navigation ceiling')
            c.add(nav / name / leaf, 'navigation', 'minime')
    c.database('minime', workspace)
    # Use the frozen day-1 release path inventory, then add documented extensions.
    old = json.loads((REPO / 'research/outputs/2026-09-09-source-study-fidelity-day1/supplement.json').read_bytes())
    for path in sorted({r['path'] for r in old['records'] if r['kind'] == 'release'}):
        c.add(Path(path), 'release')
    for extension in ['study-context', 'study-choice']:
        row = c.add(ROOT / f'astrid/docs/steward-notes/{extension}-validation/live-rollout.json', 'release')
        if row is None:
            continue
        release = json.loads(row['text'])
        activation = Path(release['bridge']['activation_receipt'])
        reload = Path(release['minime']['receipt'])
        assert activation.is_relative_to(ROOT / 'astrid/.runtime/bridge-deployment/transactions')
        assert reload.is_relative_to(ROOT / f'worktrees/{extension}-20260909')
        for p in [activation, reload, ROOT / f'worktrees/{extension}-20260909/bridge-stage-01/manifest.json']:
            c.add(p, 'release')
    row = c.add(REPO / 'research/outputs/2026-09-09-extended-writing-qualification/rollout/live-rollout.json', 'release')
    release = json.loads(row['text'])
    for key in ['activation_receipt', 'original_failure_receipt']:
        p = Path(release['bridge'][key])
        assert p.is_relative_to(ROOT / 'astrid/.runtime/bridge-deployment/transactions')
        c.add(p, 'release')
    p = Path(release['minime']['receipt'])
    assert p.is_relative_to(ROOT / 'worktrees/longform-20260909')
    c.add(p, 'release')
    c.add(ROOT / 'worktrees/longform-20260909/bridge-stage-01/manifest.json', 'release')
    for job_id in plan['linked_job_ids']:
        assert re.fullmatch(r'job_minime_\d+_[a-zA-Z0-9_-]+', job_id)
        for name in ['job.json', 'events.jsonl', 'prompt.txt', 'result.txt']:
            c.add(workspace / 'llm_jobs/jobs' / job_id / name, 'linked_job_' + name, 'minime')
    # Inspect only structured references, never prose, for existing failure diagnostics.
    def references(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from references(item)
        elif isinstance(value, list):
            for item in value:
                yield from references(item)
        elif isinstance(value, str) and value.startswith(str(workspace / 'diagnostics/source_study_attempts') + '/'):
            yield value
    for row in base['records'] + list(c.records):
        if row['kind'] in ['generation', 'job_job.json', 'linked_job_job.json']:
            for pointer in references(json.loads(row['text'])):
                c.linked_study_failure(workspace, pointer, 'minime')
    return dict(schema='s007_daily_supplement_v2', protocol=plan, records=c.records,
                inventories=c.inventories, errors=c.errors)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('packet', type=Path)
    a = p.parse_args()
    assert a.packet.resolve().is_relative_to(REPO / 'research/outputs')
    result = capture(a.packet)
    path = a.packet / 'supplement.json'
    with path.open('xb') as out:
        out.write(encoded(result))
    path.chmod(0o600)
    print(json.dumps(dict(counts=dict(Counter(r['kind'] for r in result['records'])), errors=result['errors'])))
