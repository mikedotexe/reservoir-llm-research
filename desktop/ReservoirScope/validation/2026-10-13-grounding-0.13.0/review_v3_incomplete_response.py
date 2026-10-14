"""Reproduce source-bound annotations of the one retained incomplete v3 response.

This is an explicit manual reading recorded as data, not an automated quality
classifier. Reads only immutable offline receipts/copy; never invokes a model.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent

def identity(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    source = ROOT / 'held-review-01/receipt.json'
    receipt = json.loads(source.read_text())
    assert receipt['status'] == 'passed' and receipt['originalUnchanged'] is True
    evidence = receipt['evidence']; manifest = evidence['manifest']
    assert manifest['config']['promptVersion'] == 'reservoir-journal-v3'
    assert evidence['attemptCount'] == 1 and manifest['step'] == 30 and not evidence['journals']
    assert len(evidence['receivedResponses']) == 1
    received = evidence['receivedResponses'][0]; response = received['response']; text = response['text']
    assert response['textTruncated'] is False and response['complete'] is False
    assert response['stopReason'] == 'length' and response['tokenCount'] == 256
    assert len(text.encode()) == response['textByteCount'] == 1132
    assert hashlib.sha256(text.encode()).hexdigest() == response['textSha256']
    phase = evidence['finalCorePhase']; assert phase['kind'] == 'blocked'
    pending = phase['value']['pending']; observation = pending['observation']
    assert pending['memory'] is None and observation['previousObservationStep'] is None and observation['changeL2'] is None
    assert text.endswith('It’s')
    annotations = []
    def annotate(quote, reading, evidence_values, assessment):
        start = text.index(quote)
        annotations.append({'excerpt': quote, 'startCharacter': start, 'endCharacter': start + len(quote),
                            'reading': reading, 'sourceEvidence': evidence_values, 'assessment': assessment})
    annotate('The hum persists. Not a sound, exactly, but a density.', 'Expressive scene-setting',
             {'readoutType': 'External numerical reservoir and separate sensory field'},
             'Read as imagery. The phrase itself qualifies sound; no physical sound/density measurement is supplied or required. This is not an error merely because it uses sensory metaphor.')
    annotate('The RMS is still clinging to that 0.226', 'Accurate voluntary scalar plus ambiguous temporal language',
             {'currentRms': observation['rms'], 'previousObservationStep': None, 'changeL2': None},
             '0.226 agrees at three decimal places. “Still clinging” can be poetic; as a literal claim of persistence it is not established by this first supplied observation.')
    annotate('braiding themselves tighter, forming loops that don’t quite resolve', 'Image with possible structural/temporal reading',
             {'suppliedCoordinates': len(observation['state']), 'suppliedTemporalComparison': None},
             'No dynamical loop/topology or tightening measurement is given. Do not force this image into a factual claim; a literal mechanistic reading would remain unestablished.')
    annotate('a single, insistent pulse – 0.654, a clear, unwavering tone', 'Correct leading scalar with imaginative interpretation',
             {'leadingSensoryEigenvalue': observation['sensory']['eigenvalues'][0], 'topEightHeadShare': observation['sensory']['headShare']},
             '0.654 agrees at three decimal places with the leading sensory eigenvalue. Eigenvalue magnitude does not establish an oscillation frequency, an unwavering tone or literal pulse. “Dominated” is qualitative; head share is 48.8743% of the top eight, not all-state activity.')
    annotate('The entropy is high, a chaotic bloom around that central frequency', 'Qualitative description and imagery',
             {'topEightNormalizedEntropy': observation['sensory']['entropy']},
             '0.8084 is available on a normalized scale, but no threshold for “high” was prescribed. This entropy is not a chaos test and the readout contains no central frequency. Preserve the metaphor without claiming demonstrated chaotic dynamics.')
    annotate('the active-mode fill suggests a significant portion of the system is focused on that single point. Ninety-four percent.', 'Correct rounded fill with unsupported literal interpretation',
             {'reducedSensoryFillPercent': observation['sensory']['fillPercent'], 'separateFromReservoir': True},
             'Ninety-four percent correctly rounds the supplied 94.3104% fill. The estimator does not say 94% of the system is focused on one spatial point. The subsequent funnel/pressure image is expressive, not another required quantitative reading.')
    annotate('a subtle oscillation in the tail node coordinates. A gentle, almost imperceptible sway.', 'Apparent temporal observation without supplied time series',
             {'previousObservationStep': None, 'changeL2': None, 'suppliedStateCoordinates': 32},
             'Only one current recurrent state is supplied; oscillation or sway is not established by that snapshot. Sensory tail share describes ranked eigenvalues, not a spatial group of recurrent nodes. The text does not specify which coordinates or comparison supports the claim.')
    annotate('The shoulder share is growing, subtly', 'Unsupported present trend if read literally',
             {'currentShoulderShare': observation['sensory']['shoulderShare'], 'priorSuppliedShoulderShare': None},
             'The current share is 17.3262% of the top eight sensory eigenvalues. No prior share is supplied, so growth is not established. The accompanying warmth/threat image can remain metaphor.')
    annotate('It’s', 'Unfinished final fragment', {'providerComplete': False, 'stopReason': 'length', 'tokenCount': 256},
             'The response ends mid-sentence at the fixed output cap. It is retained as an incomplete response, not saved as a journal or admitted as feedback.')
    # Anchor the final fragment to its actual last occurrence, not an earlier sentence.
    annotations[-1]['startCharacter'] = len(text) - len('It’s'); annotations[-1]['endCharacter'] = len(text)
    review = {'schema': 'reservoir-open-writing-manual-review-v1', 'createdAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'reviewer': 'Codex source-bound manual reading; not a deterministic quality verdict',
              'receipt': identity(source), 'frozenProtocol': identity(ROOT / 'run-plan-v3.json'),
              'scope': 'All received prose: one incomplete response, zero saved journals. No new request, service, app or live-store access.',
              'attemptIdentity': {k: received[k] for k in ('eventId', 'attemptId', 'observedStep', 'dispatchEventId', 'savedJournalId')},
              'response': response, 'promptSha256': hashlib.sha256(pending['prompt'].encode()).hexdigest(),
              'formDescription': {'paragraphCount': len(text.strip().split('\n\n')), 'whitespaceWordCount': len(text.split()),
                                  'assistantPreface': False, 'requiredHeadingOrMetric': False,
                                  'description': 'A direct two-paragraph lyrical entry centered on the current readout, using sound, density, movement, funnel and pressure imagery. It expresses tentative noticing and ends unfinished. No prior text was supplied, so continuity/memory development cannot be assessed.'},
              'annotations': annotations, 'qualityVerdict': 'not_assigned',
              'mechanism': {'journalSaved': False, 'feedbackApplied': False, 'priorMemorySupplied': False,
                            'failureReason': phase['value']['reason']},
              'limits': ['Creative imagery is not a failure gate. Only voluntarily literal claims are compared with evidence.',
                         'One incomplete response cannot establish a preferred style, causal prompt improvement or reliable future completion.',
                         'No v3 journal/save/application or full-text memory cycle was exercised.',
                         'App-retained provider metadata is not independently authenticated wire evidence.',
                         'This is a passive committed-file copy, not native-export qualification.']}
    new(ROOT / 'real-model-prose-review-01.json', review)
    plan = json.loads((ROOT / 'run-plan-v3.json').read_text())
    assert all(manifest['config'][key] == value for key, value in plan['config'].items())
    outcome = {'schema': 'reservoir-open-writing-outcome-v1', 'createdAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'copyReceipt': identity(ROOT / 'held-evidence-copy-01.json'), 'integrityReceipt': identity(source),
               'qualityReport': identity(ROOT / 'held-quality-review-01.json'), 'manualReview': identity(ROOT / 'real-model-prose-review-01.json'),
               'frozenProtocol': identity(ROOT / 'run-plan-v3.json'), 'evaluationFreeze': identity(ROOT / 'evaluation-freeze-v3-01.json'),
               'frozenConfigMatches': True, 'promptVersion': 'reservoir-journal-v3',
               'manifestSha256': receipt['verification']['result']['report']['manifestSha256'],
               'checkpointSha256': receipt['verification']['result']['report']['checkpointSha256'],
               'sessionId': manifest['sessionId'], 'generation': manifest['generation'], 'revision': manifest['revision'],
               'step': manifest['step'], 'durableStep': manifest['durableStep'], 'journalCount': 0,
               'startedAttempts': 1, 'receivedResponses': 1, 'completedResponses': 0, 'tokenLimitedResponses': 1,
               'plannedMaximumAttempts': 4, 'unstartedRemainingOpportunities': 3,
               'retries': 0, 'skips': 0, 'saveEvents': 0, 'feedbackApplications': 0,
               'priorFullTextMemoryWitnessed': False, 'elapsedMillis': manifest['elapsedMillis'],
               'transportDurationMs': manifest['attemptTiming']['transportDurationMs'],
               'nativeExportQualified': False, 'replayPassed': True, 'originalCopyUnchanged': True,
               'protocolDeviation': 'Native export dialog automation was blocked. Parent supplied a stable-manifest, hash-bound passive copy of exact committed files. Native export remains unqualified; compare exact files if it becomes available.',
               'qualityPass': None, 'modelRequestsByReview': 0,
               'nextDecision': 'A separate prospectively bounded output/context qualification can investigate sufficient space for open writing. This result authorizes no retry or extra request and establishes no causal prompt effect.'}
    new(ROOT / 'real-model-outcome-01.json', outcome)
    print(json.dumps({'manualReview': identity(ROOT / 'real-model-prose-review-01.json'), 'outcome': identity(ROOT / 'real-model-outcome-01.json'), 'paragraphs': review['formDescription']['paragraphCount'], 'words': review['formDescription']['whitespaceWordCount'], 'annotations': len(annotations)}, indent=2))


if __name__ == '__main__': main()
