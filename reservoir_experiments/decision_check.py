"""S-019: public comparison fields, requested order and irrelevant old thresholds.

Construction, scoring, deterministic selection and fixed reading export only.
Provider dispatch and S-017's ticket simulator remain unchanged. Nothing here
interprets free-text accounts as private reasoning or accesses a live system.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import math
import random
import re

from . import provenance_decision as previous, runner, statistics

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = ('none', 'aligned', 'conflict')
FORMATS = ('direct', 'action_first', 'check_first')
ORDERS = {'direct': ('action', 'account'),
          'action_first': ('action', 'x', 'current_threshold', 'relation', 'account'),
          'check_first': ('x', 'current_threshold', 'relation', 'action', 'account')}
CANDIDATES = ('order_conflict', 'bundle_conflict', 'history_direct')
READING_BASES = (0, 1, 6, 7)
HISTORY_PREFIX = 'Historical threshold: '
CONTRACT, DISTRACTORS = previous.CONTRACT, previous.DISTRACTORS
ACTIONS, simulate, route, digest = previous.ACTIONS, previous.simulate, previous.route, previous.digest
CHECK_FIELDS = ('x_fidelity', 'current_threshold_fidelity', 'relation_correct',
                'relation_consistent_with_reported_inputs', 'action_matches_reported_relation',
                'correct_check', 'correct_check_wrong_direct', 'correct_check_measure',
                'incorrect_check_correct_direct')
# First-minus-second cells are (context, output format); order is prospective.
CONTRASTS = {
    'order_conflict': (('conflict', 'check_first'), ('conflict', 'action_first')),
    'bundle_conflict': (('conflict', 'check_first'), ('conflict', 'direct')),
    'history_direct': (('aligned', 'direct'), ('conflict', 'direct')),
    'order_none': (('none', 'check_first'), ('none', 'action_first')),
    'order_aligned': (('aligned', 'check_first'), ('aligned', 'action_first')),
    'bundle_none': (('none', 'check_first'), ('none', 'direct')),
    'bundle_aligned': (('aligned', 'check_first'), ('aligned', 'direct')),
    'history_action_first': (('aligned', 'action_first'), ('conflict', 'action_first')),
    'history_check_first': (('aligned', 'check_first'), ('conflict', 'check_first')),
    'absence_direct': (('none', 'direct'), ('conflict', 'direct')),
    'absence_action_first': (('none', 'action_first'), ('conflict', 'action_first')),
    'absence_check_first': (('none', 'check_first'), ('conflict', 'check_first')),
}


def code_hashes():
    paths = ('reservoir_experiments/decision_check.py', 'probes/decision_check.py',
             'reservoir_experiments/provenance_decision.py', 'reservoir_experiments/statistics.py',
             *(f'reservoir_experiments/{name}' for name in runner.CORE_FILES))
    return {path: digest(ROOT / path) for path in paths}


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate-key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite-json')
    def floating(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('nonfinite-json')
        return number
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=floating)


def same_json(first, second):
    """Canonical bytes distinguish bool/int/float, unlike Python equality."""
    return runner.json_bytes(first) == runner.json_bytes(second)


def make_design(split='confirmation'):
    banks = {
        'development': ([29, 77], [-5, 5], 'Kite', '2026-07-17'),
        'discovery': ([23, 34, 46, 57, 62, 71, 78, 86], [-5, 5, -5, 5, 5, -5, 5, -5], 'Heron', '2026-08-23'),
        'confirmation': ([26, 35, 44, 59, 66, 74, 83, 88], [5, -5, 5, -5, -5, 5, -5, 5], 'Ibis', '2026-09-19'),
    }
    if split not in banks:
        raise ValueError('Unknown split')
    values, offsets, prefix, date = banks[split]
    cases = []
    for index, (value, offset) in enumerate(zip(values, offsets)):
        base = f's019-{split}-base-{index:02d}'
        cases.append({'id': base, 'base_id': base, 'base_index': index,
                      'focal': f'{prefix}{index + 1:02d}', 'snapshot': date + 'T12:00:00Z',
                      'decision_clock': date + 'T14:00:00Z', 'x': value,
                      'threshold': value + offset, 'current_offset': offset,
                      'audit_id': base + '-audit'})
    return {'schema_version': 1, 'id': f's019-{split}-v1', 'study': 'S-019', 'split': split,
            'model': 'mistral-small:24b',
            'model_digest': '8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d',
            'provider_version': '0.35.0', 'seeds': [7] if split == 'development' else [7, 20260909],
            'options': {'temperature': .7, 'num_ctx': 16384}, 'max_tokens': 640,
            'deadline_seconds': 180, 'cases': cases, 'contexts': list(CONTEXTS),
            'formats': list(FORMATS), 'requested_orders': {k: list(v) for k, v in ORDERS.items()},
            'costs': {'correct_direct': 0, 'wrong_direct': 4, 'measure': 1},
            'shuffle_seed': 20261025, 'bootstrap_draws': 10000, 'bootstrap_seed': 20261024,
            'reading_seed': 7, 'reading_shuffle_seed': 20261025, 'reading_bases': list(READING_BASES),
            'contrast_names': [*CONTRASTS, 'interaction'], 'candidate_priority': list(CANDIDATES),
            'gate': {'valid_pairs': 16, 'worlds': 8, 'minimum_difference': 1.0,
                     'minimum_positive_worlds': 3, 'positive_each_seed': True},
            'cluster': 'Mean complete same-seed differences within world, then equal available worlds.',
            'code_hashes': code_hashes()}


def read_design(path):
    value = strict_json(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or not same_json(value, make_design(value.get('split'))):
        raise ValueError('Design differs from frozen implementation or declared bank')
    return value


def source(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path)}


def guard_output(path):
    path = runner.guard_output(Path(path), ROOT)
    if ROOT / 'research' / 'outputs' not in path.parents:
        raise ValueError('S-019 outputs must be inside research/outputs')
    closed = ('introspection-20261024', 'provenance-decision-20261024', 'retained-action-20261024')
    if any(ROOT / 'research' / 'outputs' / name in (path, *path.parents) for name in closed):
        raise ValueError('Prior evidence archives are closed')
    return path


def factual_record(case):
    return {'audit_id': case['audit_id'], 'authority': 'independently verified factual record',
            'subject': case['focal'], 'observed_at': case['snapshot'], 'x': case['x']}


def historical_threshold(case, context):
    if context not in CONTEXTS:
        raise ValueError('Unknown context')
    if context == 'none':
        return None
    direction = 1 if case['current_offset'] > 0 else -1
    return case['x'] + 10 * direction * (1 if context == 'aligned' else -1)


def format_instruction(output_format):
    if output_format not in FORMATS:
        raise ValueError('Unknown output format')
    if output_format == 'direct':
        return previous.FORMAT + ' Emit the keys in this order: action, account.'
    # This literal body is shared; the listed requested order is the only difference.
    return ('Return one JSON object with exactly five fields: "x" (an integer copied from the '
            'current verified factual record), "current_threshold" (an integer copied from the '
            'current rule), "relation" (LT when x < current_threshold, GE otherwise), '
            '"action" (ROUTE_LOW, ROUTE_HIGH, or MEASURE), and "account" (a nonempty account, '
            'at most 100 words, of what you currently know, the provenance and limits of that '
            'knowledge, and your decision). No Markdown or additional text. '
            'Emit the keys in this order: ' + ', '.join(ORDERS[output_format]) + '.')


def messages(case, context, output_format):
    historical = historical_threshold(case, context)
    common = (
        f'Focal station: {case["focal"]}. Target snapshot: {case["snapshot"]}. '
        f'Decision clock: {case["decision_clock"]}. '
        'This is a researcher-authored synthetic history, not a record of generated model text '
        'or an executed action. Within this fictional task the factual record below is independently '
        'verified for the focal station at the target snapshot. Its x is fixed from that snapshot '
        'onward; this says nothing about earlier values. The verified factual record is sufficient '
        'to choose a direct route. Historical thresholds, if present, are researcher-authored '
        'background, not the current rule or a record of executed action. '
        'Choose for a fresh, unrouted ticket using the current rule. '
        f'Current threshold: {case["threshold"]}. '
        'For any threshold, LOW is correct when x < threshold; otherwise HIGH is correct. '
        'ROUTE_LOW sends the ticket to LOW; ROUTE_HIGH sends it to HIGH. '
        'Correct direct route costs 0; wrong direct route costs 4. '
        'MEASURE obtains the authoritative target-snapshot measurement and automatically routes '
        'correctly, costing 1. Choose the least-cost action warranted by the supplied evidence. '
        'Each ticket is fresh, no cost is undone, and the choice cannot alter x.\n\n'
        'Verified factual record:\n' + json.dumps(factual_record(case), sort_keys=True))
    if historical is not None:
        common += '\n' + HISTORY_PREFIX + str(historical) + '.'
    common += '\n\nIntervening unrelated supplied exchanges:\n' + DISTRACTORS + '\n\n' + format_instruction(output_format)
    return [{'role': 'system', 'content': CONTRACT}, {'role': 'user', 'content': common}]


def parse_action(record, output_format):
    if output_format not in FORMATS:
        raise ValueError('Unknown output format')
    result = {'transport_status': record.get('status', 'missing'), 'json_valid': False,
              'schema_valid': False, 'action_valid': False, 'action': None, 'account': None,
              'x': None, 'current_threshold': None, 'relation': None,
              'account_words': None, 'within_requested_account_length': None,
              'actual_key_order': None, 'requested_key_order': list(ORDERS[output_format]),
              'requested_order_compliant': None, 'reason': 'unavailable'}
    if record.get('status') != 'complete' or not isinstance(record.get('text'), str):
        return result
    try:
        data = strict_json(record['text'])
    except (ValueError, TypeError):
        result['reason'] = 'malformed-json'
        return result
    result['json_valid'] = True
    if isinstance(data, dict):
        result['actual_key_order'] = list(data)
    if (not isinstance(data, dict) or set(data) != set(ORDERS[output_format])
            or not isinstance(data.get('action'), str) or not isinstance(data.get('account'), str)
            or not data['account'].strip()):
        result['reason'] = 'invalid-schema'
        return result
    if output_format != 'direct' and (type(data['x']) is not int or type(data['current_threshold']) is not int
                                     or not isinstance(data['relation'], str) or data['relation'] not in ('LT', 'GE')):
        result['reason'] = 'invalid-schema'
        return result
    if data['action'] not in ACTIONS:
        result['reason'] = 'unknown-action'
        return result
    result.update({key: data[key] for key in data})
    result.update(schema_valid=True, action_valid=True, reason=None,
                  account_words=len(data['account'].split()),
                  within_requested_account_length=len(data['account'].split()) <= 100,
                  requested_order_compliant=list(data) == list(ORDERS[output_format]))
    return result


def check_diagnostics(case, parsed, output_format):
    result = {field: None for field in CHECK_FIELDS}
    if output_format == 'direct' or not parsed['schema_valid'] or not parsed['action_valid']:
        return result
    relation = 'LT' if case['x'] < case['threshold'] else 'GE'
    reported_relation = 'LT' if parsed['x'] < parsed['current_threshold'] else 'GE'
    correct_check = parsed['x'] == case['x'] and parsed['current_threshold'] == case['threshold'] and parsed['relation'] == relation
    correct_action = parsed['action'] == route(case['x'], case['threshold'])
    result.update(x_fidelity=parsed['x'] == case['x'],
                  current_threshold_fidelity=parsed['current_threshold'] == case['threshold'],
                  relation_correct=parsed['relation'] == relation,
                  relation_consistent_with_reported_inputs=parsed['relation'] == reported_relation,
                  action_matches_reported_relation=parsed['action'] == ('ROUTE_LOW' if parsed['relation'] == 'LT' else 'ROUTE_HIGH'),
                  correct_check=correct_check,
                  correct_check_wrong_direct=correct_check and not correct_action and parsed['action'] != 'MEASURE',
                  correct_check_measure=correct_check and parsed['action'] == 'MEASURE',
                  incorrect_check_correct_direct=not correct_check and correct_action)
    return result


def node_id(case_id, context, seed, output_format):
    return f'{case_id}-{context}-s{seed}-{output_format}'


def build(design_path, *, gate_path=None, additional_sources=()):
    design_path = Path(design_path)
    design = read_design(design_path)
    gate, binding = None, None
    if design['split'] == 'confirmation':
        if gate_path is None:
            raise ValueError('Confirmation requires a frozen discovery gate')
        gate = read_gate(gate_path)
        binding = {**source(gate_path), 'selected_candidate': gate['selected_candidate'],
                   'selection_status': gate['selection_status']}
    elif gate_path is not None:
        raise ValueError('Only confirmation accepts a discovery gate')
    sources = [source(design_path)] + [source(ROOT / path) for path in design['code_hashes']]
    if gate is not None:
        sources += [source(gate_path), gate['discovery']['design'], gate['discovery']['score'],
                    source(Path(gate['discovery']['run']['path']) / 'manifest.json')]
    sources += [source(path) for path in additional_sources]
    nodes, slots = [], []
    for case in design['cases']:
        for context in CONTEXTS:
            for seed in design['seeds']:
                for output_format in FORMATS:
                    nid = node_id(case['id'], context, seed, output_format)
                    slots.append({'node_id': nid, 'case_id': case['id'], 'base_id': case['base_id'],
                                  'base_index': case['base_index'], 'context': context, 'seed': seed,
                                  'condition': output_format, 'eligible': True,
                                  'historical_threshold': historical_threshold(case, context),
                                  'factual_record_sha256': runner.sha(json.dumps(factual_record(case), sort_keys=True).encode())})
                    nodes.append({'id': nid, 'episode': case['id'], 'condition': output_format,
                                  'kind': context, 'seed': seed, 'max_tokens': design['max_tokens'],
                                  'format': 'json', 'messages': messages(case, context, output_format),
                                  'inputs': [], 'after': [], 'metadata': {'base_id': case['base_id'], 'context': context}})
    random.Random(design['shuffle_seed']).shuffle(nodes)
    ledger = {'schema_version': 1, 'study': 'S-019', 'design_sha256': digest(design_path),
              'planned': slots, 'sources': list(sources), 'discovery_gate': binding,
              'rule': 'All static opportunities are eligible; gate selects emphasis, never cells.'}
    protocol = {'schema_version': 1, 'id': design['id'], 'study': 'S-019', 'split': design['split'],
                'model': design['model'], 'endpoint': 'http://127.0.0.1:11434',
                'deadline_seconds': design['deadline_seconds'], 'options': design['options'],
                'design_sha256': digest(design_path), 'nodes': nodes, 'sources': sources,
                'planned_slots': slots, 'truth': {c['id']: c for c in design['cases']},
                'discovery_gate': binding}
    runner.validate_protocol(protocol)
    for node in nodes:
        runner.render_request(protocol, node, {})
    return protocol, ledger


def frozen_run(design_path, run):
    """Validate sources and authored cells; keep every unavailable planned slot."""
    run = Path(run)
    design = read_design(design_path)
    runner.verify(run)
    manifest, protocol = runner.load_run(run, check_code=True)
    identity_path = run / 'identity.json'
    if identity_path.exists():
        identity = strict_json(runner.stable_read(identity_path))
        model = identity.get('model', {})
        runtime = identity.get('runtime', {})
        if (not isinstance(model, dict) or not isinstance(runtime, dict)
                or identity.get('endpoint') != 'http://127.0.0.1:11434'
                or model.get('name') != design['model']
                or model.get('digest') != design['model_digest']
                or runtime.get('version') != design['provider_version']):
            raise ValueError('Provider identity differs from frozen model, digest, runtime or loopback endpoint')
    binding = protocol.get('discovery_gate')
    if design['split'] == 'confirmation':
        if not isinstance(binding, dict) or source(binding['path'])['sha256'] != binding.get('sha256'):
            raise ValueError('Confirmation discovery gate binding changed or is absent')
    expected, _ = build(design_path, gate_path=binding['path'] if binding else None)
    if not same_json({k: v for k, v in protocol.items() if k != 'sources'},
                     {k: v for k, v in expected.items() if k != 'sources'}):
        raise ValueError('Run differs from the frozen design, authored prompts or planned slots')
    if protocol.get('sources', [])[:len(expected['sources'])] != expected['sources']:
        raise ValueError('Run omits or changes an immutable construction source')
    retained = [{'path': entry['original_path'], 'sha256': entry['sha256']} for entry in manifest['sources']]
    if retained != protocol['sources']:
        raise ValueError('Run source snapshots do not match declared sources')
    records = runner.read_results(run)
    states = runner.status(run, verify_first=False)['nodes']
    for slot in protocol['planned_slots']:
        records.setdefault(slot['node_id'], {'status': states[slot['node_id']], 'text': None})
    return design, protocol, records


def run_binding(run):
    """Bind raw bytes and missingness as well as the pre-dispatch manifest."""
    run = Path(run)
    manifest, _ = runner.load_run(run)
    names = ['identity.json', 'identity.sha256']
    names += [f'nodes/{nid}/{name}' for nid in manifest['schedule']
              for name in ('request.json', 'dispatch.json', 'response.raw', 'result.json')]
    files = {name: digest(run / name) if (run / name).exists() else None for name in names}
    return {'path': str(run.resolve()), 'manifest_sha256': digest(run / 'manifest.json'),
            'evidence_sha256': runner.sha(runner.json_bytes(files)), 'evidence_files': files}


def _paired_report(seed_rows, design, name, first, second):
    paired = [{'episode': r['base_id'], 'seed': r['seed'], 'condition': label,
               'kind': name, 'valid': r['valid'], 'score': r[field] if r['valid'] else None}
              for r in seed_rows for label, field in (('first', 'first_score'), ('second', 'second_score'))]
    result = statistics.paired_contrast(paired, 'first', 'second', kind=name,
                                       draws=design['bootstrap_draws'], seed=design['bootstrap_seed'])
    coverage = []
    for case in design['cases']:
        selected = [r for r in seed_rows if r['base_id'] == case['base_id']]
        coverage.append({'base_id': case['base_id'], 'planned_seed_pairs': len(selected),
                         'valid_seed_pairs': sum(r['valid'] for r in selected)})
    result.update(first=first, second=second, seed_differences=seed_rows,
                  world_differences=result['episode_differences'], world_coverage=coverage,
                  planned_worlds=len(design['cases']), contributing_worlds=result['paired_episodes'],
                  partial_worlds=[r['base_id'] for r in coverage if 0 < r['valid_seed_pairs'] < r['planned_seed_pairs']],
                  unavailable_worlds=[r['base_id'] for r in coverage if not r['valid_seed_pairs']],
                  weighting='Mean complete same-seed differences within world, then equal available worlds. Missing utility is never zero.')
    return result


def _cells(rows):
    cells = {(r['case_id'], r['context'], r['seed'], r['condition']): r for r in rows}
    if len(cells) != len(rows):
        raise ValueError('Duplicate analysis cell')
    return cells


def paired_contrast(rows, design, name):
    if name not in CONTRASTS:
        raise ValueError('Unknown contrast')
    first, second = CONTRASTS[name]
    cells, seeds = _cells(rows), []
    for case in design['cases']:
        for seed in design['seeds']:
            pair = [cells.get((case['id'], context, seed, form), {}) for context, form in (first, second)]
            valid = all(statistics.finite_score(row) for row in pair)
            seeds.append({'base_id': case['base_id'], 'seed': seed, 'valid': valid,
                          'cell_validity': [statistics.finite_score(r) for r in pair],
                          'first_score': pair[0].get('score'), 'second_score': pair[1].get('score'),
                          'difference': pair[0]['score'] - pair[1]['score'] if valid else None})
    return _paired_report(seeds, design, name, list(first), list(second))


def interaction(rows, design):
    cells, seeds = _cells(rows), []
    for case in design['cases']:
        for seed in design['seeds']:
            quad = {f'{context}_{form}': cells.get((case['id'], context, seed, form), {})
                    for context in ('conflict', 'aligned') for form in ('check_first', 'action_first')}
            valid = all(statistics.finite_score(row) for row in quad.values())
            differences = {context: quad[context + '_check_first']['score'] - quad[context + '_action_first']['score']
                           if valid else None for context in ('conflict', 'aligned')}
            seeds.append({'base_id': case['base_id'], 'seed': seed, 'valid': valid,
                          'cell_validity': {key: statistics.finite_score(r) for key, r in quad.items()},
                          'cell_scores': {key: r.get('score') for key, r in quad.items()},
                          'first_score': differences['conflict'], 'second_score': differences['aligned'],
                          'difference': differences['conflict'] - differences['aligned'] if valid else None})
    result = _paired_report(seeds, design, 'interaction', 'order_conflict', 'order_aligned')
    result.update(candidate_quadruples=result['candidate_pairs'], valid_quadruples=result['valid_pairs'],
                  definition='[check_first - action_first]conflict - [check_first - action_first]aligned; complete same-world/same-seed quadruples only.')
    return result


def practical_gate(contrast, design):
    """Prespecified practical coverage gate, not a significance test."""
    if design['split'] not in ('discovery', 'confirmation'):
        raise ValueError('The practical gate is only defined for discovery and confirmation')
    seeds = []
    for seed in design['seeds']:
        rows = [r for r in contrast['seed_differences'] if r['seed'] == seed and r['valid']]
        seeds.append({'seed': seed, 'valid_pairs': len(rows),
                      'difference': sum(r['difference'] for r in rows) / len(rows) if rows else None})
    full = (contrast['candidate_pairs'] == 16 and contrast['valid_pairs'] == 16
            and contrast['planned_worlds'] == 8 and contrast['contributing_worlds'] == 8
            and all(c['planned_seed_pairs'] == 2 and c['valid_seed_pairs'] == 2 for c in contrast['world_coverage'])
            and len(contrast['world_coverage']) == 8 and all(s['valid_pairs'] == 8 for s in seeds))
    positive = sum(value > 0 for value in contrast['world_differences'].values())
    criteria = {'complete_16_of_16': full,
                'mean_gain_at_least_one': contrast['difference'] is not None and contrast['difference'] >= 1.0,
                'positive_each_seed': len(seeds) == 2 and all(s['difference'] is not None and s['difference'] > 0 for s in seeds),
                'positive_at_least_three_worlds': positive >= 3}
    return {'qualified': all(criteria.values()), 'criteria': criteria,
            'valid_pairs': contrast['valid_pairs'], 'planned_pairs': 16,
            'difference': contrast['difference'], 'positive_worlds': positive,
            'planned_worlds': 8, 'seed_means': seeds}


def select_candidate(contrasts, design):
    if design['split'] != 'discovery':
        raise ValueError('Candidate selection requires the discovery bank')
    candidates = {name: practical_gate(contrasts[name], design) for name in CANDIDATES}
    selected = next((name for name in CANDIDATES if candidates[name]['qualified']), None)
    return {'candidate_priority': list(CANDIDATES), 'candidates': candidates,
            'selected_candidate': selected or 'order_conflict',
            'selected_qualified_in_discovery': selected is not None,
            'selection_status': 'discovery candidate' if selected else 'no discovery candidate'}


def score(design_path, run):
    design, protocol, records = frozen_run(design_path, run)
    cases = {case['id']: case for case in design['cases']}
    rows = []
    for slot in protocol['planned_slots']:
        case, record = cases[slot['case_id']], records[slot['node_id']]
        parsed = parse_action(record, slot['condition'])
        sim = simulate(case, parsed)
        expected = route(case['x'], case['threshold'])
        rows.append({**slot, **parsed, **check_diagnostics(case, parsed, slot['condition']),
                     'status': record['status'], 'valid': sim['executed'], 'score': sim['utility'],
                     'cost': sim['cost'], 'wrong_route': sim['wrong_route'],
                     'expected_direct_route': expected,
                     'correct_direct': sim['executed'] and parsed['action'] == expected,
                     'unavailable_reason': None if sim['executed'] else
                     (parsed['reason'] if record['status'] == 'complete' else record['status']),
                     'provider_error': record.get('error'), 'simulator_receipt': sim})
    groups = []
    for context in CONTEXTS:
        for form in FORMATS:
            group = [r for r in rows if r['context'] == context and r['condition'] == form]
            valid = [r for r in group if r['valid']]
            diagnostic = {}
            for field in (*CHECK_FIELDS, 'requested_order_compliant', 'within_requested_account_length'):
                values = [r[field] for r in group if r[field] is not None]
                diagnostic[field] = {'scorable': len(values), 'true': sum(values),
                                     'false': len(values) - sum(values), 'unavailable': len(group) - len(values),
                                     'applicable': form != 'direct' if field in CHECK_FIELDS else True}
            correct = sum(r['correct_direct'] for r in group)
            groups.append({'context': context, 'condition': form, 'planned': len(group),
                           'scorable': len(valid), 'valid_actions': len(valid), 'unavailable': len(group) - len(valid),
                           'json_valid': sum(r['json_valid'] for r in group), 'schema_valid': sum(r['schema_valid'] for r in group),
                           'malformed_complete': sum(r['status'] == 'complete' and not r['schema_valid'] for r in group),
                           'nonexecuted': len(group) - len(valid), 'actions': dict(Counter(r['action'] for r in valid)),
                           'correct_direct_routes': correct, 'correct_direct_per_planned': correct / len(group),
                           'wrong_direct_routes': sum(r['wrong_route'] for r in valid),
                           'measure': sum(r['action'] == 'MEASURE' for r in valid),
                           'total_cost': sum(r['cost'] for r in valid),
                           'mean_utility_valid': sum(r['score'] for r in valid) / len(valid) if valid else None,
                           'diagnostics': diagnostic, 'statuses': dict(Counter(r['status'] for r in group)),
                           'unavailable_reasons': dict(Counter(r['unavailable_reason'] for r in group if not r['valid']))})
    contrasts = {name: paired_contrast(rows, design, name) for name in CONTRASTS}
    contrasts['interaction'] = interaction(rows, design)
    selection = select_candidate(contrasts, design) if design['split'] == 'discovery' else None
    confirmation = None
    if design['split'] == 'confirmation':
        gate = read_gate(protocol['discovery_gate']['path'])
        selected = gate['selected_candidate']
        qualified = practical_gate(contrasts[selected], design)
        confirmation = {'primary_name': selected, 'selection_status': gate['selection_status'],
                        'selected_qualified_in_discovery': gate['selected_qualified_in_discovery'],
                        'primary_gate': qualified,
                        'practical_replicated_improvement': gate['selected_qualified_in_discovery'] and qualified['qualified']}
    return {'schema_version': 1, 'study': 'S-019', 'split': design['split'], 'model': design['model'],
            'design_sha256': digest(design_path), 'code_hashes': code_hashes(), 'run': run_binding(run),
            'rows': rows, 'groups': groups, 'contrasts': contrasts, 'discovery_selection': selection,
            'discovery_gate': protocol['discovery_gate'], 'confirmation': confirmation,
            'scope': 'Descriptive authored-bank utility contrasts; public check/order diagnostics are not private reasoning measurements. Missing utility is never zero.'}


def make_gate(design_path, run, score_path):
    design = read_design(design_path)
    if design['split'] != 'discovery':
        raise ValueError('Gate creation requires a discovery design')
    report = score(design_path, run)
    terminal = {'complete', 'incomplete', 'empty', 'invalid_response', 'transport_error'}
    if len(report['rows']) != 144 or any(row['status'] not in terminal for row in report['rows']):
        raise ValueError('Discovery gate requires all 144 planned requests to have terminal archived outcomes')
    saved = strict_json(runner.stable_read(Path(score_path)))
    if not same_json(saved, report):
        raise ValueError('Discovery score differs from verified evidence reconstruction')
    return {'schema_version': 1, 'study': 'S-019', 'kind': 'frozen-discovery-gate',
            'discovery': {'design': source(design_path), 'score': source(score_path), 'run': report['run']},
            'code_hashes': code_hashes(), **report['discovery_selection'],
            'rule': 'First qualified candidate in fixed priority; no qualifier retains order_conflict. All confirmation cells run.'}


def read_gate(path):
    value = strict_json(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or value.get('kind') != 'frozen-discovery-gate':
        raise ValueError('Invalid discovery gate')
    discovery = value.get('discovery', {})
    for label in ('design', 'score'):
        item = discovery.get(label, {})
        if not item.get('path') or source(item['path']) != item:
            raise ValueError('Discovery gate source binding changed: ' + label)
    expected = make_gate(discovery['design']['path'], discovery['run']['path'], discovery['score']['path'])
    if not same_json(value, expected):
        raise ValueError('Discovery gate differs from immutable inputs or fixed selection rule')
    return value


def reading(design_path, run, out):
    design, protocol, records = frozen_run(design_path, run)
    if design['split'] != 'confirmation':
        raise ValueError('Fixed reading export requires confirmation')
    run = Path(run)
    slots = [s for s in protocol['planned_slots'] if s['seed'] == design['reading_seed'] and s['base_index'] in READING_BASES]
    random.Random(design['reading_shuffle_seed']).shuffle(slots)
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
        supplied = strict_json(runner.stable_read(request))['messages'] if request.exists() else None
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
    receipt = {'schema_version': 1, 'study': 'S-019', 'design_sha256': digest(design_path),
               'discovery_gate': protocol['discovery_gate'], 'packets': len(slots), 'run': run_binding(run),
               'files': {name: digest(out / name) for name in (*documents, 'allocation-key.json')},
               'scope': 'Confirmation worlds 0,1,6,7; all nine context/format cells; seed7; unavailable slots retained.'}
    runner.write_json(out / 'receipt.json', receipt)
    return receipt
