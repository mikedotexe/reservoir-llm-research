"""Verify and count the sealed September16 study-direction packet offline.

Standard library only; no model calls, live reads or writes. Counts are receipt
and job units, not independent subjects or an exhaustive provider-failure census.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    args = parser.parse_args()
    root = args.packet.resolve(strict=True)
    manifest_raw = (root / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    assert manifest['count'] == len(manifest['files'])
    assert len({r['path'] for r in manifest['files']}) == manifest['count']
    bound = {}
    for record in manifest['files']:
        path = root / record['path']
        assert not path.is_symlink() and path.resolve().is_relative_to(root)
        raw = path.read_bytes()
        assert len(raw) == record['bytes'] and sha(raw) == record['sha256'], path
        bound[record['path']] = raw
    read = lambda name: json.loads(bound[name])
    prefix = 'evidence/natural/'
    summary = read(prefix + 'summary.json')
    index = read(prefix + 'capture-index.json')
    assert summary['window_closed']
    jobs = {}
    for record in index['records']:
        raw = bound[prefix + record['retained']]
        assert len(raw) == record['bytes'] and sha(raw) == record['sha256']
        if record['kind'] == 'job' and record['source'].endswith('/job.json'):
            job = json.loads(raw)
            key = (record['being'], job['job_id'])
            if key not in jobs or record['source_mtime_ns'] > jobs[key][0]['source_mtime_ns']:
                jobs[key] = (record, job)
    protocol = summary['protocol']
    start = datetime.fromisoformat(protocol['paired_verification_utc'])
    end = datetime.fromisoformat(protocol['window_end_utc'])
    job_context = []
    for (being, ident), (record, job) in sorted(jobs.items()):
        finished = job.get('completed_at') or job.get('finished_at')
        stamp = datetime.fromisoformat(finished.replace('Z', '+00:00')) if finished else None
        job_context.append(dict(being=being, job_id=ident, action=job.get('action_text'),
                                status=job['status'], finished_at=finished,
                                in_window_completion=stamp is not None and start <= stamp < end,
                                evidence=prefix + record['retained']))
    counts = {}
    for being, result in summary['results'].items():
        receipts = result['all_window_study_receipts']
        counts[being] = dict(
            distinct_shared_inputs=len({row['input_id'] for row in receipts}),
            distinct_responses=len({row['response_sha256'] for row in receipts}),
            selected=len(result['selected']),
            strict_preparation_qualified=result['strict_qualified_count'],
            missing_selected_target=max(0, result['target'] - len(result['selected'])),
            selected_completion_tokens=[r['tokens'] for r in result['selected']],
            selected_finish=[r['finish'] for r in result['selected']])
    print(json.dumps(dict(schema='study_direction_packet_verification_v1',
                          implementation=manifest['implementation'], packet=str(root),
                          manifest_sha256=sha(manifest_raw), manifest_files=len(bound),
                          natural_files=len(index['records']), counts=counts,
                          window=protocol, job_context=job_context,
                          capture_errors=summary['capture_errors'],
                          scan_bounds=summary['scan_bound_events'],
                          board='pending; not mirrored', verified=True), indent=2))


if __name__ == '__main__':
    main()
