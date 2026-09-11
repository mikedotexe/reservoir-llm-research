"""Freeze and describe a bounded Astrid study sequence; never writes live state."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('/Users/v/other/astrid/capsules/spectral-bridge/workspace')
OUT = ROOT / 'research/outputs/2026-09-11-astrid-small-studies'
CUTOFF = datetime.fromisoformat('2026-09-11T14:23:15+00:00').timestamp()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2) + '\n')
    path.chmod(0o600)

def capture():
    assert not OUT.exists(), 'A frozen selection must never be replaced.'
    OUT.mkdir(mode=0o700)
    protocol = {'cutoff_utc': '2026-09-11T14:23:15Z', 'selection': 'Latest 20 top-level SELF_STUDY journal files by filename completion clock, at or before cutoff, without content filtering.',
                'cohort': 'Completed journal sequence; not an attempt denominator or independent subjects.',
                'supplement': 'All journal types in the selected span; bounded shared/provider delivery tails for exact linkage.',
                'era_boundary': 'Astrid process restart 2026-09-11T14:05:29Z. Do not attribute before/after differences causally.',
                'limits': 'No induced generation, execution of journal commands, live state writes or source changes.'}
    write(OUT / 'protocol.json', protocol)
    paths = []
    for p in (LIVE / 'journal').iterdir():
        m = re.search(r'_(\d{10})\.txt$', p.name)
        if p.is_file() and m and int(m[1]) <= CUTOFF:
            paths.append((int(m[1]), p))
    selected = sorted((r for r in paths if re.match(r'^!?self_study_', r[1].name)), reverse=True)[:20]
    assert len(selected) == 20
    selected.reverse()
    lower = selected[0][0]
    evidence = []
    def retain(src, rel):
        raw = src.read_bytes()
        assert len(raw) <= 10_000_000
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        dst.write_bytes(raw)
        dst.chmod(0o600)
        row = {'source': str(src), 'retained': str(rel), 'bytes': len(raw), 'sha256': sha(raw),
               'observed_mtime_ns': src.stat().st_mtime_ns}
        evidence.append(row)
        return row
    entries = []
    for stamp, p in selected:
        row = retain(p, Path('journals') / p.name)
        entries.append(dict(row, filename_epoch=stamp, filename_utc=datetime.fromtimestamp(stamp, timezone.utc).isoformat()))
    neighbors = []
    for stamp, p in sorted(paths):
        if lower <= stamp <= CUTOFF:
            neighbors.append({'filename': p.name, 'filename_epoch': stamp, 'mode_prefix': re.sub(r'_\d{10}\.txt$', '', p.name.lstrip('!'))})
    write(OUT / 'selection.json', dict(protocol, entries=entries, span_start_epoch=lower, neighboring_journal_files=neighbors))
    scans = []
    for kind, directory in [('shared', LIVE / 'diagnostics/source_first_v3/shared_reader/deliveries'),
                            ('navigation', LIVE / 'diagnostics/source_first_v3/shared_reader/navigation'),
                            ('provider', LIVE / 'diagnostics/accepted_deliveries')]:
        candidates = [(p.stat().st_mtime, p) for p in directory.glob('**/*.json')]
        eligible = sorted((r for r in candidates if lower - 300 <= r[0] <= CUTOFF), reverse=True)
        bounded = eligible[:160]
        scans.append({'kind': kind, 'metadata_files': len(candidates), 'eligible_by_mtime': len(eligible), 'retained': len(bounded), 'limit': 160})
        for _, p in reversed(bounded):
            retain(p, Path(kind) / p.relative_to(directory))
    for name, p in [('reader-state-observed.json', LIVE / 'diagnostics/source_first_v3/shared_reader/reader-v1.json'),
                    ('active-selection.json', Path('/Users/v/other/astrid/.runtime/bridge-deployment/active.json'))]:
        retain(p, Path('runtime') / name)
    selection = json.loads((OUT / 'runtime/active-selection.json').read_text())
    retain(Path(selection['stage']) / 'manifest.json', Path('runtime/manifest.json'))
    retain(Path(selection['transaction']) / 'receipt.json', Path('runtime/activation-receipt.json'))
    write(OUT / 'capture-index.json', {'captured_at': datetime.now(timezone.utc).isoformat(), 'scans': scans, 'files': evidence})
    print(json.dumps({'selected': len(entries), 'first': entries[0]['filename_utc'], 'last': entries[-1]['filename_utc'], 'neighbors': len(neighbors), 'scans': scans}, indent=2))

def response_content(wire):
    if 'choices' in wire:
        return wire['choices'][0]['message'].get('content', '')
    return wire.get('message', {}).get('content', wire.get('response', ''))

def analyze():
    selection = json.loads((OUT / 'selection.json').read_text())
    index = json.loads((OUT / 'capture-index.json').read_text())
    for item in index['files']:
        assert sha((OUT / item['retained']).read_bytes()) == item['sha256']
    deliveries = []
    for kind in ('shared', 'navigation'):
        for p in (OUT / kind).glob('**/*.json'):
            d = json.loads(p.read_text())
            wire = d.get('attempt', d)
            if 'request_json' not in wire or 'response_json' not in wire:
                continue
            req, resp = json.loads(wire['request_json']), json.loads(wire['response_json'])
            deliveries.append((p, d, req, resp, response_content(resp)))
    rows = []
    for n, entry in enumerate(selection['entries'], 1):
        journal = (OUT / entry['retained']).read_text()
        matches = [(p, d, req, resp, content) for p, d, req, resp, content in deliveries if len(content) > 30 and content in journal]
        row = dict(entry, ordinal=n, matches=len(matches))
        if len(matches) == 1:
            p, d, req, resp, content = matches[0]
            output = d.get('output', {})
            user = '\n'.join(m.get('content', '') for m in req.get('messages', []) if m.get('role') == 'user')
            page = output.get('page') or d.get('page')
            row.update({'delivery': str(p.relative_to(OUT)), 'input_kind': output.get('input_kind'),
                        'output_chars': len(content), 'words': len(content.split()),
                        'tokens': resp.get('usage', {}).get('completion_tokens', resp.get('eval_count')),
                        'allowance': req.get('max_tokens', req.get('options', {}).get('num_predict')),
                        'finish': resp.get('choices', [{}])[0].get('finish_reason', resp.get('done_reason')),
                        'usage': resp.get('usage'), 'request_controls': {k: req[k] for k in ('temperature', 'top_p', 'top_k', 'think', 'max_tokens') if k in req},
                        'page': page, 'input_bytes': len(user.encode()), 'input_sha256': sha(user.encode()),
                        'system_prompts_sha256': [sha(m['content'].encode()) for m in req.get('messages', []) if m.get('role') == 'system'],
                        'next_lines': re.findall(r'^NEXT:\s*(.*)$', content, re.M),
                        'study_notes': re.findall(r'^STUDY_NOTE:\s*(.*)$', content, re.M),
                        'study_questions': re.findall(r'^STUDY_QUESTION:\s*(.*)$', content, re.M),
                        'response_sha256': sha(content.encode()),
                        'prior_choice_supplied': 'PREVIOUS RESPONSE CHOICE' in user,
                        'admission': resp.get('input_admission')})
            for suffix, body in [('response', content), ('input', user), ('system', '\n'.join(m['content'] for m in req.get('messages', []) if m.get('role') == 'system'))]:
                path = OUT / 'readings' / f'{n:02d}-{suffix}.txt'
                path.parent.mkdir(exist_ok=True, mode=0o700)
                path.write_text(body); path.chmod(0o600)
        rows.append(row)
    complete = [r for r in rows if r['matches'] == 1]
    summary = {'selected': len(rows), 'uniquely_linked': len(complete), 'neighbor_modes': dict(Counter(r['mode_prefix'] for r in selection['neighboring_journal_files'])),
               'kinds': dict(Counter(r['input_kind'] for r in complete)), 'finishes': dict(Counter(r['finish'] for r in complete)),
               'allowances': dict(Counter(str(r['allowance']) for r in complete)),
               'unique_responses': len({r['response_sha256'] for r in complete})}
    for key in ('tokens', 'words', 'output_chars', 'input_bytes'):
        values = [r[key] for r in complete if r[key] is not None]
        summary[key] = {'n': len(values), 'min': min(values), 'median': statistics.median(values), 'max': max(values)} if values else None
    summary['study_note_updates'] = sum(bool(r['study_notes']) for r in complete)
    summary['study_question_updates'] = sum(bool(r['study_questions']) for r in complete)
    write(OUT / 'linked-sequence.json', {'summary': summary, 'rows': rows})
    print(json.dumps(summary, indent=2))

def audit():
    sequence = json.loads((OUT / 'linked-sequence.json').read_text())
    providers = [(p, json.loads(p.read_text())) for p in (OUT / 'provider').glob('**/*.json')]
    helper = Path('/Users/v/other/worktrees/journal-coherence-20260911/bridge-stage-01/helpers/astrid-source-study')
    assert sha(helper.read_bytes()) == '0aa85909094a849ba4a96d53385162273744cf082031afd12cdecbac9e39d746'
    rows, intervals = [], {}
    for row in sequence['rows']:
        n = row['ordinal']
        content = (OUT / 'readings' / f'{n:02d}-response.txt').read_text()
        matches = [(p, d) for p, d in providers if d['accepted_completion'] == content]
        assert len(matches) == 1, (n, len(matches))
        p, d = matches[0]
        raw = json.loads(d['attempt']['response_json'])
        controls = raw['coupled_generation_v1']
        req = json.loads(d['attempt']['request_json'])
        admission = d['attempt']['admission']
        user_message = req['messages'][admission['message_index']]['content'].encode()
        admitted = user_message[admission['content_start_byte']:admission['content_end_byte']]
        assert sha(admitted) == admission['admitted_text_sha256']
        feedback = subprocess.run([str(helper)], input=json.dumps({'operation': 'analyze_response', 'text': content}), text=True, capture_output=True, check=True)
        # This operation returns before Reader/catalog construction; no live state is supplied.
        choice = json.loads(feedback.stdout)
        rows.append({'ordinal': n, 'provider_receipt': str(p.relative_to(OUT)),
                     'raw_equals_accepted': response_content(raw) == content,
                     'complete_input_admission': admission['offered_bytes'] == admission['admitted_end_byte'] and admission['source_start_byte'] == 0,
                     'input_admission': admission,
                     'server_controls': controls['controls'],
                     'termination': controls['termination'],
                     'filtered_tokens': controls['filtered_tokens'],
                     'cleanup_removed_chars': controls['cleanup_removed_chars'],
                     'timing': raw.get('model_qos_timing_v1'),
                     'stateless_released_parser_inspection': choice})
        if row['page']:
            page = row['page']; key = page['source'] + '@' + page['revision']['sha256']
            intervals.setdefault(key, []).append((page['start']['byte'], page['end']['byte']))
    coverage = []
    for key, spans in intervals.items():
        merged = []
        for lo, hi in sorted(spans):
            if merged and lo <= merged[-1][1]:
                merged[-1][1] = max(hi, merged[-1][1])
            else:
                merged.append([lo, hi])
        coverage.append({'source_revision': key, 'deliveries': len(spans), 'distinct_exact_spans': len(set(spans)),
                         'delivered_bytes': sum(hi-lo for lo,hi in spans), 'unique_bytes_within_selected_sequence': sum(hi-lo for lo,hi in merged), 'union': merged})
    summary = {'provider_exact_links': len(rows), 'raw_equals_accepted': sum(r['raw_equals_accepted'] for r in rows),
               'complete_input_admission': sum(r['complete_input_admission'] for r in rows),
               'model_eos_terminations': sum(r['termination']['model_eos_reached'] for r in rows),
               'thinking_enabled': sum(r['server_controls']['thinking'] for r in rows),
               'filtered_tokens': sum(r['filtered_tokens'] for r in rows), 'cleanup_removed_chars': sum(r['cleanup_removed_chars'] for r in rows),
               'source_page_deliveries': sum(r['deliveries'] for r in coverage),
               'distinct_exact_page_spans': sum(r['distinct_exact_spans'] for r in coverage),
               'source_files': len({r['source_revision'].split('@')[0] for r in coverage}),
               'delivered_source_bytes': sum(r['delivered_bytes'] for r in coverage),
               'unique_source_bytes_within_selected_sequence': sum(r['unique_bytes_within_selected_sequence'] for r in coverage)}
    intervals_s = [b['filename_epoch'] - a['filename_epoch'] for a,b in zip(sequence['rows'], sequence['rows'][1:])]
    summary['completion_spacing_seconds'] = {'n': len(intervals_s), 'min': min(intervals_s), 'median': statistics.median(intervals_s), 'max': max(intervals_s)}
    active_ms = [r['timing']['active_generation_and_reservoir_ms'] for r in rows]
    summary['worker_active_ms'] = {'n': len(active_ms), 'min': min(active_ms), 'median': statistics.median(active_ms), 'max': max(active_ms)}
    write(OUT / 'provider-and-coverage-audit.json', {'summary': summary, 'rows': rows, 'source_coverage': coverage,
            'limits': 'Completed-journal selection, not all attempts. Reused source bytes are measured only within this selected sequence. Stateless parser inspection is not historical execution.'})
    print(json.dumps(summary, indent=2))

def log_supplement():
    """Extend the recorded partial log tail by one adjacent bounded block."""
    initial = json.loads((OUT / 'runtime/log-selection.json').read_text())
    selection = json.loads((OUT / 'selection.json').read_text())
    old_text = (OUT / 'runtime/selected-bridge-log.txt').read_text()
    assert sha(old_text.encode()) == initial['retained_sha256']
    end = initial['tail_start_byte']
    start = max(0, end - 4 * 1024 * 1024)
    with Path(initial['source']).open('rb') as handle:
        handle.seek(start)
        raw = handle.read(end - start)
    clean = re.sub(r'\x1b\[[0-9;]*m', '', raw.decode('utf-8', errors='replace'))
    rows = []
    first = None
    for line in clean.splitlines() + old_text.splitlines():
        match = re.match(r'(2026-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z)', line)
        if not match:
            continue
        stamp = datetime.fromisoformat(match[1].replace('Z', '+00:00')).timestamp()
        first = stamp if first is None else min(first, stamp)
        if selection['span_start_epoch'] <= stamp <= CUTOFF and any(s in line for s in (
                'Astrid chose NEXT:', 'exchange complete', 'autonomous: ', 'restored conversation state', 'operator drain', 'checkpoint persisted')):
            rows.append((stamp, line))
    rows = sorted(set(rows))
    text = '\n'.join(line for _, line in rows) + '\n'
    path = OUT / 'runtime/covered-bridge-log.txt'
    path.write_text(text); path.chmod(0o600)
    audit_rows = json.loads((OUT / 'provider-and-coverage-audit.json').read_text())['rows']
    links = []
    for entry, inspected in zip(selection['entries'], audit_rows):
        candidates = [(stamp, line.split('Astrid chose NEXT:', 1)[1].strip()) for stamp, line in rows
                      if 'Astrid chose NEXT:' in line and 0 <= stamp - entry['filename_epoch'] < 30]
        links.append({'journal': Path(entry['source']).name, 'matches': candidates,
                      'same_as_stateless_inspection': len(candidates) == 1 and candidates[0][1] == inspected['stateless_released_parser_inspection']['selected_next']})
    result = {'source': initial['source'], 'adjacent_read_start': start, 'adjacent_read_end': end,
              'adjacent_raw_sha256': sha(raw), 'initial_partial_capture_retained': True,
              'full_selected_span_covered': first <= selection['span_start_epoch'],
              'first_timestamp': datetime.fromtimestamp(first, timezone.utc).isoformat(),
              'retained_sha256': sha(text.encode()), 'matches': links,
              'limits': 'Temporal journal-to-choice linkage, corroborated by exact choice text; not an action-ID or queue/dispatch join.'}
    write(OUT / 'runtime/log-supplement.json', result)
    print(json.dumps({'coverage': result['full_selected_span_covered'], 'corroborated_choices': sum(r['same_as_stateless_inspection'] for r in links), 'selected': len(links)}))

if __name__ == '__main__':
    {'capture': capture, 'analyze': analyze, 'audit': audit, 'log_supplement': log_supplement}[sys.argv[1]]()
