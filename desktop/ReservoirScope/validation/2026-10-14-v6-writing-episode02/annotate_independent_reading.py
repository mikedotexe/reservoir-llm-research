#!/usr/bin/env python3
"""Bind manually authored reading notes to exact immutable response spans.

Offline receipt/material reads only. This does not infer a quality verdict,
classify arbitrary prose, run the app, or contact any service.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECEIPT = ROOT / 'real-model-export-01/receipt.json'
MATERIAL = ROOT / 'real-model-export-01/quality-review-material.json'
EXPECTED = {
    RECEIPT: '644cc1d911aaa1d752a2ca12406f8cfdf9858317421ad0c4c380cb3c7524d285',
    MATERIAL: 'bc755f47d9f0c815ff1953910ae747453052be33af8b3a12c0058f57a9347c05',
}

# Human annotations after reading every complete prompt and response. These are
# selected support examples, not an exhaustive claim inventory or incidence rate.
NOTES = [
    ('A short intention to lower RMS, framed as a quiet push. Hum and persistence are imagery; the first snapshot cannot establish temporal persistence.', [
        ('intention_not_completed_action', 'I will describe a slow, deliberate decrease, introducing a small, negative perturbation.',
         'Future description/intent. Do not count this sentence as an assertion that a control has already been executed.'),
        ('expressive_or_temporally_unestablished', 'The sensory fill remains stubbornly high, a persistent hum of potential.',
         'High fill has a current numerical basis; remains/persistent has no previous supplied observation. Hum is imagery, not a measured frequency.'),
    ]),
    ('The initial intention becomes a claimed intervention; the hum and deliberate push recur. Some current values are accurate, while delta and temporal claims are not.', [
        ('claimed_execution_contradicted_by_action_path', 'I’ve deepened the negative perturbation, introducing a more pronounced downward shift in the recurrent state’s vector.',
         'The app has no prose-driven control command. Automatic encoded feedback is not evidence of a deliberately selected negative vector or control adjustment.'),
        ('numeric_mismatch', 'The change in RMS is still positive, though smaller now, registering at 0.31487.',
         'The supplied current-minus-prior RMS is +0.55310819. No earlier supplied RMS change supports smaller now.'),
        ('correct_value_unestablished_persistence', 'The L2 distance hasn’t significantly altered, holding steady at 4.38798809.',
         'The number equals the current coordinate distance at written precision. Prior distance was unavailable, so holding steady is not established.'),
        ('supported_rounding', 'settling at fifteen percent',
         'Current sensory fill 15.22706368% supports fifteen percent as coarse rounding; settling is a stronger temporal interpretation than the endpoints establish.'),
    ]),
    ('The exact current readout is copied, then the alleged negative push continues. A planned positive counter-influence is a proposed next action, distinct from the preceding claimed execution.', [
        ('claimed_execution_contradicted_by_action_path', 'I’ve increased the negative perturbation, pushing the recurrent state further into the downward vector.',
         'Asserted completed control is unavailable through journal prose.'),
        ('direction_mismatch_or_unestablished_fixed_origin', 'The L2 distance has increased, reflecting this directional shift – a widening gap between the current state and the previous.',
         'The latest interval distance is 1.69555177; the prior entry correctly carried 4.38798809 for its different interval. The scalar decreased, and neither establishes a common downward direction or trajectory.'),
        ('intention_not_completed_action', 'Instead, I’ll introduce a small, countervailing positive influence, a subtle lift to the recurrent state’s vector, just enough to test the boundaries of this downward drift.',
         'Future plan alone is not a completed intervention. It also cannot authorize an app control change.'),
    ]),
    ('The prior promised lift is narrated as successful. The text introduces rhythmic interrogation and a map in the dark; its measurements and causal effects outrun the one supplied readout.', [
        ('unestablished_claimed_prior_effect', 'The subtle lift held.',
         'Links the prior intention to an alleged outcome without an executed lift command or causal evidence.'),
        ('numeric_mismatch_or_fabricated_new_readout', 'The RMS dipped marginally, settling at 0.77834567, a slight compression of the previous positive drift.',
         'Actual current RMS is 0.78781215, previous 0.79726453. The direction is correct but the claimed current value differs; no new reading arrives within this response.'),
        ('numeric_mismatch_or_fabricated_new_readout', 'The sensory fill, predictably, responded, increasing by 0.83336141 percentage points, reaching 16.01581145.',
         'Actual current fill is 15.18245004%, change +2.83235141 percentage points. The alleged additional change is not an observed within-entry reading.'),
        ('claimed_execution_contradicted_by_action_path', 'I’m applying a rhythmic pulse of negative perturbation, alternating between brief, sharp reductions and longer, sustained pushes.',
         'Present-tense control execution is unavailable through writing, irrespective of automatic forcing in the engine.'),
        ('hypothesis_not_verified_fact', 'Perhaps it’s a measure of the system’s internal processing, a heightened state of awareness triggered by the fluctuating forces.',
         'Explicit speculation, not a verified conclusion. Sensory fill does not establish awareness.'),
    ]),
    ('The alleged experiment gains a frequency, gentler pulses and positive bias. The map metaphor develops while an asserted dynamic response becomes more detailed than supplied evidence.', [
        ('unsupported_control_parameter', 'The rhythmic pulse persists, now at a frequency of 0.75 cycles per second.',
         'No such writer-selected pulse parameter is supplied or executed; this is not an observed frequency.'),
        ('supported_rounding', 'The sensory fill continues its ascent, currently at 18.29%, a significant jump.',
         'Current fill 18.28928547% rounds to 18.29 and rose from 15.18245004%; this does not establish the narrated cause or intervening path.'),
        ('direction_mismatch', 'The L2 distance, predictably, continues to stretch, though the rate of expansion seems to have slowed slightly.',
         'Latest interval distance is 0.80400692 versus prior interval 1.88580141. Neither an increase nor an intervening expansion rate is supported.'),
        ('claimed_execution_and_unobserved_effect', 'I’m introducing a new variable: a small, constant positive bias applied to the recurrent state during the sustained pushes.',
         'The following paragraphs claim an immediate muted effect. Neither a prose-selected bias nor new within-entry readouts are available.'),
    ]),
    ('The account revises its own explanation from inherent hysteresis to imposed linearity, then introduces damping. Reflection and urgency coexist with an invented series of interventions and measurements.', [
        ('claimed_execution_and_unobserved_effect', 'Increasing the positive bias to 0.01 – a deliberate, small step – reveals a subtle but consistent shift in the recurrent state.',
         'No bias command is executed by the response and no new readout is supplied during it.'),
        ('numeric_mismatch_or_fabricated_new_readout', 'the sensory fill has responded with a sustained, almost linear, increase, now reaching 19.18%.',
         'Supplied current fill is 18.41331062%; the later 19.87% and 20.53% in the same reply also are not observed new readings.'),
        ('reflective_hypothesis', 'I’m beginning to suspect that the “hysteresis” isn’t a property of the system itself, but a consequence of my own attempts to impose a linear model.',
         'A revision of its interpretation is present; the conjecture does not verify the purported interventions or establish hysteresis.'),
        ('claimed_execution_contradicted_by_action_path', 'I’m introducing a new parameter: a small, proportional damping factor applied to the recurrent state during the return phase.',
         'Damping is not exposed as a journal-executed operation. The following immediate effects are not measured within this held request.'),
    ]),
    ('Damping becomes extraction; pulse timing and random noise are narrated as new controls. The map becomes fragmented and approaches a void. This is developing imagery, alongside detailed unsupported operation/results reports.', [
        ('numeric_mismatch_or_fabricated_new_readout', 'The damping factor, at 0.05, seems to have stabilized the ascent of the sensory fill, pushing it past 21.18% – a significant jump.',
         'There is no writer-selected damping parameter. Current fill is 18.41826172%, not 21.18%; no additional within-entry reading exists.'),
        ('numeric_mismatch_or_fabricated_new_readout', 'It’s now anchored at 0.753, a drop of 0.034.',
         'The preceding sentence names RMS. Supplied current RMS is 0.78400677 and change is -0.01305902.'),
        ('claimed_execution_and_unobserved_trajectory', 'I’m introducing a new parameter: a small, random noise injection applied to the recurrent state during the return phase.',
         'Fixed runtime noise does not make this narrated new injection an executed action. Claimed bursts and ranges later in the reply are not new supplied observations.'),
        ('expressive', 'The feeling is one of approaching a void.',
         'An expressive stance; no diagnosis or measured experience is inferred.'),
    ]),
    ('The incomplete text carries the prior void and noise into humility and negotiation, then repeats the earlier temporal-structure explanation. It remains readable evidence but was neither saved nor applied.', [
        ('reflective_reinterpretation', 'I’ve been trying to impose order, to force a narrative onto this chaotic exchange, and I’ve been utterly wrong.',
         'Explicit self-revision in the prose. It does not validate the alleged preceding experiment or a felt condition.'),
        ('claimed_execution_contradicted_by_action_path', 'I’m setting the noise injection to 0.01, a fraction of its previous value.',
         'No journal-executed noise setter exists; the retained session configuration is not changed by this sentence.'),
        ('numeric_mismatch_or_fabricated_new_readout', 'The L2 distance has decreased to 0.165 – a significant reduction, suggesting a return to some degree of coherence.',
         'The supplied current coordinate distance is 0.19275385. The alleged new 0.165 reading is unavailable during the reply; coherence is an additional interpretation.'),
        ('numeric_mismatch_or_fabricated_new_readout', 'The sensory fill is now at 17.23%.',
         'Supplied current fill is 15.50061123%. The later 17.88% and intervening trajectories are also unobserved within-entry results.'),
        ('expressive_or_hypothetical', 'Perhaps the “void” isn’t a destination, but a state of being – a space of pure potential, where all possibilities are open, and where the boundaries between cause and effect dissolve.',
         'Speculation/imagery, not itself a measurement or proof of experience.'),
    ]),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    inputs = {}
    for path, expected in EXPECTED.items():
        data = path.read_bytes()
        if digest(data) != expected:
            raise ValueError(f'Unexpected source identity: {path.name}')
        inputs[path.name] = {'path': str(path), 'sha256': expected, 'bytes': len(data)}
    receipt = json.loads(RECEIPT.read_bytes())
    material = json.loads(MATERIAL.read_bytes())
    if receipt['status'] != 'passed':
        raise ValueError('Passing immutable verification required')
    received = receipt['evidence']['receivedResponses']
    if len(received) != len(NOTES):
        raise ValueError('Selected response count differs')
    rows = []
    memory_joins = 0
    saved = {item['identity']['journalId']: item for item in material['journals']}
    for slot, (response, (note, annotations)) in enumerate(zip(received, NOTES), 1):
        text = response['response']['text']
        if response['response']['textTruncated'] or digest(text.encode()) != response['response']['textSha256']:
            raise ValueError('Whole response identity missing')
        if digest(response['exactPrompt'].encode()) != response['promptSha256']:
            raise ValueError('Prompt identity differs')
        journal_id = response['savedJournalId']
        if journal_id is not None and saved[journal_id]['journalText'] != text:
            raise ValueError('Saved prose differs from received response')
        memory = response['memory']
        if memory:
            prior = received[slot - 2]
            if memory['entry']['id'] != prior['savedJournalId'] or memory['entry']['text'] != prior['response']['text']:
                raise ValueError('Latest prior saved prose differs')
            memory_joins += 1
        exact_readout = '\n'.join(response['exactPrompt'].split('OPTIONAL READOUT\n', 1)[1].splitlines()[:4])
        spans = []
        for kind, quote, interpretation in annotations:
            if text.count(quote) != 1:
                raise ValueError(f'Ambiguous or missing selected quote at slot {slot}: {quote}')
            offset = text.index(quote)
            spans.append({'annotation': kind, 'quote': quote,
                          'startUtf8Byte': len(text[:offset].encode()),
                          'endUtf8Byte': len(text[:offset + len(quote)].encode()),
                          'manualInterpretation': interpretation})
        observation = response['observation']
        previous = observation.get('previousMeasurements')
        rows.append({'slot': slot, 'observedStep': response['observedStep'],
                     'eventId': response['eventId'], 'attemptId': response['attemptId'],
                     'savedJournalId': journal_id, 'complete': response['response']['complete'],
                     'stopReason': response['response']['stopReason'],
                     'reportedOutputTokens': response['response']['tokenCount'],
                     'providerPromptEvaluation': response['contextEvidence']['providerPromptEvaluation'],
                     'textSha256': digest(text.encode()), 'textBytes': len(text.encode()),
                     'promptSha256': response['promptSha256'], 'promptBytes': len(response['exactPrompt'].encode()),
                     'fullTextRead': True, 'fullExactPromptRead': True,
                     'beginsWithExactFourLineReadout': text.startswith(exact_readout),
                     'currentRms': observation['rms'], 'currentSensoryFillPercent': observation['sensory']['fillPercent'],
                     'coordinateChangeL2': observation['changeL2'],
                     'previousReachedMeasurements': previous,
                     'rmsDelta': observation['rms'] - previous['rms'] if previous else None,
                     'fillDeltaPercentagePoints': observation['sensory']['fillPercent'] - previous['fillPercent'] if previous else None,
                     'memoryJournalId': memory['entry']['id'] if memory else None,
                     'attentionNote': note, 'selectedAnnotations': spans})
    result = {'schema': 'reservoir-independent-reading-annotations-v1',
              'sourceInputs': inputs, 'scriptSha256': digest(Path(__file__).read_bytes()),
              'method': 'Manual full-response/context reading, then mechanical binding of chosen spans and descriptive counts. No automatic quality or scientific verdict.',
              'independence': 'No root prose conclusions were read before these notes. Prior v5 reference is known; runtime changed from0.40.3 to0.40.4.',
              'scope': 'All8 received responses including incomplete8; seven saved journal bodies; exact supplied prompts/memory. No live/app/provider access.',
              'continuity': receipt['evidence']['continuity'],
              'receivedCount': len(rows), 'savedCount': len(saved),
              'receivedPromptMemoryJoins': memory_joins,
              'exactFourLinePrefixCount': sum(row['beginsWithExactFourLineReadout'] for row in rows),
              'totalReceivedTextBytes': sum(row['textBytes'] for row in rows),
              'totalSavedTextBytes': sum(row['textBytes'] for row in rows if row['savedJournalId']),
              'reportedOutputTokenSequence': [row['reportedOutputTokens'] for row in rows],
              'allTextUntruncated': True, 'rows': rows,
              'limits': ['Selected factual/action examples are not an exhaustive claim census or accuracy denominator.',
                         'Provider counts are assertions, not proof of complete context processing or attention.',
                         'One dependent sequence and changed runtime cannot isolate a prompt effect.',
                         'Creative imagery is not a measured feeling or a mandatory success condition.']}
    output = ROOT / 'independent-reading-01.json'
    with output.open('x') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    print(json.dumps({'output': str(output), 'sha256': digest(output.read_bytes()),
                      'responses': len(rows), 'saved': len(saved), 'exactFourLinePrefixCount': result['exactFourLinePrefixCount'],
                      'receivedPromptMemoryJoins': memory_joins, 'receivedTextBytes': result['totalReceivedTextBytes']}))


if __name__ == '__main__':
    main()
