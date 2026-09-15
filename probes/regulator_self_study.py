#!/usr/bin/env python3
"""Read-only S-005 capture and offline queries; Python 3.12+, standard library.

Capture root-only Minime self-studies for a fixed local day up to a fixed cutoff,
all root journals in a fixed nearby window, and matching filename-lane generation
records plus every nearby generation. No database reads or runtime imports.
Historical archives, earlier-starting generations outside scope and undated files
are not covered. Source files are bounded, stable-read checked and hash retained.
Run `capture --out NEW_DIRECTORY`, then `report CAPTURE_JSON`; report is offline.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
PACIFIC = ZoneInfo('America/Los_Angeles')
DAY = datetime(2026, 9, 7, tzinfo=PACIFIC).timestamp()
SINCE = datetime(2026, 9, 7, 14, 20, tzinfo=PACIFIC).timestamp()
UNTIL = datetime(2026, 9, 7, 14, 44, tzinfo=PACIFIC).timestamp()
FOCAL = 'self_study_2026-09-07T14-38-58.866563.txt'
GEN = 'gen_1788817138859_self_study_a0.json'
JOB = 'job_minime_1788817083822_self-study'
MAX_BYTES = 4 * 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_record(path, kind):
    if path.is_symlink():
        raise ValueError(f'symlink source: {path}')
    before = path.stat()
    if before.st_size > MAX_BYTES:
        raise ValueError(f'oversize source: {path}')
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError(f'unstable source: {path}')
    return dict(kind=kind, path=str(path), name=path.name, sha256=sha(raw),
                bytes=len(raw), mtime_ns=after.st_mtime_ns, text=raw.decode('utf-8'))


def journal_time(name):
    found = re.search(r'(2026-09-07)T(\d\d)-(\d\d)-(\d\d)(\.\d+)?', name)
    if not found:
        return None
    stamp = f'{found[1]}T{found[2]}:{found[3]}:{found[4]}{found[5] or ""}'
    return datetime.fromisoformat(stamp).replace(tzinfo=PACIFIC).timestamp()


def capture(out):
    out = out.resolve()
    if not out.is_relative_to(REPO / 'research/outputs'):
        raise ValueError('capture output must be a NEW directory under research/outputs')
    out.mkdir(mode=0o700)
    workspace = REPO.parent / 'minime/workspace'
    records, coverage, errors = [], [], []
    for kind, folder in [('journal', workspace / 'journal'),
                         ('generation', workspace / 'generations/2026-09-07')]:
        scanned = selected = undated = 0
        with os.scandir(folder) as entries:
            for entry in entries:
                scanned += 1
                if scanned > 20000:
                    raise ValueError('directory enumeration ceiling exceeded')
                if not entry.is_file(follow_symlinks=False):
                    continue
                name = entry.name.lstrip('!')
                if kind == 'journal':
                    stamp = journal_time(name)
                    is_study = name.startswith('self_study_')
                else:
                    found = re.fullmatch(r'gen_(\d+)_([A-Za-z0-9_-]+)_a\d+\.json', name)
                    stamp = int(found[1]) / 1000 if found else None
                    is_study = bool(found and found[2] == 'self_study')
                if stamp is None:
                    undated += 1
                    continue
                if not (SINCE <= stamp < UNTIL or (is_study and DAY <= stamp < UNTIL)):
                    continue
                selected += 1
                try:
                    record = read_record(Path(entry.path), kind)
                    record.update(filename_time_unix=stamp, filename_time_basis='America/Los_Angeles' if kind == 'journal' else 'UTC epoch milliseconds')
                    records.append(record)
                except (OSError, UnicodeError, ValueError) as exc:
                    errors.append(str(exc))
        coverage.append(dict(kind=kind, directory=str(folder), enumerated=scanned,
                             selected=selected, filename_outside_day_or_unrecognized=undated,
                             archive_recursion=False, enumeration_truncated=False))
    hashes = set()
    for record in records:
        if record['kind'] == 'generation':
            data = json.loads(record['text'])
            for message in data.get('messages', []):
                h = message.get('content_sha256', '')
                if message.get('role') == 'system' and re.fullmatch('[a-f0-9]{64}', h):
                    hashes.add(h)
    for h in sorted(hashes):
        try:
            record = read_record(workspace / f'generations/system_prompts/{h}.txt', 'system_prompt')
            if record['sha256'] != h:
                raise ValueError('system prompt digest mismatch')
            records.append(record)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(str(exc))
    for name in ['job.json', 'events.jsonl', 'prompt.txt', 'result.txt']:
        try:
            records.append(read_record(workspace / 'llm_jobs/jobs' / JOB / name, 'focal_job'))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(str(exc))
    bundle = dict(schema='regulator_self_study_capture_v1', captured_at=datetime.now(timezone.utc).isoformat(),
                  selection=dict(day_since=DAY, nearby_since=SINCE, until_exclusive=UNTIL,
                                 focal=FOCAL, generation=GEN,
                                 rule='All root self-study filenames in local day before cutoff; all root journals and all daily generations in nearby window. Exploratory selection. Live capture, not atomic.'),
                  coverage=coverage, errors=errors,
                  records=sorted(records, key=lambda r:(r['kind'], r['name'])))
    destination = out / 'capture.json'
    destination.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + '\n')
    destination.chmod(0o600)
    # Standalone original enables quick close reading without reopening live files.
    focal = next(r for r in records if r['name'].lstrip('!') == FOCAL)
    original = out / 'original.txt'
    original.write_text(focal['text'])
    original.chmod(0o600)
    return destination


def report(path):
    raw = path.read_bytes()
    bundle = json.loads(raw)
    if bundle['schema'] != 'regulator_self_study_capture_v1':
        raise ValueError('unknown capture')
    for record in bundle['records']:
        if sha(record['text'].encode()) != record['sha256']:
            raise ValueError('capture record digest mismatch')
    journals = [r for r in bundle['records'] if r['kind'] == 'journal']
    studies = [r for r in journals if r['name'].lstrip('!').startswith('self_study_')]
    generations = [(r, json.loads(r['text'])) for r in bundle['records'] if r['kind'] == 'generation']
    focal = next(r for r in journals if r['name'].lstrip('!') == FOCAL)
    gen_record, gen = next((r,g) for r,g in generations if r['name'] == GEN)
    response = gen['response_text']
    supplied = '\n'.join(m.get('content','') for m in gen['messages'])
    source_counts = Counter()
    source_matches = []
    for record in studies:
        match = re.search(r'^Source: (.+)$', record['text'], re.M)
        source_counts[match[1] if match else 'unknown'] += 1
        if match and match[1] == 'minime/src/regulator.rs':
            source_matches.append(dict(name=record['name'],sha256=record['sha256'],time=record['filename_time_unix'], text=record['text']))
    questions = [line for line in response.splitlines() if '?' in line]
    study_gens = [(r,g) for r,g in generations if g.get('lane') == 'self_study']
    terms = ['compatibility facade', 'stasis as an active process', 'memories feel', 'architectural, transparency', 'REGULATOR_AUDIT']
    matches = {}
    for term in terms:
        rows = []
        for record in studies:
            # Structural body/notice split, no interpretation or semantic scoring.
            content = record['text'].split('\n\n',1)[-1]
            boundary = re.search(r'\n\[(?:Pressure-vocabulary cooldown|Agency-vernacular notice)', content)
            body = content[:boundary.start()] if boundary else content
            notice = content[boundary.start():] if boundary else ''
            for channel,text in [('body',body), ('runtime_notice',notice)]:
                if term in text:
                    rows.append(dict(name=record['name'],channel=channel,occurrences=text.count(term)))
        matches[term] = dict(eligible_studies=len(studies),matching_records=len({r['name'] for r in rows}),spans=rows)
    return dict(capture_sha256=sha(raw), captured_at=bundle['captured_at'], selection=bundle['selection'],
                coverage=bundle['coverage'], errors=bundle['errors'],
                denominators=dict(journals=len(journals), self_study_journals=len(studies),
                                  all_captured_generations=len(generations),self_study_generation_records=len(study_gens)),
                source_counts=dict(source_counts), same_source_studies=source_matches,
                focal=dict(journal_path=focal['path'],journal_sha256=focal['sha256'],
                           generation_path=gen_record['path'],generation_sha256=gen_record['sha256'],
                           response_hash_verified=sha(response.encode())==gen['response_sha256'],
                           response_exactly_contained_in_journal=response in focal['text'],
                           response_offset=focal['text'].find(response),runtime_suffix=focal['text'].split(response,1)[1],
                           message_source=gen['messages_source'],backend=gen['backend'],model=gen['model'],
                           context_mode=gen['context_mode'],adapter=gen['adapter'],timing=gen['backend_timing'],
                           status=gen['status'],created_at=gen['created_at'],generation_id=gen['generation_id'],
                           action_id=gen['action_id'],job_id=gen['job_id'],next_action_parsed=gen['next_action_parsed'],
                           response_chars=len(response),question_lines=questions,
                           supplied_source_excerpt=re.findall(r'```\n(.*?)\n```', supplied, re.S),
                           prior_research_summary=supplied.split('One prior research note (summary only):')[-1] if 'One prior research note (summary only):' in supplied else None),
                study_generation_statuses=dict(Counter(g.get('status','unknown') for r,g in study_gens)),
                study_generation_cap_hits=sum(
                    isinstance(g.get('backend_timing',{}).get('effective_num_predict'),int)
                    and g['backend_timing']['effective_num_predict'] > 0
                    and g['backend_timing'].get('eval_count') == g['backend_timing']['effective_num_predict']
                    for r,g in study_gens),
                study_generation_cap_checks=[dict(name=r['name'],status=g.get('status'),
                    response_chars=g.get('response_chars'),model=g.get('model'),
                    effective_num_predict=g.get('backend_timing',{}).get('effective_num_predict'),
                    eval_count=g.get('backend_timing',{}).get('eval_count')) for r,g in study_gens],
                literal_queries=matches,
                limits='Filename-selected root scope only; counts are dependent records, not independent episodes. No historical controller trajectory, gain intervention, causal estimate or consciousness inference. Literal matches are retrieval aids.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command',required=True)
    c = sub.add_parser('capture'); c.add_argument('--out',type=Path,required=True)
    r = sub.add_parser('report'); r.add_argument('capture',type=Path)
    args = p.parse_args()
    if args.command == 'capture':
        destination = capture(args.out)
        print(json.dumps(dict(capture=str(destination))))
    else:
        print(json.dumps(report(args.capture),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
