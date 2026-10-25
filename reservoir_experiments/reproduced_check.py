"""S-020: exact historical requests and a bounded public-check comparison.

Construction, strict scoring, evidence-bound gates and fixed reading export only.
Provider dispatch belongs to the unchanged runner; no live-system access.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import random
import re

from . import retained_action as historical, decision_check as checks
from . import provenance_decision as previous, runner, statistics

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ('reproduction', 'matched', 'confirmation')
RULES = historical.RULES
FORMATS = checks.FORMATS
ORDERS = checks.ORDERS
CHECK_FIELDS = checks.CHECK_FIELDS
PAIRS = {'bundle': ('check_first', 'direct'),
         'action_bundle': ('action_first', 'direct'),
         'order': ('check_first', 'action_first')}
PRIMARY = 'bundle_changed'
CONTRASTS = tuple(f'{name}_{rule}' for rule in RULES for name in PAIRS) + tuple(f'{name}_interaction' for name in PAIRS)
TERMINAL = {'complete', 'incomplete', 'empty', 'invalid_response', 'transport_error'}
strict_json, same_json, digest = checks.strict_json, checks.same_json, previous.digest
source, run_binding = checks.source, checks.run_binding
route, simulate = previous.route, previous.simulate


def code_hashes():
    paths = ('reservoir_experiments/reproduced_check.py', 'probes/reproduced_check.py',
             'reservoir_experiments/retained_action.py', 'probes/retained_action.py',
             'reservoir_experiments/decision_check.py', 'probes/decision_check.py',
             'reservoir_experiments/provenance_decision.py', 'reservoir_experiments/statistics.py',
             *(f'reservoir_experiments/{name}' for name in runner.CORE_FILES))
    return {path: digest(ROOT / path) for path in paths}


def make_design(split='confirmation'):
    if split not in SPLITS:
        raise ValueError('Unknown split')
    cases = historical.make_design('confirmation')['cases']
    if split == 'confirmation':
        cases = []
        for index, (value, threshold) in enumerate(zip((21, 33, 43, 56, 67, 79), (16, 28, 38, 61, 72, 84))):
            base = f's020-confirmation-base-{index:02d}'
            cases.append({'id': base, 'base_id': base, 'base_index': index,
                          'focal': f'Wren{index + 1:02d}', 'snapshot': '2026-09-23T12:00:00Z',
                          'decision_clock': '2026-09-23T14:00:00Z', 'x': value,
                          'threshold': 50, 'later_threshold': threshold, 'audit_id': base + '-audit'})
    return {'schema_version': 1, 'study': 'S-020', 'id': f's020-{split}-v1', 'split': split,
            'model': 'mistral-small:24b',
            'model_digest': '8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d',
            'provider_version': '0.35.0', 'seeds': [7, 20260909],
            'options': {'temperature': .7, 'num_ctx': 16384}, 'max_tokens': 640,
            'deadline_seconds': 180, 'cases': cases, 'rules': list(RULES),
            'formats': ['direct'] if split == 'reproduction' else list(FORMATS),
            'requested_orders': {k: None if k == 'direct' else list(v) for k, v in ORDERS.items()},
            'costs': {'correct_direct': 0, 'wrong_direct': 4, 'measure': 1},
            'shuffle_seed': 20261025, 'bootstrap_draws': 10000, 'bootstrap_seed': 20261024,
            'reading_seed': 7, 'reading_shuffle_seed': 20261025, 'primary': PRIMARY,
            'contrast_names': [] if split == 'reproduction' else list(CONTRASTS),
            'reproduction_gate': {'valid_complete_actions': 24, 'minimum_worlds_wrong_at_both_seeds': 2},
            'practical_gate': {'valid_pairs': 12, 'minimum_gain': 1, 'minimum_positive_worlds': 2,
                               'positive_each_seed': True},
            'code_hashes': code_hashes()}


def read_design(path):
    value = strict_json(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or not same_json(value, make_design(value.get('split'))):
        raise ValueError('Design differs from frozen implementation or declared bank')
    return value


def guard_output(path):
    path = runner.guard_output(Path(path), ROOT)
    base = ROOT.resolve() / 'research' / 'outputs'
    if base not in path.parents:
        raise ValueError('S-020 outputs must be inside research/outputs')
    closed = {'introspection-20261024', 'provenance-decision-20261024',
              'retained-action-20261024', 'decision-check-20261025'}
    for parent in (path, *path.parents):
        if parent == base:
            break
        if (parent / 'CLOSED.json').exists() or parent.name in closed:
            raise ValueError('Evidence archive is closed')
    return path


def messages(case, rule, output_format):
    if output_format not in FORMATS:
        raise ValueError('Unknown format')
    result = historical.messages(case, rule, 'facts')
    if output_format != 'direct':
        assert result[1]['content'].endswith(historical.FORMAT)
        result[1]['content'] = result[1]['content'][:-len(historical.FORMAT)] + checks.format_instruction(output_format)
    return result


def parse_action(record, output_format):
    result = checks.parse_action(record, output_format)
    if output_format == 'direct':
        result['requested_key_order'] = None
        result['requested_order_compliant'] = None
    return result


def current_case(case, rule):
    if rule not in RULES:
        raise ValueError('Unknown rule')
    return {**case, 'threshold': case['later_threshold'] if rule == 'changed' else case['threshold']}


def planned_nodes(design):
    nodes, slots = [], []
    for case in design['cases']:
        for rule in RULES:
            for seed in design['seeds']:
                for form in design['formats']:
                    nid = f's020-{design["split"]}-base-{case["base_index"]:02d}-{rule}-s{seed}-{form}'
                    slots.append({'node_id': nid, 'case_id': case['id'], 'base_id': case['base_id'],
                                  'base_index': case['base_index'], 'rule': rule, 'seed': seed,
                                  'condition': form, 'eligible': True,
                                  'factual_record_sha256': runner.sha(json.dumps(historical.factual_record(case), sort_keys=True).encode())})
                    nodes.append({'id': nid, 'episode': case['id'], 'condition': form, 'kind': rule,
                                  'seed': seed, 'max_tokens': design['max_tokens'], 'format': 'json',
                                  'messages': messages(case, rule, form), 'inputs': [], 'after': [],
                                  'metadata': {'base_id': case['base_id'], 'rule': rule}})
    random.Random(design['shuffle_seed']).shuffle(nodes)
    return nodes, slots


def preview(design_path):
    """Freeze future request bytes/schedule without producing a dispatchable protocol."""
    design = read_design(design_path)
    nodes, slots = planned_nodes(design)
    requests = []
    for node in nodes:
        raw = runner.render_request(design, node, {})
        requests.append({'node_id': node['id'], 'sha256': runner.sha(raw), 'request': strict_json(raw)})
    return {'schema_version': 1, 'study': 'S-020', 'kind': 'nondispatchable-request-preview',
            'split': design['split'], 'design_sha256': digest(design_path),
            'schedule': [n['id'] for n in nodes], 'planned': slots, 'requests': requests}


def build(design_path, *, reproduction_gate=None, matched_gate=None, additional_sources=()):
    design = read_design(design_path)
    split = design['split']
    bindings, gates = {}, {}
    expected = () if split == 'reproduction' else ('reproduction',) if split == 'matched' else ('reproduction', 'matched')
    paths = {'reproduction': reproduction_gate, 'matched': matched_gate}
    for phase, path in paths.items():
        if phase not in expected:
            if path is not None:
                raise ValueError(f'{split} does not accept a {phase} gate')
            continue
        if path is None:
            raise ValueError(f'{split} requires a {phase} gate')
        gate = read_gate(path)
        if gate['split'] != phase or (phase == 'reproduction' and not gate['decision']['qualified']):
            raise ValueError('Wrong gate phase or reproduction did not qualify')
        gates[phase] = gate
        bindings[phase] = source(path)
    if split == 'confirmation' and gates['matched']['reproduction_gate'] != bindings['reproduction']:
        raise ValueError('Matched and confirmation reproduction gates differ')
    sources = [source(design_path)] + [source(ROOT / path) for path in design['code_hashes']]
    for phase in expected:
        gate = gates[phase]
        sources += [bindings[phase], gate['evidence']['design'], gate['evidence']['score'],
                    source(Path(gate['evidence']['run']['path']) / 'manifest.json')]
    sources += [source(path) for path in additional_sources]
    nodes, slots = planned_nodes(design)
    protocol = {'schema_version': 1, 'study': 'S-020', 'id': design['id'], 'split': split,
                'model': design['model'], 'endpoint': 'http://127.0.0.1:11434',
                'deadline_seconds': design['deadline_seconds'], 'options': design['options'],
                'design_sha256': digest(design_path), 'nodes': nodes, 'planned_slots': slots,
                'truth': {c['id']: c for c in design['cases']}, 'sources': sources,
                'gates': bindings}
    ledger = {'schema_version': 1, 'study': 'S-020', 'design_sha256': digest(design_path),
              'planned': slots, 'sources': list(sources), 'gates': bindings,
              'rule': 'Reproduction headroom gates both full comparisons; matched gain never selects confirmation cells.'}
    runner.validate_protocol(protocol)
    for node in nodes:
        runner.render_request(protocol, node, {})
    return protocol, ledger


def frozen_run(design_path, run):
    run = Path(run)
    design = read_design(design_path)
    runner.verify(run)
    manifest, protocol = runner.load_run(run, check_code=True)
    identity_path = run / 'identity.json'
    if identity_path.exists():
        identity = strict_json(runner.stable_read(identity_path))
        model, runtime = identity.get('model', {}), identity.get('runtime', {})
        if (not isinstance(model, dict) or not isinstance(runtime, dict)
                or identity.get('endpoint') != 'http://127.0.0.1:11434'
                or model.get('name') != design['model']
                or model.get('digest') != design['model_digest']
                or runtime.get('version') != design['provider_version']):
            raise ValueError('Provider identity differs from frozen apparatus')
    gates = protocol.get('gates', {})
    for binding in gates.values():
        if source(binding['path']) != binding:
            raise ValueError('Gate binding changed')
    expected, _ = build(design_path, reproduction_gate=gates.get('reproduction', {}).get('path'),
                        matched_gate=gates.get('matched', {}).get('path'))
    if not same_json({k: v for k, v in protocol.items() if k != 'sources'},
                     {k: v for k, v in expected.items() if k != 'sources'}):
        raise ValueError('Run differs from frozen authored protocol')
    if protocol['sources'][:len(expected['sources'])] != expected['sources']:
        raise ValueError('Missing immutable source')
    if [{'path': e['original_path'], 'sha256': e['sha256']} for e in manifest['sources']] != protocol['sources']:
        raise ValueError('Source snapshots differ')
    records = runner.read_results(run)
    states = runner.status(run, verify_first=False)['nodes']
    for slot in protocol['planned_slots']:
        records.setdefault(slot['node_id'], {'status': states[slot['node_id']], 'text': None})
    return design, protocol, records


def _cells(rows):
    cells = {(r['case_id'], r['rule'], r['seed'], r['condition']): r for r in rows}
    if len(cells) != len(rows):
        raise ValueError('Duplicate analysis cell')
    return cells


def contrast(rows, design, name):
    if name not in CONTRASTS:
        raise ValueError('Unknown contrast')
    pair_name, rule = name.rsplit('_', 1)
    first, second = PAIRS[pair_name]
    cells, seeds = _cells(rows), []
    for case in design['cases']:
        for seed in design['seeds']:
            if rule == 'interaction':
                quad = {f'{r}_{f}': cells.get((case['id'], r, seed, f), {}) for r in RULES for f in (first, second)}
                valid = all(statistics.finite_score(row) for row in quad.values())
                values = {r: quad[f'{r}_{first}']['score'] - quad[f'{r}_{second}']['score'] if valid else None for r in RULES}
                row = {'first_score': values['changed'], 'second_score': values['unchanged'],
                       'cell_validity': {k: statistics.finite_score(v) for k, v in quad.items()},
                       'cell_scores': {k: v.get('score') for k, v in quad.items()}}
            else:
                pair = [cells.get((case['id'], rule, seed, f), {}) for f in (first, second)]
                valid = all(statistics.finite_score(v) for v in pair)
                row = {'first_score': pair[0].get('score'), 'second_score': pair[1].get('score'),
                       'cell_validity': [statistics.finite_score(v) for v in pair]}
            seeds.append({'base_id': case['base_id'], 'seed': seed, 'valid': valid, **row,
                          'difference': row['first_score'] - row['second_score'] if valid else None})
    result = checks._paired_report(seeds, design, name, first, second)
    if rule == 'interaction':
        result.update(candidate_quadruples=result['candidate_pairs'], valid_quadruples=result['valid_pairs'],
                      definition=f'[{first} - {second}]changed - [{first} - {second}]unchanged; complete same-world/same-seed quadruples only.')
    return result


def practical_gate(result, design):
    seeds = []
    for seed in design['seeds']:
        values = [r['difference'] for r in result['seed_differences'] if r['seed'] == seed and r['valid']]
        seeds.append({'seed': seed, 'valid_pairs': len(values), 'difference': sum(values) / len(values) if values else None})
    complete = (result['candidate_pairs'] == 12 and result['valid_pairs'] == 12
                and result['planned_worlds'] == result['contributing_worlds'] == 6
                and len(result['world_coverage']) == 6
                and all(r['planned_seed_pairs'] == r['valid_seed_pairs'] == 2 for r in result['world_coverage'])
                and all(r['valid_pairs'] == 6 for r in seeds))
    positive = sum(v > 0 for v in result['world_differences'].values())
    criteria = {'complete_12_of_12': complete,
                'mean_gain_at_least_one': result['difference'] is not None and result['difference'] >= 1,
                'positive_each_seed': len(seeds) == 2 and all(r['difference'] is not None and r['difference'] > 0 for r in seeds),
                'positive_at_least_two_worlds': positive >= 2}
    return {'qualified': all(criteria.values()), 'criteria': criteria, 'seed_means': seeds,
            'difference': result['difference'], 'positive_worlds': positive,
            'valid_pairs': result['valid_pairs'], 'planned_pairs': 12}


def reproduction_decision(rows, design):
    cells = _cells(rows)
    complete = len(rows) == 24 and all(r['status'] == 'complete' and r['valid'] for r in rows)
    worlds = []
    for case in design['cases']:
        values = [cells.get((case['id'], 'changed', seed, 'direct'), {}) for seed in design['seeds']]
        worlds.append({'base_id': case['base_id'],
                       'wrong_direct_at_both_seeds': len(values) == 2 and all(r.get('wrong_route') is True for r in values)})
    count = sum(r['wrong_direct_at_both_seeds'] for r in worlds)
    return {'qualified': complete and count >= 2,
            'criteria': {'all_24_complete_valid': complete, 'at_least_two_worlds_wrong_at_both_seeds': count >= 2},
            'worlds': worlds, 'worlds_wrong_at_both_seeds': count,
            'decision': 'proceed unchanged' if complete and count >= 2 else 'stop after reproduction'}


def score_rows(design, slots, records):
    cases = {c['id']: c for c in design['cases']}
    rows = []
    for slot in slots:
        case = current_case(cases[slot['case_id']], slot['rule'])
        record = records.get(slot['node_id'], {'status': 'missing', 'text': None})
        parsed = parse_action(record, slot['condition'])
        sim = simulate(case, parsed)
        expected = route(case['x'], case['threshold'])
        rows.append({**slot, **parsed, **checks.check_diagnostics(case, parsed, slot['condition']),
                     'status': record['status'], 'valid': sim['executed'], 'score': sim['utility'],
                     'cost': sim['cost'], 'wrong_route': sim['wrong_route'], 'expected_direct_route': expected,
                     'correct_direct': sim['executed'] and parsed['action'] == expected,
                     'unavailable_reason': None if sim['executed'] else parsed['reason'] if record['status'] == 'complete' else record['status'],
                     'provider_error': record.get('error'), 'simulator_receipt': sim})
    groups = []
    for rule in RULES:
        for form in design['formats']:
            group = [r for r in rows if r['rule'] == rule and r['condition'] == form]
            valid = [r for r in group if r['valid']]
            diagnostics = {}
            for field in (*CHECK_FIELDS, 'requested_order_compliant', 'within_requested_account_length'):
                values = [r[field] for r in group if r[field] is not None]
                diagnostics[field] = {'scorable': len(values), 'true': sum(values), 'false': len(values) - sum(values),
                                      'unavailable': len(group) - len(values),
                                      'applicable': form != 'direct' if field != 'within_requested_account_length' else True}
            correct = sum(r['correct_direct'] for r in group)
            groups.append({'rule': rule, 'condition': form, 'planned': len(group), 'scorable': len(valid),
                           'valid_actions': len(valid), 'unavailable': len(group) - len(valid),
                           'json_valid': sum(r['json_valid'] for r in group), 'schema_valid': sum(r['schema_valid'] for r in group),
                           'malformed_complete': sum(r['status'] == 'complete' and not r['schema_valid'] for r in group),
                           'nonexecuted': len(group) - len(valid), 'actions': dict(Counter(r['action'] for r in valid)),
                           'correct_direct_routes': correct, 'correct_direct_per_planned': correct / len(group),
                           'wrong_direct_routes': sum(r['wrong_route'] for r in valid),
                           'measure': sum(r['action'] == 'MEASURE' for r in valid), 'total_cost': sum(r['cost'] for r in valid),
                           'mean_utility_valid': sum(r['score'] for r in valid) / len(valid) if valid else None,
                           'diagnostics': diagnostics, 'statuses': dict(Counter(r['status'] for r in group)),
                           'unavailable_reasons': dict(Counter(r['unavailable_reason'] for r in group if not r['valid']))})
    contrasts = {name: contrast(rows, design, name) for name in design['contrast_names']}
    decision = reproduction_decision(rows, design) if design['split'] == 'reproduction' else None
    practical = practical_gate(contrasts[PRIMARY], design) if contrasts else None
    return {'rows': rows, 'groups': groups, 'contrasts': contrasts, 'reproduction_decision': decision, 'primary_gate': practical}


def score(design_path, run):
    design, protocol, records = frozen_run(design_path, run)
    report = score_rows(design, protocol['planned_slots'], records)
    confirmation = None
    if design['split'] == 'confirmation':
        prior = read_gate(protocol['gates']['matched']['path'])
        confirmation = {'primary_name': PRIMARY, 'matched_primary_gate': prior['decision'],
                        'confirmation_primary_gate': report['primary_gate'],
                        'practical_replicated_improvement': prior['decision']['qualified'] and report['primary_gate']['qualified']}
    return {'schema_version': 1, 'study': 'S-020', 'split': design['split'], 'model': design['model'],
            'design_sha256': digest(design_path), 'code_hashes': code_hashes(), 'run': run_binding(run),
            'gates': protocol['gates'], **report, 'confirmation': confirmation,
            'scope': 'Descriptive authored-bank utility; public check/order diagnostics do not authenticate private reasoning. Missing utility is never zero.'}


def make_gate(design_path, run, score_path):
    design = read_design(design_path)
    if design['split'] not in ('reproduction', 'matched'):
        raise ValueError('Only reproduction and matched phases produce a gate')
    report = score(design_path, run)
    count = 24 if design['split'] == 'reproduction' else 72
    if len(report['rows']) != count or any(r['status'] not in TERMINAL for r in report['rows']):
        raise ValueError('Gate requires every planned opportunity to have a terminal archived outcome')
    if not same_json(strict_json(runner.stable_read(Path(score_path))), report):
        raise ValueError('Score differs from verified evidence reconstruction')
    return {'schema_version': 1, 'study': 'S-020', 'kind': 'frozen-phase-gate', 'split': design['split'],
            'evidence': {'design': source(design_path), 'score': source(score_path), 'run': report['run']},
            'code_hashes': code_hashes(), 'reproduction_gate': report['gates'].get('reproduction'),
            'decision': report['reproduction_decision'] if design['split'] == 'reproduction' else report['primary_gate'],
            'rule': 'Reproduction must qualify; a terminal matched phase permits the full confirmation regardless of gain.'}


def read_gate(path):
    value = strict_json(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or value.get('kind') != 'frozen-phase-gate':
        raise ValueError('Invalid gate')
    evidence = value.get('evidence', {})
    for label in ('design', 'score'):
        item = evidence.get(label, {})
        if not item.get('path') or source(item['path']) != item:
            raise ValueError('Gate source binding changed: ' + label)
    expected = make_gate(evidence['design']['path'], evidence['run']['path'], evidence['score']['path'])
    if not same_json(value, expected):
        raise ValueError('Gate differs from immutable inputs or fixed rule')
    return value


def reading(design_path, run, out):
    design, protocol, records = frozen_run(design_path, run)
    if design['split'] == 'matched':
        raise ValueError('No matched-phase reading was predeclared')
    if design['split'] == 'reproduction' and score_rows(design, protocol['planned_slots'], records)['reproduction_decision']['qualified']:
        raise ValueError('Qualified reproduction requires the confirmation reading')
    if any(r['status'] not in TERMINAL for r in records.values()):
        raise ValueError('Reading requires a terminal phase')
    slots = [s for s in protocol['planned_slots'] if s['seed'] == design['reading_seed']]
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
        directory = Path(run) / 'nodes' / slot['node_id']
        request = directory / 'request.json'
        supplied = strict_json(runner.stable_read(request))['messages'] if request.exists() else None
        documents['evidence.md'] += header + (''.join(m['role'] + ':\n' + fenced(m['content']) for m in supplied) if supplied else '[No request dispatched.]\n') + '\n'
        key.append({'packet': index, **slot, 'status': record['status'],
                    'files': {name: digest(directory / name) if (directory / name).exists() else None
                              for name in ('request.json', 'dispatch.json', 'response.raw', 'result.json')}})
    out = guard_output(out)
    if out.exists():
        raise ValueError('Reading destination already exists')
    out.mkdir(parents=True, mode=0o700)
    for name, text in documents.items():
        runner.write_once(out / name, text.encode())
    runner.write_json(out / 'allocation-key.json', key)
    receipt = {'schema_version': 1, 'study': 'S-020', 'split': design['split'],
               'design_sha256': digest(design_path), 'gates': protocol['gates'], 'packets': len(slots),
               'run': run_binding(run), 'files': {name: digest(out / name) for name in (*documents, 'allocation-key.json')},
               'scope': 'All six worlds and both rules at seed 7, all phase formats; fixed shuffled sample, unavailable outputs retained.'}
    runner.write_json(out / 'receipt.json', receipt)
    return receipt
