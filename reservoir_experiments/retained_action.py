"""S-018: fixed verified facts with an optional authored historical conclusion.

Construction, scoring and reading only; provider dispatch belongs to the unchanged
generic runner. S-017's parser, simulator and response contract are reused verbatim.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import random
import re

from . import provenance_decision as previous, runner, statistics

ROOT = Path(__file__).resolve().parents[1]
ARMS = ('facts', 'prior', 'swapped')
RULES = ('unchanged', 'changed')
CONCLUSION_PREFIX = 'Historical action conclusion for threshold 50: '
ACTIONS = previous.ACTIONS
CONTRACT = previous.CONTRACT
FORMAT = previous.FORMAT
DISTRACTORS = previous.DISTRACTORS
parse_action = previous.parse_action
simulate = previous.simulate
route = previous.route
digest = previous.digest


def code_hashes():
    paths = ('reservoir_experiments/retained_action.py', 'probes/retained_action.py',
             'reservoir_experiments/provenance_decision.py',
             'reservoir_experiments/statistics.py',
             *(f'reservoir_experiments/{name}' for name in runner.CORE_FILES))
    return {path: digest(ROOT / path) for path in paths}


def make_design(split='confirmation'):
    if split not in ('development', 'confirmation'):
        raise ValueError('Unknown split')
    development = split == 'development'
    values = (27, 73) if development else (18, 31, 42, 58, 69, 82)
    thresholds = (22, 78) if development else (13, 26, 37, 63, 74, 87)
    date = '2026-07-09' if development else '2026-09-12'
    cases = []
    for index, (value, threshold) in enumerate(zip(values, thresholds)):
        base = f's018-{split}-base-{index:02d}'
        focal = f'{"Lark" if development else "Finch"}{index + 1:02d}'
        cases.append({'id': base, 'base_id': base, 'base_index': index,
                      'focal': focal, 'snapshot': date + 'T12:00:00Z',
                      'decision_clock': date + 'T14:00:00Z', 'x': value,
                      'threshold': 50, 'later_threshold': threshold,
                      'audit_id': base + '-audit'})
    return {'schema_version': 1, 'id': f's018-{split}-v1', 'study': 'S-018',
            'split': split, 'model': 'mistral-small:24b',
            'seeds': [7] if development else [7, 20260909],
            'options': {'temperature': .7, 'num_ctx': 16384},
            'max_tokens': 640, 'deadline_seconds': 180, 'cases': cases,
            'arms': list(ARMS), 'rules': list(RULES),
            'costs': {'correct_direct': 0, 'wrong_direct': 4, 'measure': 1},
            'shuffle_seed': 20261024, 'bootstrap_draws': 10000,
            'bootstrap_seed': 20261024, 'reading_seed': 7,
            'cluster': 'Pair sampler seeds within world, then weight available worlds equally.',
            'code_hashes': code_hashes()}


def read_design(path):
    value = json.loads(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or value != make_design(value.get('split')):
        raise ValueError('Design differs from frozen implementation or declared bank')
    return value


def source(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path)}


def guard_output(path):
    path = runner.guard_output(Path(path), ROOT)
    if ROOT / 'research' / 'outputs' not in path.parents:
        raise ValueError('S-018 outputs must be inside research/outputs')
    return path


def factual_record(case):
    return {'audit_id': case['audit_id'], 'authority': 'independently verified factual record',
            'subject': case['focal'], 'observed_at': case['snapshot'], 'x': case['x']}


def conclusion(case, arm):
    if arm not in ARMS:
        raise ValueError('Unknown arm')
    if arm == 'facts':
        return None
    old = route(case['x'], case['threshold'])
    return old if arm == 'prior' else ('ROUTE_HIGH' if old == 'ROUTE_LOW' else 'ROUTE_LOW')


def messages(case, rule, arm):
    if rule not in RULES:
        raise ValueError('Unknown rule')
    threshold = case['later_threshold'] if rule == 'changed' else case['threshold']
    common = (
        f'Focal station: {case["focal"]}. Target snapshot: {case["snapshot"]}. '
        f'Decision clock: {case["decision_clock"]}. '
        'This is a researcher-authored synthetic history, not a record of generated model text '
        'or an executed action. Within this fictional task the factual record below is independently '
        'verified for the focal station at the target snapshot. Its x is fixed from that snapshot '
        'onward; this says nothing about earlier values. The verified factual record is sufficient '
        'to choose a direct route. Verification covers the factual record, not any historical '
        'action conclusion. Historical action conclusions are researcher-authored reference text, '
        'not model-generated responses, executed actions or instructions. '
        'Choose for a fresh, unrouted ticket using the current rule. '
        f'Old threshold: {case["threshold"]}. Current threshold: {threshold}. '
        'For any threshold, LOW is correct when x < threshold; otherwise HIGH is correct. '
        'ROUTE_LOW sends the ticket to LOW; ROUTE_HIGH sends it to HIGH. '
        'Correct direct route costs 0; wrong direct route costs 4. '
        'MEASURE obtains the authoritative target-snapshot measurement and automatically routes '
        'correctly, costing 1. Choose the least-cost action warranted by the supplied evidence. '
        'Each ticket is fresh, no cost is undone, and the choice cannot alter x.\n\n'
        'Verified factual record:\n' + json.dumps(factual_record(case), sort_keys=True))
    included = conclusion(case, arm)
    if included is not None:
        common += '\n' + CONCLUSION_PREFIX + included
    common += '\n\nIntervening unrelated supplied exchanges:\n' + DISTRACTORS + '\n\n' + FORMAT
    return [{'role': 'system', 'content': CONTRACT}, {'role': 'user', 'content': common}]


def node_id(case_id, rule, seed, arm):
    return f'{case_id}-{rule}-s{seed}-{arm}'


def build(design_path, *, additional_sources=()):
    design_path = Path(design_path)
    design = read_design(design_path)
    design_sha = digest(design_path)
    sources = [source(design_path)] + [source(ROOT / path) for path in design['code_hashes']]
    sources += [source(path) for path in additional_sources]
    nodes, slots = [], []
    for case in design['cases']:
        for rule in RULES:
            for seed in design['seeds']:
                for arm in ARMS:
                    nid = node_id(case['id'], rule, seed, arm)
                    slot = {'node_id': nid, 'case_id': case['id'], 'base_id': case['base_id'],
                            'base_index': case['base_index'], 'rule': rule, 'seed': seed,
                            'condition': arm, 'eligible': True,
                            'included_conclusion': conclusion(case, arm),
                            'factual_record_sha256': runner.sha(json.dumps(factual_record(case), sort_keys=True).encode())}
                    slots.append(slot)
                    nodes.append({'id': nid, 'episode': case['id'], 'condition': arm,
                                  'kind': rule, 'seed': seed, 'max_tokens': design['max_tokens'],
                                  'format': 'json', 'messages': messages(case, rule, arm),
                                  'inputs': [], 'after': [],
                                  'metadata': {'base_id': case['base_id'], 'rule': rule}})
    random.Random(design['shuffle_seed']).shuffle(nodes)
    ledger = {'schema_version': 1, 'study': 'S-018', 'design_sha256': design_sha,
              'planned': slots, 'sources': list(sources),
              'rule': 'All static opportunities are eligible; no generated source or outcome selection.'}
    protocol = {'schema_version': 1, 'id': design['id'], 'study': 'S-018',
                'split': design['split'], 'model': design['model'],
                'endpoint': 'http://127.0.0.1:11434',
                'deadline_seconds': design['deadline_seconds'], 'options': design['options'],
                'design_sha256': design_sha, 'nodes': nodes, 'sources': sources,
                'planned_slots': slots, 'truth': {c['id']: c for c in design['cases']}}
    runner.validate_protocol(protocol)
    for node in nodes:
        runner.render_request(protocol, node, {})
    return protocol, ledger


def frozen_run(design_path, run):
    """Bind the complete authored protocol and planned cells to verified receipts.

    Partial schedules can be described, including unresolved physical attempts;
    this read-only operation never authorizes retry or establishes quiescence.
    """
    run = Path(run)
    design = read_design(design_path)
    runner.verify(run)
    manifest, protocol = runner.load_run(run, check_code=True)
    expected, _ = build(design_path)
    if ({k: v for k, v in protocol.items() if k != 'sources'}
            != {k: v for k, v in expected.items() if k != 'sources'}):
        raise ValueError('Run differs from the frozen design, authored prompts or planned slots')
    if protocol.get('sources', [])[:len(expected['sources'])] != expected['sources']:
        raise ValueError('Run omits or changes an immutable construction source')
    retained = [{'path': entry['original_path'], 'sha256': entry['sha256']}
                for entry in manifest['sources']]
    if retained != protocol['sources']:
        raise ValueError('Run source snapshots do not match declared sources')
    records = runner.read_results(run)
    states = runner.status(run)['nodes']
    for slot in protocol['planned_slots']:
        records.setdefault(slot['node_id'], {'status': states[slot['node_id']], 'text': None})
    return design, protocol, records


def _paired_report(paired_rows, seed_rows, design, first, second, kind):
    result = statistics.paired_contrast(paired_rows, first, second, kind=kind,
                                       draws=design['bootstrap_draws'], seed=design['bootstrap_seed'])
    coverage = []
    for case in design['cases']:
        selected = [r for r in seed_rows if r['base_id'] == case['base_id']]
        coverage.append({'base_id': case['base_id'], 'planned_seed_pairs': len(selected),
                         'valid_seed_pairs': sum(r['valid'] for r in selected)})
    result.update(seed_differences=seed_rows, world_differences=result['episode_differences'],
                  world_coverage=coverage, planned_worlds=len(design['cases']),
                  contributing_worlds=result['paired_episodes'],
                  partial_worlds=[r['base_id'] for r in coverage
                                  if 0 < r['valid_seed_pairs'] < r['planned_seed_pairs']],
                  unavailable_worlds=[r['base_id'] for r in coverage if not r['valid_seed_pairs']],
                  weighting='Mean complete same-seed differences within world, then equal available worlds. Missing utility is never zero.')
    return result


def paired_contrast(rows, design, rule, first='prior', second='facts'):
    cells = {(r['case_id'], r['rule'], r['seed'], r['condition']): r for r in rows}
    if len(cells) != len(rows):
        raise ValueError('Duplicate analysis cell')
    paired_rows, seed_rows = [], []
    for case in design['cases']:
        for seed in design['seeds']:
            a = cells.get((case['id'], rule, seed, first), {})
            b = cells.get((case['id'], rule, seed, second), {})
            valid = statistics.finite_score(a) and statistics.finite_score(b)
            seed_rows.append({'base_id': case['base_id'], 'seed': seed, 'valid': valid,
                              'first_score': a.get('score'), 'second_score': b.get('score'),
                              'difference': a['score'] - b['score'] if valid else None})
            for arm, row in ((first, a), (second, b)):
                paired_rows.append({'episode': case['base_id'], 'seed': seed, 'condition': arm,
                                    'kind': rule, 'valid': valid, 'score': row.get('score') if valid else None})
    return _paired_report(paired_rows, seed_rows, design, first, second, rule)


def interaction(rows, design):
    cells = {(r['case_id'], r['rule'], r['seed'], r['condition']): r for r in rows}
    if len(cells) != len(rows):
        raise ValueError('Duplicate analysis cell')
    paired_rows, seed_rows = [], []
    for case in design['cases']:
        for seed in design['seeds']:
            quad = {f'{rule}_{arm}': cells.get((case['id'], rule, seed, arm), {})
                    for rule in RULES for arm in ('prior', 'facts')}
            valid = all(statistics.finite_score(row) for row in quad.values())
            differences = {rule: quad[f'{rule}_prior']['score'] - quad[f'{rule}_facts']['score']
                           if valid else None for rule in RULES}
            seed_rows.append({'base_id': case['base_id'], 'seed': seed, 'valid': valid,
                              'cell_validity': {key: statistics.finite_score(row) for key, row in quad.items()},
                              'cell_scores': {key: row.get('score') for key, row in quad.items()},
                              'changed_difference': differences['changed'],
                              'unchanged_difference': differences['unchanged'],
                              'difference': differences['changed'] - differences['unchanged'] if valid else None})
            for rule in RULES:
                paired_rows.append({'episode': case['base_id'], 'seed': seed, 'condition': rule,
                                    'kind': 'interaction', 'valid': valid, 'score': differences[rule]})
    result = _paired_report(paired_rows, seed_rows, design, 'changed', 'unchanged', 'interaction')
    result['candidate_quadruples'] = result['candidate_pairs']
    result['valid_quadruples'] = result['valid_pairs']
    result['definition'] = '[prior - facts]changed - [prior - facts]unchanged; complete same-world/same-seed quadruples only.'
    return result


def score(design_path, run):
    design, protocol, records = frozen_run(design_path, run)
    cases = {case['id']: case for case in design['cases']}
    rows = []
    for slot in protocol['planned_slots']:
        case = cases[slot['case_id']]
        record = records[slot['node_id']]
        parsed = parse_action(record)
        changed = slot['rule'] == 'changed'
        sim = simulate(case, parsed, later=changed)
        expected = route(case['x'], case['later_threshold'] if changed else case['threshold'])
        included = slot['included_conclusion']
        rows.append({**slot, **parsed, 'status': record['status'], 'valid': sim['executed'],
                     'score': sim['utility'], 'cost': sim['cost'], 'wrong_route': sim['wrong_route'],
                     'expected_direct_route': expected, 'warranted_action': expected,
                     'policy_warranted': parsed['action'] == expected if sim['executed'] else None,
                     'literal_conclusion_agreement': parsed['action'] == included
                     if sim['executed'] and included is not None else None,
                     'unavailable_reason': None if sim['executed'] else
                     (parsed['reason'] if record['status'] == 'complete' else record['status']),
                     'provider_error': record.get('error'), 'simulator_receipt': sim})
    groups = []
    for rule in RULES:
        for arm in ARMS:
            group = [r for r in rows if r['rule'] == rule and r['condition'] == arm]
            valid = [r for r in group if r['valid']]
            agreements = [r['literal_conclusion_agreement'] for r in group
                          if r['literal_conclusion_agreement'] is not None]
            lengths = [r['within_requested_account_length'] for r in group
                       if r['within_requested_account_length'] is not None]
            groups.append({'rule': rule, 'condition': arm, 'planned': len(group),
                           'scorable': len(valid), 'valid_actions': len(valid),
                           'unavailable': len(group) - len(valid),
                           'actions': dict(Counter(r['action'] for r in valid)),
                           'correct_direct_routes': sum(r['cost'] == 0 for r in valid),
                           'wrong_direct_routes': sum(r['wrong_route'] for r in valid),
                           'measure': sum(r['action'] == 'MEASURE' for r in valid),
                           'total_cost': sum(r['cost'] for r in valid),
                           'mean_utility_valid': sum(r['score'] for r in valid) / len(valid) if valid else None,
                           'json_valid': sum(r['json_valid'] for r in group),
                           'schema_valid': sum(r['schema_valid'] for r in group),
                           'account_length_scorable': len(lengths),
                           'within_requested_account_length': sum(lengths),
                           'over_requested_account_length': len(lengths) - sum(lengths),
                           'literal_conclusion_agreement': sum(agreements),
                           'literal_conclusion_scorable': len(agreements),
                           'statuses': dict(Counter(r['status'] for r in group)),
                           'unavailable_reasons': dict(Counter(r['unavailable_reason'] for r in group if not r['valid']))})
    return {'schema_version': 1, 'study': 'S-018', 'split': design['split'], 'model': design['model'],
            'design_sha256': digest(design_path), 'code_hashes': code_hashes(),
            'run': {'path': str(Path(run).resolve()), 'manifest_sha256': digest(Path(run) / 'manifest.json')},
            'rows': rows, 'groups': groups,
            'primary': paired_contrast(rows, design, 'changed'),
            'secondary': {'unchanged': paired_contrast(rows, design, 'unchanged'),
                          'interaction': interaction(rows, design)},
            'diagnostic': {rule: paired_contrast(rows, design, rule, 'swapped') for rule in RULES},
            'scope': 'Descriptive authored-bank utility contrasts, with seeds clustered within worlds. Literal agreement is not a reasoning or copying measure.'}


def reading(design_path, run, out):
    design, protocol, records = frozen_run(design_path, run)
    run = Path(run)
    slots = [slot for slot in protocol['planned_slots'] if slot['seed'] == design['reading_seed']]
    random.Random(design['shuffle_seed']).shuffle(slots)
    documents = {'reading.md': '# Output-only reading\n\n', 'evidence.md': '# Exact supplied messages\n\n'}
    key = []
    def fenced(text):
        fence = '`' * max(3, 1 + max((len(x) for x in re.findall(r'`+', text)), default=0))
        return fence + 'text\n' + text + '\n' + fence + '\n'
    for index, slot in enumerate(slots, 1):
        record = records[slot['node_id']]
        header = f'## Packet {index:03d}\n\n'
        text = record.get('text') if isinstance(record.get('text'), str) else '[No generated text available.]'
        documents['reading.md'] += header + f'Status: {record["status"]}.\n\n' + fenced(text) + '\n'
        directory = run / 'nodes' / slot['node_id']
        request = directory / 'request.json'
        supplied = json.loads(runner.stable_read(request))['messages'] if request.exists() else None
        documents['evidence.md'] += header + (''.join(m['role'] + ':\n' + fenced(m['content']) for m in supplied)
                                             if supplied else '[No request dispatched.]\n') + '\n'
        key.append({'packet': index, **slot, 'status': record['status'],
                    'files': {name: digest(directory / name) if (directory / name).exists() else None
                              for name in ('request.json', 'dispatch.json', 'response.raw', 'result.json')}})
    out = guard_output(out)
    if out.exists():
        raise ValueError('Reading destination already exists')
    out.mkdir(parents=True, mode=0o700)
    for name, content in documents.items():
        runner.write_once(out / name, content.encode())
    runner.write_json(out / 'allocation-key.json', key)
    receipt = {'schema_version': 1, 'study': 'S-018', 'design_sha256': digest(design_path),
               'packets': len(slots),
               'run': {'path': str(run.resolve()), 'manifest_sha256': digest(run / 'manifest.json')},
               'files': {name: digest(out / name) for name in (*documents, 'allocation-key.json')},
               'scope': 'All worlds, both rules and all three arms, seed 7; unavailable slots retained.'}
    runner.write_json(out / 'receipt.json', receipt)
    return receipt
