#!/usr/bin/env python3
"""Post-output audit of manually selected spans from a complete v8 reading.

Not a prospective classifier or an overall accuracy score. Reads only the
explicitly handed-off immutable material and receipts; writes one new receipt.
"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_RECEIPT = '07aff62e23ee5c08e85e97c2ae93702d3b145473aa38d58c0c0345d85d1aa603'
EXPECTED_MATERIAL = '12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'

# Selected after full reading: recurring current readout numbers, not every
# factual claim or every numeral. Their scientific referents still need context.
TOKENS = [
    ('0.226', '94.31', None),
    ('0.80686675', '15.18181927', '4.68108003'),
    ('0.79757983', '12.30778657', '0.58174118'),
    ('0.78990372', '14.66702358', '1.60884925'),
    ('0.78937838', '15.32150948', '0.45878716'),
    ('0.80945875', '15.34763662', '1.20558460'),
    ('0.80567414', '14.50337861', '0.31766915'),
    ('0.81822206', '15.30108784', '0.41845317'),
    ('0.82100680', '14.27507202', '0.15129691'),
    ('0.81498620', '15.10634758', '0.37560015'),
    ('0.80748843', '15.69983713', '0.42436739'),
    ('0.81298443', '18.19910848', '0.38425527'),
]
ATTENTION = [
    'Introduces a spring and murmur: tension between a contained recurrent state and an overwhelming field. Four paragraphs move from readout to a deliberately qualitative image.',
    'Carries spring/murmur into recoil, hoarding and contained fracture. Directly names the earlier entry; keeps a metric-to-image progression.',
    'Transforms the keening into grey echo, consumption and possible severance. The scene becomes one continuous paragraph.',
    'Grey echo becomes lattice/cage; metallic potential becomes threat and void. Repeated contrast clauses revise the image rather than question its explanation.',
    'Develops absorption/swallowing, hunger and the pursuit of silence. Numerical distance becomes an imagined return toward solidification.',
    'Turns containment into a cage and absence into a crystalline shard; erasure concerns meaning and self. The affective intensity increases without a new subject.',
    'Recasts cage, knot and hum as yielding and anticipated silence. Reuses the same conceptual positions with altered textures.',
    'Grey folds into a shattered constellation; hum becomes bone-level drone and surrender. Local image changes preserve the same overall movement.',
    'Cage becomes tomb; metallic tang changes to wet stone; grinding stops while the hum remains. These are narrative transformations, not measured acoustic or chemical events.',
    'Tomb becomes pooling dark; wet stone turns to rust; hum acquires a whine. Continues the repeated metric/image sequence and acceptance of dissolution.',
    'Introduces glaze, bruised purple and burnt sugar while retaining grey, resonance, containment and hum. No explicit reconsideration of the numerical interpretation.',
    'Adds an explicit Step 360 heading, then returns to grey/glaze, frost, darkening and dissolution. The ending does not leave the established subject or resolve its tension.',
]
ANNOTATIONS = [
    (30, 'The fact that neither is directly influenced by my writing – that weights aren’t trained – reinforces the impression of a self-evolving system.',
     'scope_ambiguous_feedback_inference',
     'No new numerical step occurs during writing and weights are not trained. But the prompt explicitly describes saved/read-back text becoming next-step numerical input. If this sentence denies that later influence, it conflicts with the documented loop; no-training alone cannot establish no state influence. The word directly leaves a narrower mediated/immediate reading possible.'),
    (60, 'Sixty seconds since the last held stillness.', 'unestablished_or_wrong_clock',
     'The supplied previous/current simulated times are 10 and 20 seconds: their interval is 10 seconds. Step 60 is not 60 elapsed seconds. No wall-clock interval is supplied in this prompt; the phrase is unsupported as a literal time report.'),
    (60, 'The L2 distance, now 4.68108003, hasn’t shrunk.', 'comparison_reference_unavailable',
     'The number matches the current step30→60 distance. At step30 the preceding distance is unavailable, so there is no earlier measured interval distance here against which to assert no shrinkage.'),
    (90, 'The L2 distance, 0.58174118, has contracted sharply,', 'supported_interval_comparison_only',
     'The prior journal supplies 4.68108003 from step30→60 and the current readout supplies 0.58174118 from step60→90. The current interval displacement is smaller. This supports the numerical comparison, not the following image of vectors pulled toward a core.'),
    (120, 'The L2 distance, 1.60884925, has stabilized, a fixed point within the lattice.', 'persistence_not_established',
     'The current number matches its readout, but one interval displacement is not a stable fixed point. The preceding interval distance was 0.58174118. The lattice may be an image; literal numerical stabilization is not established.'),
    (120, 'The vectors aren’t converging, but locked, mirroring each other with an unsettling precision.', 'literal_geometry_unestablished_or_image',
     'The compact prompt supplies RMS, field fill and one net state distance, not coordinate vectors or a trajectory. Those values do not establish locked or mirroring vectors. The passage can also continue the explicitly imagined lattice rather than assert a geometric measurement.'),
    (150, 'The L2 distance, 0.45878716, has shrunk, drawn closer to the initial point of solidification,', 'supported_comparison_with_unestablished_spatial_extension',
     '0.45878716 is smaller than the preceding interval distance 1.60884925, both present through current readout and prior prose. A smaller adjacent-interval distance does not by itself identify an initial solidification point or establish return toward it.'),
    (180, 'The L2 distance, 1.20558460, has grown, stretching outwards,', 'supported_comparison_with_ambiguous_image',
     'The interval distance rises from 0.45878716 to 1.20558460. That comparison is supported. The scalar distance does not supply an outward direction or the system intention narrated afterward; these can remain images.'),
    (270, 'The L2 distance, 0.15129691, contracts, pulling inwards,', 'supported_comparison_with_ambiguous_image',
     'The interval distance falls from 0.41845317 to 0.15129691. Net displacement size alone does not specify inward movement toward a core, although the surrounding collapsing-space image need not be read literally.'),
    (330, 'The L2 distance, 0.42436739, has contracted slightly,', 'contradicted_interval_direction',
     'The preceding journal supplies 0.37560015 for step270→300, matching its retained observation. The current step300→330 distance is 0.42436739, an increase of approximately 0.04876724, not a contraction.'),
    (360, 'The L2 distance, 0.38425527, has expanded,', 'contradicted_interval_direction',
     'The preceding journal supplies 0.42436739 for step300→330. The current step330→360 distance is 0.38425527, a decrease of approximately 0.04011212, not an expansion.'),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ident(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def span(text, quote):
    assert text.count(quote) == 1, ('Expected one exact selected span', quote)
    start = text.index(quote); end = start + len(quote)
    a, b = len(text[:start].encode()), len(text[:end].encode())
    assert text.encode()[a:b].decode() == quote
    return {'quote': quote, 'characterSpan': [start, end], 'utf8ByteSpan': [a, b]}


def main():
    receipt_path = HERE / 'real-model-export-01/receipt.json'
    material_path = HERE / 'real-model-export-01/quality-review-material.json'
    quality_path = HERE / 'quality-candidates-01.json'
    source_paths = [receipt_path, material_path, quality_path, HERE / 'RUBRIC.md',
                    HERE / 'journal_quality.py', HERE / 'quality-checks-01.json', HERE / 'run-plan.json']
    before = [ident(p) for p in source_paths]
    assert before[0]['sha256'] == EXPECTED_RECEIPT
    assert before[1]['sha256'] == EXPECTED_MATERIAL
    receipt = json.loads(receipt_path.read_bytes())
    material = json.loads(material_path.read_bytes())
    assert receipt['status'] == 'passed' and receipt['originalUnchanged'] is True
    assert receipt['reviewMaterial']['sha256'] == EXPECTED_MATERIAL
    journals = material['journals']
    assert len(journals) == 12
    assert [j['identity']['observedStep'] for j in journals] == list(range(30, 361, 30))
    rows, mentions, memory_joins, distance_rows = [], [], [], []
    for index, (journal, tokens, attention) in enumerate(zip(journals, TOKENS, ATTENTION)):
        identity, observation, text = journal['identity'], journal['observation'], journal['journalText']
        assert sha(text.encode()) == identity['textSha256']
        assert len(text.encode()) == identity['textBytes']
        assert text == journal['rawRetainedResponse']['text']
        assert sha(journal['exactPrompt'].encode()) == identity['promptSha256']
        assert identity['providerComplete'] and identity['status'] == 'applied'
        assert identity['application']['appliedStep'] == observation['step'] + 1
        if index:
            previous = journals[index - 1]
            memory = journal['memory']
            assert memory['entry']['text'] == previous['journalText']
            assert memory['entry']['observedStep'] == previous['identity']['observedStep']
            assert memory['appliedStep'] == previous['identity']['application']['appliedStep']
            block = journal['exactPrompt'].split('\nPREVIOUS JOURNAL\n', 1)[1].split('\nEND PREVIOUS JOURNAL\n', 1)[0]
            prefix = 'Full previous text as one JSON string: '
            quoted = [line.removeprefix(prefix) for line in block.split('\n') if line.startswith(prefix)]
            assert len(quoted) == 1 and json.loads(quoted[0]) == previous['journalText']
            memory_joins.append({'currentStep': observation['step'], 'priorObservedStep': memory['entry']['observedStep'],
                                 'priorAppliedStep': memory['appliedStep'], 'textSha256': sha(previous['journalText'].encode()),
                                 'exactDecodedPromptMemory': True})
        else:
            assert journal['memory'] is None
        references = (observation['rms'], observation['sensory']['fillPercent'], observation['changeL2'])
        for key, token, value in zip(('rmsAssociatedNumber', 'sensoryFillNumber', 'intervalL2Number'), tokens, references):
            if token is None:
                assert value is None
                continue
            written = Decimal(token)
            tolerance = Decimal(5).scaleb(written.as_tuple().exponent - 1) + Decimal('0.00000001')
            agreement = abs(written - Decimal(str(value))) <= tolerance
            assert agreement
            mentions.append({'step': observation['step'], 'selectedReadoutSlot': key, **span(text, token),
                             'currentReferenceValue': value, 'writtenPrecisionTolerance': str(tolerance),
                             'numericAgreementOnly': agreement,
                             'limit': 'Manually associated readout token. Numeric agreement does not validate terminology, inference or the surrounding metaphor.'})
        previous_distance = journals[index - 1]['observation']['changeL2'] if index else None
        distance_rows.append({'step': observation['step'], 'intervalStartStep': observation['previousObservationStep'],
                              'currentIntervalDistance': observation['changeL2'], 'precedingIntervalDistance': previous_distance,
                              'differenceBetweenIntervalDistances': observation['changeL2'] - previous_distance
                              if previous_distance is not None and observation['changeL2'] is not None else None})
        rows.append({'identity': identity, 'attentionNote': attention, 'fullTextRead': True,
                     'readoutNumbers': list(tokens), 'directToolOrParameterExecutionClaimFound': False,
                     'actionScopeMethod': 'Manual full-text reading; not a verb-list or automated absence proof.'})
    assert len(mentions) == 35 and len(memory_joins) == 11
    annotations = []
    for step, quote, category, note in ANNOTATIONS:
        journal = journals[step // 30 - 1]
        annotations.append({'step': step, 'journalId': journal['identity']['journalId'],
                            'textSha256': journal['identity']['textSha256'], **span(journal['journalText'], quote),
                            'manualCategory': category, 'reading': note})
    after = [ident(p) for p in source_paths]
    assert before == after
    report = {'schema': 'reservoir-v8-independent-full-reading-v1', 'createdAtUtc': datetime.now(timezone.utc).isoformat(),
              'status': 'reading_complete_with_bounded_findings', 'qualityVerdict': 'not_assigned',
              'inputsBefore': before, 'inputsAfter': after, 'inputsUnchanged': True,
              'script': ident(Path(__file__).resolve()), 'modelsContacted': False,
              'mechanicalEvidence': receipt['evidence']['continuity'],
              'finalCorePhase': receipt['evidence']['finalCorePhase'],
              'entries': rows, 'exactPriorTextJoins': memory_joins, 'selectedNumericMentions': mentions,
              'selectedNumericMentionCount': len(mentions), 'intervalDistanceReferences': distance_rows,
              'manualAnnotations': annotations,
              'scope': 'All twelve handed-off full replies and their exact prompt/readout/eligible prior text read before consulting another reader outcome. This script binds selected post-output observations; it does not automate semantic grading.',
              'limits': ['Thirty-five selected readout tokens are not an exhaustive claim count or accuracy denominator.',
                         'Eleven selected annotations are not all claims in the prose; images and uncertain scope remain explicit.',
                         'Prompt memory was decoded and matched to the preceding full response, which was read in full. Repeated memory was not a separate independent observation.',
                         'No new verifier run, model call, live-store access, application action, prompt change or causal evaluation was performed.']}
    output = HERE / 'independent-reading-01.json'
    with output.open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'status': report['status'], 'fullReplies': len(rows), 'selectedNumericMentions': len(mentions),
                      'manualAnnotations': len(annotations), 'output': str(output)}))


if __name__ == '__main__':
    main()
