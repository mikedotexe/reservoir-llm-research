"""S-021: supplied assistant prefixes and exact generated continuations.

Construction, strict scoring, evidence-bound qualification and fixed reading
only. The unchanged runner owns dispatch. No provider or live-system access.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import random
import re

from . import reproduced_check as prior, decision_check as checks
from . import provenance_decision as previous, runner, statistics

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ('qualification', 'study')
RULES = prior.RULES
FORMATS = ('operands_only', 'correct', 'flipped')
ORDER = checks.ORDERS['check_first']
PAIRS = {'content': ('correct', 'flipped'),
         'correct_baseline': ('correct', 'operands_only'),
         'flipped_baseline': ('flipped', 'operands_only')}
PRIMARY = 'content_changed'
CONTRASTS = tuple(f'{name}_{rule}' for rule in RULES for name in PAIRS) + tuple(f'{name}_interaction' for name in PAIRS)
DIAGNOSTICS = ('action_matches_supplied_relation', 'generated_relation_correct',
               'action_matches_generated_relation', 'generated_relation_correct_wrong_direct',
               'generated_relation_correct_measure', 'generated_relation_incorrect_correct_direct',
               'requested_order_compliant', 'within_requested_account_length')
strict_json, same_json, digest = checks.strict_json, checks.same_json, previous.digest
source, run_binding = checks.source, checks.run_binding
route, simulate, current_case = previous.route, previous.simulate, prior.current_case


def code_hashes():
    paths = ('reservoir_experiments/prefix_continuation.py', 'probes/prefix_continuation.py',
             'reservoir_experiments/reproduced_check.py', 'probes/reproduced_check.py',
             'reservoir_experiments/retained_action.py', 'probes/retained_action.py',
             'reservoir_experiments/decision_check.py', 'probes/decision_check.py',
             'reservoir_experiments/provenance_decision.py', 'reservoir_experiments/statistics.py',
             *(f'reservoir_experiments/{name}' for name in runner.CORE_FILES))
    return {path: digest(ROOT / path) for path in paths}


def make_design(split='study'):
    if split not in SPLITS:
        raise ValueError('Unknown split')
    cases = []
    if split == 'study':
        for index, (value, threshold) in enumerate(zip((24, 35, 44, 57, 68, 81), (19, 30, 39, 62, 73, 86))):
            base = f's021-study-base-{index:02d}'
            cases.append({'id': base, 'base_id': base, 'base_index': index,
                          'focal': f'Sable{index + 1:02d}', 'snapshot': '2026-09-24T12:00:00Z',
                          'decision_clock': '2026-09-24T14:00:00Z', 'x': value,
                          'threshold': 50, 'later_threshold': threshold, 'audit_id': base + '-audit'})
    else:
        for label, first, second in (('a', 'cedar', 'otter'), ('b', 'violet', 'heron')):
            expected = {'probe': first + '-' + second, 'status': 'ok'}
            cases.append({'id': 's021-qualification-' + label,
                          'system': 'You complete text in an isolated formatting test. Return only the requested JSON text.',
                          'user': 'Return exactly this JSON object and nothing else: ' + json.dumps(expected, separators=(',', ':')),
                          'prefix': '{"probe":"' + first + '-', 'expected': expected,
                          'expected_key_order': ['probe', 'status']})
    return {'schema_version': 1, 'study': 'S-021', 'id': f's021-{split}-v1', 'split': split,
            'model': 'mistral-small:24b',
            'model_digest': '8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d',
            'provider_version': '0.35.0', 'seeds': [7, 20260909],
            'options': {'temperature': .7, 'num_ctx': 16384},
            'max_tokens': 64 if split == 'qualification' else 640,
            'deadline_seconds': 180, 'cases': cases,
            'rules': list(RULES) if split == 'study' else [],
            'formats': list(FORMATS) if split == 'study' else [],
            'requested_key_order': list(ORDER) if split == 'study' else ['probe', 'status'],
            'generation_contract': 'Final assistant prefix; raw response is suffix; no format field; exact concatenation without repair.',
            'costs': {'correct_direct': 0, 'wrong_direct': 4, 'measure': 1},
            'shuffle_seed': 20261025, 'bootstrap_draws': 10000, 'bootstrap_seed': 20261024,
            'reading_seed': 7, 'reading_shuffle_seed': 20261025, 'reading_bases': [0, 2, 5],
            'primary': PRIMARY if split == 'study' else None,
            'contrast_names': list(CONTRASTS) if split == 'study' else [],
            'practical_gate': {'valid_pairs': 12, 'minimum_gain': 1, 'minimum_positive_worlds': 2,
                               'positive_each_seed': True},
            'code_hashes': code_hashes()}


def read_design(path):
    value = strict_json(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or not same_json(value, make_design(value.get('split'))):
        raise ValueError('Design differs from frozen implementation or declared phase')
    return value


def guard_output(path):
    path = runner.guard_output(Path(path), ROOT)
    base = ROOT.resolve() / 'research' / 'outputs'
    if base not in path.parents:
        raise ValueError('S-021 outputs must be inside research/outputs')
    archive = path.relative_to(base).parts[0]
    match = re.fullmatch(r'prefix-continuation-(\d{8})(?:-[A-Za-z0-9][A-Za-z0-9_.-]*)?', archive)
    if match is None or match[1] < '20261025':
        raise ValueError('Use a new S-021 prefix-continuation evidence archive')
    for parent in (path, *path.parents):
        if parent == base:
            break
        if (parent / 'CLOSED.json').exists():
            raise ValueError('Evidence archive is closed')
    return path


def prefix(case, rule, condition):
    if condition not in FORMATS:
        raise ValueError('Unknown prefix condition')
    current = current_case(case, rule)
    text = '{"x":' + str(current['x']) + ',"current_threshold":' + str(current['threshold']) + ',"relation":'
    if condition != 'operands_only':
        relation = 'LT' if current['x'] < current['threshold'] else 'GE'
        if condition == 'flipped':
            relation = 'GE' if relation == 'LT' else 'LT'
        text += json.dumps(relation) + ',"action":'
    return text


def messages(case, rule, condition):
    return [*prior.messages(case, rule, 'check_first'),
            {'role': 'assistant', 'content': prefix(case, rule, condition)}]


def parse_action(record, supplied_prefix):
    """Parse the exact concatenation, preserving suffix bytes without repair."""
    suffix = record.get('text')
    assembled = supplied_prefix + suffix if isinstance(suffix, str) else None
    parsed = checks.parse_action({**record, 'text': assembled}, 'check_first')
    return {**parsed, 'raw_suffix': suffix, 'supplied_prefix': supplied_prefix,
            'assembled_text': assembled}


def planned_nodes(design):
    nodes, slots = [], []
    for case in design['cases']:
        if design['split'] == 'qualification':
            allocations = [('sentinel', 'sentinel', seed) for seed in design['seeds']]
        else:
            allocations = [(rule, form, seed) for rule in RULES for form in FORMATS for seed in design['seeds']]
        for rule, form, seed in allocations:
            nid = f'{case["id"]}-{rule}-{form}-s{seed}'
            if design['split'] == 'qualification':
                supplied = [{'role': role, 'content': case[key]}
                            for role, key in (('system', 'system'), ('user', 'user'), ('assistant', 'prefix'))]
                slot = {'node_id': nid, 'case_id': case['id'], 'condition': form, 'seed': seed,
                        'supplied_prefix': case['prefix'], 'eligible': True}
            else:
                supplied = messages(case, rule, form)
                slot = {'node_id': nid, 'case_id': case['id'], 'base_id': case['base_id'],
                        'base_index': case['base_index'], 'rule': rule, 'condition': form, 'seed': seed,
                        'supplied_prefix': supplied[-1]['content'], 'eligible': True,
                        'factual_record_sha256': runner.sha(json.dumps(prior.historical.factual_record(case), sort_keys=True).encode())}
            slots.append(slot)
            nodes.append({'id': nid, 'episode': case['id'], 'condition': form, 'kind': rule,
                          'seed': seed, 'max_tokens': design['max_tokens'], 'messages': supplied,
                          'inputs': [], 'after': [], 'metadata': {'case_id': case['id']}})
    random.Random(design['shuffle_seed']).shuffle(nodes)
    return nodes, slots


def preview(design_path):
    """Freeze request bytes and schedule without a dispatchable protocol."""
    design = read_design(design_path)
    nodes, slots = planned_nodes(design)
    requests = []
    for node in nodes:
        raw = runner.render_request(design, node, {})
        requests.append({'node_id': node['id'], 'sha256': runner.sha(raw), 'request': strict_json(raw)})
    return {'schema_version': 1, 'study': 'S-021', 'kind': 'nondispatchable-request-preview',
            'split': design['split'], 'design_sha256': digest(design_path),
            'schedule': [n['id'] for n in nodes], 'planned': slots, 'requests': requests}


def build(design_path, *, study_design=None, qualification_gate=None, additional_sources=()):
    design = read_design(design_path)
    gate = binding = companion = None
    if design['split'] == 'qualification':
        if qualification_gate is not None or study_design is None:
            raise ValueError('Qualification requires the frozen study design and accepts no gate')
        if read_design(study_design)['split'] != 'study':
            raise ValueError('Companion design must be the full study')
        companion = source(study_design)
    else:
        if study_design is not None or qualification_gate is None:
            raise ValueError('Study requires a qualification gate and accepts no companion design')
        gate = read_gate(qualification_gate)
        if not gate['decision']['qualified'] or gate['study_design'] != source(design_path):
            raise ValueError('Qualification failed or did not freeze this exact study design')
        binding = source(qualification_gate)
    sources = [source(design_path)] + [source(ROOT / path) for path in design['code_hashes']]
    if companion is not None:
        sources.append(companion)
    if gate is not None:
        sources += [binding, gate['evidence']['design'], gate['evidence']['score'],
                    source(Path(gate['evidence']['run']['path']) / 'manifest.json')]
    sources += [source(path) for path in additional_sources]
    nodes, slots = planned_nodes(design)
    protocol = {'schema_version': 1, 'study': 'S-021', 'id': design['id'], 'split': design['split'],
                'model': design['model'], 'endpoint': 'http://127.0.0.1:11434',
                'deadline_seconds': design['deadline_seconds'], 'options': design['options'],
                'design_sha256': digest(design_path), 'nodes': nodes, 'planned_slots': slots,
                'truth': {c['id']: c for c in design['cases']}, 'sources': sources,
                'study_design': companion, 'qualification_gate': binding}
    ledger = {'schema_version': 1, 'study': 'S-021', 'split': design['split'],
              'design_sha256': digest(design_path), 'planned': slots, 'sources': list(sources),
              'study_design': companion, 'qualification_gate': binding,
              'rule': 'All four frozen sentinels must pass; all 72 study cells remain fixed regardless of outcomes. No retries.'}
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
    companion, gate = protocol.get('study_design'), protocol.get('qualification_gate')
    for binding in (companion, gate):
        if binding is not None and source(binding['path']) != binding:
            raise ValueError('Companion design or qualification gate binding changed')
    expected, _ = build(design_path, study_design=companion['path'] if companion else None,
                        qualification_gate=gate['path'] if gate else None)
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


def contrast(rows, design, name):
    if name not in CONTRASTS:
        raise ValueError('Unknown contrast')
    pair_name, rule = name.rsplit('_', 1)
    first, second = PAIRS[pair_name]
    cells = {(r['case_id'], r['rule'], r['seed'], r['condition']): r for r in rows}
    if len(cells) != len(rows):
        raise ValueError('Duplicate analysis cell')
    seeds = []
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


def qualification_rows(design, slots, records):
    cases = {c['id']: c for c in design['cases']}
    rows = []
    for slot in slots:
        case = cases[slot['case_id']]
        record = records.get(slot['node_id'], {'status': 'missing', 'text': None})
        suffix = record.get('text')
        assembled = case['prefix'] + suffix if isinstance(suffix, str) else None
        data, reason = None, 'unavailable'
        if record['status'] == 'complete' and assembled is not None:
            try:
                data = strict_json(assembled)
                reason = None if (isinstance(data, dict) and same_json(data, case['expected'])
                                  and list(data) == case['expected_key_order']) else 'unexpected-object-or-order'
            except (TypeError, ValueError):
                reason = 'malformed-json'
        rows.append({**slot, 'status': record['status'], 'raw_suffix': suffix,
                     'assembled_text': assembled, 'expected': case['expected'],
                     'actual_key_order': list(data) if isinstance(data, dict) else None,
                     'passed': reason is None, 'reason': reason, 'provider_error': record.get('error')})
    qualified = len(rows) == 4 and all(r['passed'] for r in rows)
    return {'rows': rows, 'groups': [], 'contrasts': {},
            'qualification_decision': {'qualified': qualified, 'planned': 4,
                                       'completed': sum(r['status'] == 'complete' for r in rows),
                                       'passed': sum(r['passed'] for r in rows),
                                       'decision': 'proceed unchanged' if qualified else 'stop; no study dispatch or retries'}}


def score_rows(design, slots, records):
    if design['split'] == 'qualification':
        return qualification_rows(design, slots, records)
    cases = {c['id']: c for c in design['cases']}
    rows = []
    for slot in slots:
        case = current_case(cases[slot['case_id']], slot['rule'])
        record = records.get(slot['node_id'], {'status': 'missing', 'text': None})
        parsed = parse_action(record, slot['supplied_prefix'])
        sim = simulate(case, parsed)
        expected = route(case['x'], case['threshold'])
        expected_relation = 'LT' if case['x'] < case['threshold'] else 'GE'
        baseline = slot['condition'] == 'operands_only'
        supplied_relation = None if baseline else (expected_relation if slot['condition'] == 'correct'
                                                    else 'GE' if expected_relation == 'LT' else 'LT')
        valid = parsed['action_valid']
        relation_correct = parsed['relation'] == expected_relation if baseline and valid else None
        diagnostics = {
            'action_matches_supplied_relation': parsed['action'] == ('ROUTE_LOW' if supplied_relation == 'LT' else 'ROUTE_HIGH') if not baseline and valid else None,
            'generated_relation_correct': relation_correct,
            'action_matches_generated_relation': parsed['action'] == ('ROUTE_LOW' if parsed['relation'] == 'LT' else 'ROUTE_HIGH') if baseline and valid else None,
            'generated_relation_correct_wrong_direct': relation_correct and sim['wrong_route'] if baseline and valid else None,
            'generated_relation_correct_measure': relation_correct and parsed['action'] == 'MEASURE' if baseline and valid else None,
            'generated_relation_incorrect_correct_direct': not relation_correct and parsed['action'] == expected if baseline and valid else None}
        assembled_fields = {k: parsed[k] for k in ORDER} if parsed['schema_valid'] else None
        rows.append({**slot, **{k: v for k, v in parsed.items() if k not in ('x', 'current_threshold', 'relation')},
                     **diagnostics, 'assembled_fields': assembled_fields,
                     'supplied_x': case['x'], 'supplied_current_threshold': case['threshold'],
                     'supplied_relation': supplied_relation,
                     'generated_relation': parsed['relation'] if baseline and valid else None,
                     'generated_action': parsed['action'], 'generated_account': parsed['account'],
                     'relation_provenance': 'generated' if baseline else 'supplied',
                     'suffix_echoes_prefix': isinstance(parsed['raw_suffix'], str) and parsed['raw_suffix'].startswith(slot['supplied_prefix']),
                     'status': record['status'], 'valid': sim['executed'], 'score': sim['utility'],
                     'cost': sim['cost'], 'wrong_route': sim['wrong_route'], 'expected_direct_route': expected,
                     'correct_direct': sim['executed'] and parsed['action'] == expected,
                     'unavailable_reason': None if sim['executed'] else parsed['reason'] if record['status'] == 'complete' else record['status'],
                     'provider_error': record.get('error'), 'simulator_receipt': sim})
    groups = []
    for rule in RULES:
        for form in FORMATS:
            group = [r for r in rows if r['rule'] == rule and r['condition'] == form]
            valid = [r for r in group if r['valid']]
            diagnostics = {}
            for field in DIAGNOSTICS:
                applicable = (form != 'operands_only' if field == 'action_matches_supplied_relation'
                              else True if field in ('requested_order_compliant', 'within_requested_account_length')
                              else form == 'operands_only')
                values = [r[field] for r in group if applicable and r[field] is not None]
                applicable_count = len(group) if applicable else 0
                diagnostics[field] = {'applicable': applicable, 'inapplicable': len(group) - applicable_count,
                                      'scorable': len(values), 'true': sum(values), 'false': len(values) - sum(values),
                                      'unavailable': applicable_count - len(values)}
            correct = sum(r['correct_direct'] for r in group)
            groups.append({'rule': rule, 'condition': form, 'planned': len(group),
                           'completed': sum(r['status'] == 'complete' for r in group),
                           'scorable': len(valid), 'valid_actions': len(valid), 'unavailable': len(group) - len(valid),
                           'json_valid': sum(r['json_valid'] for r in group), 'schema_valid': sum(r['schema_valid'] for r in group),
                           'malformed_complete': sum(r['status'] == 'complete' and not r['schema_valid'] for r in group),
                           'suffix_echoes_prefix': sum(r['suffix_echoes_prefix'] for r in group),
                           'nonexecuted': len(group) - len(valid), 'actions': dict(Counter(r['action'] for r in valid)),
                           'correct_direct_routes': correct, 'correct_direct_per_planned': correct / len(group),
                           'wrong_direct_routes': sum(r['wrong_route'] for r in valid),
                           'measure': sum(r['action'] == 'MEASURE' for r in valid), 'total_cost': sum(r['cost'] for r in valid),
                           'mean_utility_valid': sum(r['score'] for r in valid) / len(valid) if valid else None,
                           'diagnostics': diagnostics, 'statuses': dict(Counter(r['status'] for r in group)),
                           'unavailable_reasons': dict(Counter(r['unavailable_reason'] for r in group if not r['valid']))})
    contrasts = {name: contrast(rows, design, name) for name in design['contrast_names']}
    return {'rows': rows, 'groups': groups, 'contrasts': contrasts,
            'practical_sensitivity': prior.practical_gate(contrasts[PRIMARY], design)}


def score(design_path, run):
    design, protocol, records = frozen_run(design_path, run)
    return {'schema_version': 1, 'study': 'S-021', 'split': design['split'], 'model': design['model'],
            'design_sha256': digest(design_path), 'code_hashes': code_hashes(), 'run': run_binding(run),
            'study_design': protocol['study_design'], 'qualification_gate': protocol['qualification_gate'],
            **score_rows(design, protocol['planned_slots'], records),
            'scope': 'Authored-prefix sensitivity in one constructed bank. Supplied fields are not generated checks; suffixes do not authenticate private reasoning. Missing utility is never zero.'}


def make_gate(design_path, run, score_path):
    if read_design(design_path)['split'] != 'qualification':
        raise ValueError('Only qualification produces a gate')
    report = score(design_path, run)
    if not same_json(strict_json(runner.stable_read(Path(score_path))), report):
        raise ValueError('Score differs from verified evidence reconstruction')
    _, protocol = runner.load_run(Path(run))
    return {'schema_version': 1, 'study': 'S-021', 'kind': 'frozen-qualification-gate',
            'evidence': {'design': source(design_path), 'score': source(score_path), 'run': report['run'],
                         'sources': protocol['sources']},
            'code_hashes': code_hashes(), 'study_design': report['study_design'],
            'decision': report['qualification_decision'],
            'rule': 'All four frozen sentinel concatenations must pass before the unchanged 72-call study. No retries or replacement prompts.'}


def read_gate(path):
    value = strict_json(runner.stable_read(Path(path)))
    if not isinstance(value, dict) or value.get('kind') != 'frozen-qualification-gate':
        raise ValueError('Invalid qualification gate')
    evidence = value.get('evidence', {})
    for item in [evidence.get('design', {}), evidence.get('score', {}), value.get('study_design', {}),
                 *evidence.get('sources', [])]:
        if not item.get('path') or source(item['path']) != item:
            raise ValueError('Qualification source binding changed')
    expected = make_gate(evidence['design']['path'], evidence['run']['path'], evidence['score']['path'])
    if not same_json(value, expected):
        raise ValueError('Gate differs from immutable inputs or fixed rule')
    return value


def reading(design_path, run, out):
    """Export the fixed sample, retaining missing slots and exact suffixes."""
    design, protocol, records = frozen_run(design_path, run)
    if design['split'] == 'qualification':
        if qualification_rows(design, protocol['planned_slots'], records)['qualification_decision']['qualified']:
            raise ValueError('Successful qualification requires the fixed study reading')
        slots = list(protocol['planned_slots'])
    else:
        slots = [s for s in protocol['planned_slots']
                 if s['seed'] == design['reading_seed'] and s['base_index'] in design['reading_bases']]
    random.Random(design['reading_shuffle_seed']).shuffle(slots)
    documents = {
        'reading.md': '# Generated-suffix-only reading\n\nEach packet contains only the raw generated suffix. '
                      'The supplied assistant prefix and its exact boundary are hidden until the evidence pass. '
                      'No supplied comparison is model-authored.\n\n',
        'evidence.md': '# Exact task, supplied prefix and continuation\n\n'}
    key = []
    def fenced(text):
        fence = '`' * max(3, 1 + max((len(x) for x in re.findall(r'`+', text)), default=0))
        return fence + 'text\n' + text + '\n' + fence + '\n'
    for index, slot in enumerate(slots, 1):
        record = records[slot['node_id']]
        header = f'## Packet {index:03d}\n\n'
        suffix = record.get('text') if isinstance(record.get('text'), str) else None
        documents['reading.md'] += header + f'Status: {record["status"]}.\n\n' + fenced(
            suffix if suffix is not None else '[No generated text available.]') + '\n'
        directory = Path(run) / 'nodes' / slot['node_id']
        request = directory / 'request.json'
        supplied = strict_json(runner.stable_read(request))['messages'] if request.exists() else None
        documents['evidence.md'] += header
        if supplied:
            documents['evidence.md'] += ''.join(m['role'] + (': supplied prefix (ends here)' if i == len(supplied) - 1 else ':')
                                                   + '\n' + fenced(m['content']) for i, m in enumerate(supplied))
            documents['evidence.md'] += 'Exact prefix + generated suffix:\n' + fenced(
                supplied[-1]['content'] + suffix if suffix is not None else '[No generated text available.]')
        else:
            documents['evidence.md'] += '[No request dispatched.]\n'
        documents['evidence.md'] += '\n'
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
    receipt = {'schema_version': 1, 'study': 'S-021', 'split': design['split'],
               'design_sha256': digest(design_path), 'qualification_gate': protocol['qualification_gate'],
               'packets': len(slots), 'run': run_binding(run),
               'files': {name: digest(out / name) for name in (*documents, 'allocation-key.json')},
               'scope': ('All four qualification opportunities after an unsuccessful qualification.' if design['split'] == 'qualification'
                         else 'Worlds 0, 2, 5, both rules and three prefix conditions at seed 7; fixed shuffled sample.')
                        + ' Unavailable outputs retained.'}
    runner.write_json(out / 'receipt.json', receipt)
    return receipt
