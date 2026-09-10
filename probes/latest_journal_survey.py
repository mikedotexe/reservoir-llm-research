"""Verify a frozen ten-file journal survey; no live writes or generation calls.

Usage: python3 probes/latest_journal_survey.py research/outputs/<capture>
Selection was frozen by journal-file modification/completion observation, unfiltered
by mode. Linked generations require exact response inclusion in the retained file.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
from collections import Counter


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(root):
    selection = json.loads((root / 'selection.json').read_text())
    links = json.loads((root / 'generation-links.json').read_text())
    report = dict(cutoff_utc=selection['cutoff_utc'], selection=selection['selection'],
                  entries=[], minime_generations=[], astrid_study=None,
                  generation_is_not_independent_episode=True, live_writes=0)
    for entry in selection['entries']:
        raw = (root / entry['retained']).read_bytes()
        assert digest(raw) == entry['sha256']
        text = raw.decode()
        report['entries'].append(dict(entry, mode=(re.search(r'^Mode: (.*)$', text, re.M).group(1)
                                                  if entry['being'] == 'astrid' else 'self_study'),
                                     next_lines=re.findall(r'^(?:NEXT: )?(SELF_STUDY .*|RELATE .*|SEARCH .*)$', text, re.M)))
    for link in links:
        raw = (root / link['retained']).read_bytes()
        assert digest(raw) == link['sha256']
        generation = json.loads(raw)
        if 'response_json' in generation:
            response = json.loads(generation['response_json'])
            request = json.loads(generation['request_json'])
            text = response['choices'][0]['message']['content']
            report['astrid_study'] = dict(tokens=response['usage']['completion_tokens'],
                finish=response['choices'][0]['finish_reason'], allowance=request['max_tokens'],
                input_kind=generation['output']['input_kind'], source_page=generation['output']['page'])
        else:
            text = generation['response_text']
        for name in link['matches']:
            assert text in (root / name).read_text()
        if generation.get('being') == 'minime':
            user = '\n'.join(m.get('content', '') for m in generation['messages'] if m['role'] == 'user')
            current = user.split('RECALLED ACCOUNT', 1)[0]
            candidates = re.findall(r'^SELF_STUDY OPEN (\S+) (\d+) —', current, re.M)
            report['minime_generations'].append(dict(generation_id=generation['generation_id'],
                journal=link['matches'][0], tokens=generation['backend_timing']['eval_count'],
                finish=generation['backend_timing']['native_finish'],
                allowance=generation['generation_controls']['adapter_sent']['num_predict'],
                navigation_page=re.search(r'Navigation page (\d+/\d+)', current).group(1),
                candidates=len(candidates), candidate_paths=dict(Counter(p for p, _ in candidates))))
    source = json.loads((root / 'source-evidence.json').read_text())
    for row in source['snapshots']:
        assert digest((root / row['retained']).read_bytes()) == row['sha256']
    report['source_scan'] = source['scan']
    report['counts'] = dict(Counter(e['being'] for e in report['entries']))
    assert report['counts'] == {'minime': 5, 'astrid': 5}
    assert len(report['minime_generations']) == 5
    (root / 'verified-survey.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ('counts', 'astrid_study', 'minime_generations')}, indent=2))


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
