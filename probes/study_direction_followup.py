"""Freeze and replay both Beings' post-release journals. Filesystem reads only.

No model calls, runtime imports, database writes or NEXT execution. Filename
times select journals; receipt mtimes and generation filename clocks remain distinct.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.parsing import filename_timestamp, parse_journal

RESEARCH = Path(__file__).resolve().parents[1]
ROOTS = {'astrid': RESEARCH.parent / 'astrid/capsules/spectral-bridge/workspace',
         'minime': RESEARCH.parent / 'minime/workspace'}
OUT = RESEARCH / 'research/outputs/2026-09-16-study-direction-followup'
START = '2026-09-16T19:33:39.605405+00:00'
END = '2026-09-16T23:37:19+00:00'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)


def stable(path):
    a = path.stat()
    assert not path.is_symlink() and a.st_size <= 12_000_000, path
    raw = path.read_bytes()
    b = path.stat()
    assert (a.st_ino, a.st_size, a.st_mtime_ns) == (b.st_ino, b.st_size, b.st_mtime_ns), path
    return raw


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def capture():
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    assert not (OUT / 'protocol.json').exists(), 'Capture is immutable; replay instead'
    lo, hi = timestamp(START), timestamp(END)
    save(OUT / 'protocol.json', dict(start_inclusive_utc=START, end_exclusive_utc=END,
         selected_before_reading='Last20 prose-candidate journals and last20 source-study journals per Being, union; all files in census retained.',
         channels='Root and all immediate archive directories plus private_writing/journal; all UTC-day generations by filename epoch, referenced jobs/system prompts; recent shared/accepted receipts by filesystem mtime.',
         limits='No causal attribution. Prose shares are file counts, not attention or activity shares. File, attempt and action units differ. Provider/generation logging may be incomplete. NEXT text is not execution.',
         max_bucket_bytes=128_000_000, max_file_bytes=12_000_000,
         authority='Read-only toward Beings; no induced requests, messages, source/state edits or S007 changes.',
         board='pending; not mirrored'))
    manifests, inventories, errors = {}, [], []

    def retain(paths, name):
        records = []; total = 0
        for path, stamp in sorted(set(paths), key=lambda p: (p[1] or 0, str(p[0]))):
            try:
                raw = stable(path); total += len(raw)
                assert total <= 128_000_000, 'Bucket byte bound'
                records.append(dict(path=str(path), name=path.name, timestamp=stamp,
                     mtime_ns=path.stat().st_mtime_ns, bytes=len(raw), sha256=sha(raw), text=raw.decode()))
            except (OSError, ValueError, AssertionError) as error:
                errors.append(dict(path=str(path), error=str(error)))
        p = OUT / name
        with p.open('x') as stream:
            for row in records: stream.write(json.dumps(row, ensure_ascii=False)+'\n')
        p.chmod(0o600)
        manifests[name] = dict(count=len(records), bytes=total, sha256=sha(p.read_bytes()))
        return records

    for being, root in ROOTS.items():
        paths = []
        journal = root / 'journal'
        folders = [journal, root / 'private_writing/journal']
        archive = journal / 'archive'
        if archive.is_dir(): folders += [Path(e.path) for e in os.scandir(archive) if e.is_dir(follow_symlinks=False)]
        for folder in folders:
            if not folder.is_dir():
                inventories.append(dict(being=being, directory=str(folder), missing=True)); continue
            count = 0
            for e in os.scandir(folder):
                count += 1
                t = filename_timestamp(e.name, being)
                # Shared WRITE filenames can carry epoch seconds even for Minime.
                if t is None and folder == root / 'private_writing/journal':
                    t = filename_timestamp(e.name, 'astrid')
                if e.is_file(follow_symlinks=False) and e.name.endswith('.txt') and t is not None and lo <= t < hi:
                    paths.append((Path(e.path), t))
            inventories.append(dict(being=being, directory=str(folder), enumerated=count))
        retain(paths, f'{being}-journals.jsonl')
        paths = []
        day = root / 'generations/2026-09-16'
        for e in os.scandir(day):
            m = re.fullmatch(r'gen_(\d+)_.+\.json', e.name)
            if e.is_file(follow_symlinks=False) and m and lo <= int(m[1])/1000 < hi:
                paths.append((Path(e.path), int(m[1])/1000))
        generations = retain(paths, f'{being}-generations.jsonl')
        jobs, prompts = set(), set()
        for row in generations:
            d = json.loads(row['text'])
            if d.get('job_id'): jobs.add(d['job_id'])
            prompts.update(m['content_sha256'] for m in d.get('messages', []) if re.fullmatch(r'[a-f0-9]{64}', m.get('content_sha256','')))
        retain([(root / 'llm_jobs/jobs' / j / 'job.json', None) for j in jobs if re.fullmatch(r'[A-Za-z0-9_-]+',j)], f'{being}-jobs.jsonl')
        retain([(root / 'generations/system_prompts' / (s+'.txt'), None) for s in prompts], f'{being}-systems.jsonl')
        for kind, directory in [('shared',root/'diagnostics/source_first_v3/shared_reader/deliveries'),
                                 ('navigation',root/'diagnostics/source_first_v3/shared_reader/navigation'),
                                 ('provider',root/'diagnostics/accepted_deliveries')]:
            paths = []; scanned = 0
            if directory.is_dir():
                for e in os.scandir(directory):
                    scanned += 1; stat = e.stat(follow_symlinks=False)
                    if e.is_file(follow_symlinks=False) and e.name.endswith('.json') and lo <= stat.st_mtime < hi:
                        paths.append((Path(e.path),stat.st_mtime))
                    elif e.is_dir(follow_symlinks=False) and stat.st_mtime >= lo:
                        for c in os.scandir(e.path):
                            if c.is_file(follow_symlinks=False) and c.name.endswith('.json'):
                                t=c.stat(follow_symlinks=False).st_mtime
                                if lo <= t < hi: paths.append((Path(c.path),t))
            inventories.append(dict(being=being, directory=str(directory), enumerated=scanned, selected=len(paths)))
            retain(paths,f'{being}-{kind}.jsonl')
    save(OUT/'capture-manifest.json',dict(captured_at=datetime.now(timezone.utc).isoformat(),files=manifests,inventories=inventories,errors=errors))
    (OUT/'parsing-snapshot.py').write_bytes((RESEARCH/'reservoir_research/parsing.py').read_bytes())
    (OUT/'probe-snapshot.py').write_bytes(Path(__file__).read_bytes())


def load(name):
    for line in (OUT/name).read_text().splitlines():
        row=json.loads(line); assert sha(row['text'].encode())==row['sha256']; yield row


def analyze():
    assert (RESEARCH/'reservoir_research/parsing.py').read_bytes() == (OUT/'parsing-snapshot.py').read_bytes(), 'Parser changed; use the retained parser snapshot for this frozen replay'
    manifest=json.loads((OUT/'capture-manifest.json').read_text())
    for name,r in manifest['files'].items(): assert sha((OUT/name).read_bytes())==r['sha256'],name
    report={'window':json.loads((OUT/'protocol.json').read_text()),'beings':{},'capture_errors':manifest['errors']}
    all_rows=[]; readings=[]
    for being in ROOTS:
        entries=[]; seen={}; duplicates=[]
        for row in load(f'{being}-journals.jsonl'):
            key=row['name'].lstrip('!')
            if key in seen:
                duplicates.append(dict(name=key,identical=seen[key]==row['sha256']))
                if seen[key]==row['sha256']:continue
            seen[key]=row['sha256']; parsed=parse_journal(row['text'],being,row['name'])
            private='/private_writing/journal/' in row['path']
            study=key.startswith('self_study_') or key.startswith('introspection_')
            kind=('private_write' if private else 'source_study' if study else parsed['lane'] or parsed['entry_type'])
            prose=private or study or parsed['content_kind']=='prose'
            entries.append(dict(row,**parsed,being=being,mode=kind,prose_candidate=prose,words=len(parsed['body_text'].split())))
        entries.sort(key=lambda r:(r['timestamp'],r['name']))
        prose=[r for r in entries if r['prose_candidate']]; studies=[r for r in entries if r['mode']=='source_study']
        chosen={r['path'] for r in prose[-20:]}|{r['path'] for r in studies[-20:]}
        for r in entries:
            if r['path'] in chosen:readings.append(dict(r,groups=(["latest20_prose"] if r in prose[-20:] else [])+(["latest20_study"] if r in studies[-20:] else [])))
        report['beings'][being]=dict(files=len(entries),prose_files=len(prose),study_files=len(studies),
            prose_modes=dict(Counter(r['mode'] for r in prose)),all_types=dict(Counter(r['mode'] for r in entries)),
            median_study_words=statistics.median([r['words'] for r in studies]) if studies else None,
            study_next_text=dict(Counter(r['next_verb'] or 'none' for r in studies)),
            duplicates=duplicates,selected=len(chosen),latest_files=[r['name'] for r in entries[-5:]])
        runs=[]
        for r in prose:
            if runs and runs[-1]['mode']==r['mode']:
                runs[-1]['count']+=1;runs[-1]['last']=r['name']
            else:runs.append(dict(mode=r['mode'],count=1,first=r['name'],last=r['name']))
        report['beings'][being]['prose_mode_runs']=runs
        all_rows.extend(entries)
    for name,rows in [('journal-index.jsonl',all_rows),('reading-pack.jsonl',readings)]:
        with (OUT/name).open('w') as stream:
            for row in rows:
                if name=='journal-index.jsonl':row={k:v for k,v in row.items() if k not in ('text','body_text','header_text')}
                stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        (OUT/name).chmod(0o600)
    save(OUT/'summary.json',report)
    save(OUT/'analysis-manifest.json',dict(capture_sha256=sha((OUT/'capture-manifest.json').read_bytes()),
         probe_sha256=sha(Path(__file__).read_bytes()),parser_sha256=sha((RESEARCH/'reservoir_research/parsing.py').read_bytes()),
         files={n:sha((OUT/n).read_bytes()) for n in ['summary.json','journal-index.jsonl','reading-pack.jsonl']}))
    print(json.dumps(report['beings'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['capture','analyze']);a=parser.parse_args()
    if a.mode=='capture':capture()
    else:analyze()
