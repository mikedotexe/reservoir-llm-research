"""Bounded Sept 15 observation; reads live files, writes only a new research packet."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('/Users/v/other/minime/workspace')
OUT = ROOT / 'research/outputs/2026-09-15-minime-study-survey'
CUTOFF = datetime.fromisoformat('2026-09-15T15:06:32+00:00').timestamp()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    path.chmod(0o600)

def files(directory):
    for entry in os.scandir(directory):
        if entry.is_dir(follow_symlinks=False):
            yield from files(entry.path)
        elif entry.is_file(follow_symlinks=False):
            yield Path(entry.path)

def capture():
    assert not (OUT / 'protocol.json').exists(), 'Do not replace a frozen cohort'
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(OUT / 'protocol.json', {
        'cutoff_utc': '2026-09-15T15:06:32Z',
        'selection': 'Latest 100 top-level SELF_STUDY journals at/before cutoff by local filename clock; chronological, no content filter.',
        'discovery': 'Daily day-6 account and one recent generation schema/body inspected before formal capture. Latest-100 selection was already chosen; exploratory survey, not blinded or causal experiment.',
        'attempt_frame': 'All generation records by completion filename clock in selected journal span; all lanes retained as metadata, self_study records retained whole, plus 5-minute incoming boundary supplement.',
        'limits': 'Top-level journals; existing files, not all conceivable opportunities. Metadata daily counts are partial live-directory counts. No model calls, live writes, commands to Beings, or S-007 cursor changes.'})
    inventory = []
    for entry in os.scandir(LIVE / 'journal'):
        match = re.match(r'^!?(.+)_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d+)\.txt$', entry.name)
        if not entry.is_file() or not match:
            continue
        stamp = datetime.strptime(match[2], '%Y-%m-%dT%H-%M-%S.%f').replace(tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()
        if stamp <= CUTOFF:
            inventory.append({'path': entry.path, 'name': entry.name, 'mode': match[1], 'epoch': stamp, 'local_day': match[2][:10], 'bytes': entry.stat().st_size})
    selected = sorted((r for r in inventory if r['mode'] == 'self_study'), key=lambda r: r['epoch'])[-100:]
    assert len(selected) == 100
    lower = selected[0]['epoch']
    write(OUT / 'selection.json', {'entries': selected, 'start_epoch': lower, 'end_epoch': CUTOFF})
    write(OUT / 'journal-inventory.json', {'rows': [r for r in inventory if r['local_day'] >= '2026-09-11']})
    retained = {}
    def retain(src, rel):
        src = Path(src)
        if str(src) in retained:
            return retained[str(src)]['retained']
        before = src.stat(); raw = src.read_bytes(); after = src.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), src
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        dst.write_bytes(raw); dst.chmod(0o600)
        retained[str(src)] = {'source': str(src), 'retained': str(rel), 'sha256': sha(raw), 'bytes': len(raw), 'mtime_ns': before.st_mtime_ns}
        return str(rel)
    for row in selected:
        retain(row['path'], Path('journals') / row['name'])
    generation_frame = []
    for day in sorted(os.scandir(LIVE / 'generations'), key=lambda e: e.name):
        if not day.is_dir() or not re.match(r'^2026-09-1[45]$', day.name):
            continue
        for entry in os.scandir(day.path):
            match = re.match(r'^gen_(\d+)_(.+)_a\d+\.json$', entry.name)
            if not match or not lower - 300 <= int(match[1]) / 1000 <= CUTOFF:
                continue
            d = json.loads(Path(entry.path).read_text())
            meta = {k: d.get(k) for k in ('generation_id', 'created_at_unix_ms', 'lane', 'prompt_class', 'status', 'error', 'job_id', 'pid', 'model')}
            meta['path'] = entry.path
            meta['main_window'] = int(match[1]) / 1000 >= lower
            generation_frame.append(meta)
            if d.get('lane') != 'self_study':
                continue
            retain(entry.path, Path('generations') / entry.name)
            for msg in d.get('messages', []):
                if msg.get('role') == 'system' and msg.get('content_sha256'):
                    p = LIVE / 'generations/system_prompts' / (msg['content_sha256'] + '.txt')
                    if p.exists():
                        retain(p, Path('system') / p.name)
            job = LIVE / 'llm_jobs/jobs' / str(d.get('job_id')) / 'job.json'
            if job.exists():
                retain(job, Path('jobs') / job.parent.name / 'job.json')
            for a in d.get('linked_artifacts', []):
                p = Path(a.get('path', ''))
                if p.is_file() and p.parent == LIVE / 'journal':
                    retain(p, Path('journals') / p.name)
    write(OUT / 'generation-frame.json', sorted(generation_frame, key=lambda r: r.get('created_at_unix_ms') or 0))
    scan = []
    for kind in ('deliveries', 'navigation'):
        directory = LIVE / 'diagnostics/source_first_v3/shared_reader' / kind
        count = 0; kept = 0
        for p in files(directory):
            count += 1
            if p.suffix == '.json' and lower - 600 <= p.stat().st_mtime <= CUTOFF:
                retain(p, Path('shared') / kind / p.relative_to(directory)); kept += 1
        scan.append({'kind': kind, 'metadata_scanned': count, 'retained_by_mtime': kept})
    for name, p in [('source-status.json', LIVE / 'runtime/autonomous_agent_source_status.json'),
                    ('jobs-status.json', LIVE / 'runtime/llm_jobs_status.json'),
                    ('reader-state-observed.json', LIVE / 'diagnostics/source_first_v3/shared_reader/reader-v1.json')]:
        if p.exists():
            retain(p, Path('runtime') / name)
    write(OUT / 'capture-index.json', {'captured_utc': datetime.now(timezone.utc).isoformat(), 'scan': scan, 'files': list(retained.values())})
    print(json.dumps({'selected': len(selected), 'first_local': selected[0]['name'], 'last_local': selected[-1]['name'], 'generation_frame': len(generation_frame), 'scan': scan, 'retained': len(retained)}, indent=2))

def analyze():
    for r in json.loads((OUT / 'capture-index.json').read_text())['files']:
        assert sha((OUT / r['retained']).read_bytes()) == r['sha256'], r
    selected = json.loads((OUT / 'selection.json').read_text())['entries']
    gens = [(p, json.loads(p.read_text())) for p in sorted((OUT / 'generations').iterdir())]
    rows = []
    for i, journal in enumerate(selected, 1):
        matches = [(p, d) for p, d in gens if any(a.get('path') == journal['path'] for a in d.get('linked_artifacts', []))]
        assert len(matches) == 1, (journal, len(matches))
        p, d = matches[0]; response = d.get('response_text', '')
        user = '\n'.join(m.get('content', '') for m in d['messages'] if m.get('role') == 'user')
        timing = d.get('backend_timing', {})
        jobpath = OUT / 'jobs' / d['job_id'] / 'job.json'
        job = json.loads(jobpath.read_text()) if jobpath.exists() else {}
        row = {'ordinal': i, **journal, 'generation_id': d['generation_id'], 'generation': str(p.relative_to(OUT)), 'job_id': d['job_id'], 'action': job.get('action_text'), 'job_status': job.get('status'),
               'response_chars': len(response), 'response_words': len(response.split()), 'response_sha256': sha(response.encode()), 'response_in_journal': response in (OUT / 'journals' / journal['name']).read_text(),
               'next': d.get('next_action_parsed'), 'input_heading': user.splitlines()[0], 'input_chars': len(user),
               'note_updates': re.findall(r'^STUDY_NOTE:\s*(.*)$', response, re.M), 'question_updates': re.findall(r'^STUDY_QUESTION:\s*(.*)$', response, re.M),
               'timing': timing, 'controls': d.get('generation_controls'), 'status': d.get('status'), 'elapsed_s': d.get('elapsed_s'), 'pid': d.get('pid'), 'model': d.get('model'), 'backend': d.get('backend')}
        for name, text in [('response', response), ('input', user)]:
            dst = OUT / 'readings' / f'{i:03d}-{name}.txt'; dst.parent.mkdir(exist_ok=True, mode=0o700); dst.write_text(text); dst.chmod(0o600)
        rows.append(row)
    write(OUT / 'linked-sequence.json', rows)
    summary = {'count': len(rows), 'input_headings': dict(Counter(r['input_heading'] for r in rows)), 'finishes': dict(Counter(r['timing'].get('native_finish') for r in rows)),
               'tokens': {k: f([r['timing']['eval_count'] for r in rows]) for k, f in [('min', min), ('median', statistics.median), ('max', max)]},
               'words': {k: f([r['response_words'] for r in rows]) for k, f in [('min', min), ('median', statistics.median), ('max', max)]},
               'allowances': dict(Counter(r['timing'].get('effective_num_predict') for r in rows)), 'exact_journal_matches': sum(r['response_in_journal'] for r in rows),
               'note_updates': sum(len(r['note_updates']) for r in rows), 'question_updates': sum(len(r['question_updates']) for r in rows),
               'unique_responses': len({r['response_sha256'] for r in rows}), 'next_to_next_job_matches': sum(a['next'] == b['action'] for a, b in zip(rows, rows[1:]))}
    write(OUT / 'summary.json', summary); print(json.dumps(summary, indent=2))

def claim_trace():
    base = Path('/Users/v/other/astrid')
    dest = OUT / 'claim-trace'
    assert not dest.exists()
    dest.mkdir(mode=0o700)
    paths = ['crates/astrid-events/src/subscriber.rs', 'crates/astrid-kernel/src/lib.rs',
             'crates/astrid-cli/src/tui/mod.rs', 'capsules/astralis/astrid-capsule-cli/src/lib.rs',
             'capsules/spectral-bridge/src/lifecycle.rs', 'capsules/spectral-bridge/src/signal_spine.rs']
    records = []
    for rel in paths:
        raw = (base / rel).read_bytes()
        target = dest / 'source' / rel
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        target.write_bytes(raw); target.chmod(0o600)
        old = subprocess.run(['git', 'show', 'ed62f1b8c2524b18922f3bb3c796a3a25f452119:' + rel], cwd=base, capture_output=True)
        records.append({'source': str(base / rel), 'retained': str(target.relative_to(OUT)), 'sha256': sha(raw), 'bytes': len(raw), 'matches_ed62_source': old.returncode == 0 and old.stdout == raw})
    commands = [
        ['rg', '-n', 'capsules_loaded|impl.*EventSubscriber', 'crates', 'capsules', '--glob', '*.rs', '--glob', '*.ts', '--glob', '*.js', '--glob', '*.py'],
        ['rg', '-n', 'capsules_loaded', 'capsules/spectral-bridge/src'],
        ['git', 'log', '-1', '--format=%H %s']]
    results = []
    for command in commands:
        result = subprocess.run(command, cwd=base, capture_output=True, text=True)
        results.append({'command': command, 'cwd': str(base), 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    write(dest / 'source-index.json', {'captured_utc': datetime.now(timezone.utc).isoformat(), 'files': records, 'searches': results,
                                      'limits': 'Current on-disk source audit, not newly supplied Being evidence or proof of every installed capsule. Text search absence is scoped to listed directories/extensions; crate-private trait visibility is stronger than a naming search.'})

def verify():
    index = json.loads((OUT / 'packet-index.json').read_text())
    for row in index['files']:
        p = OUT / row['path']
        assert p.stat().st_size == row['bytes'] and sha(p.read_bytes()) == row['sha256'], row['path']
    rows = json.loads((OUT / 'linked-sequence.json').read_text())
    assert len(rows) == 100 and len({r['generation_id'] for r in rows}) == 100
    for row in rows:
        d = json.loads((OUT / row['generation']).read_text())
        response = d['response_text']
        assert sha(response.encode()) == row['response_sha256'] == d['response_sha256']
        assert response in (OUT / 'journals' / row['name']).read_text()
        assert response == (OUT / f"readings/{row['ordinal']:03d}-response.txt").read_text()
        assert d['backend_timing']['native_finish'] == 'stop'
        assert d['backend_timing']['eval_count'] < d['backend_timing']['effective_num_predict']
    assert all(a['next'] == b['action'] for a, b in zip(rows, rows[1:]))
    print(json.dumps({'verified_files': len(index['files']), 'selected_responses': len(rows), 'next_to_next_job_matches': 99, 'packet_index_sha256': sha((OUT / 'packet-index.json').read_bytes())}, indent=2))

if __name__ == '__main__':
    {'capture': capture, 'analyze': analyze, 'claim-trace': claim_trace, 'verify': verify}[sys.argv[1]]()
