#!/usr/bin/env python3
"""Retain authored close-reading annotations plus exact local-export measurements.

This is not an automatic quality score. It reads only the prior offline checker
output and explicitly named qualification receipts; no app/service calls.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json

V = Path(__file__).resolve().parent
OUT = V / 'real-model-export-01'
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

ANNOTATIONS = {
    30: [
        {'quote': 'RMS is low (0.226)', 'assessment': 'value supported', 'basis': 'Current RMS rounds to 0.226; low is a qualitative judgment without a stated comparison threshold.'},
        {'quote': 'indicating good convergence within the first few steps', 'assessment': 'not established', 'basis': 'The prompt has one observation at global step30 and explicitly unavailable prior-observation change. A single RMS does not establish temporal convergence.'},
        {'quote': 'dominant mode at 0.654', 'assessment': 'value supported', 'basis': 'Current top sensory eigenvalue rounds to0.654. The sensory field is explicitly separate from recurrent state.'},
        {'quote': 'high normalized entropy (0.8084) and active-mode fill percentage (94.31%)', 'assessment': 'values supported; processing inference not established', 'basis': 'Both numbers round correctly. These are top-eight sensory entropy and reduced active-mode fill, not a direct measure of recurrent processing or cognition.'},
        {'quote': 'consistent, near-uniform distribution of the sensory field eigenvalues', 'assessment': 'overgeneralized', 'basis': 'Much of the tail is near-flat, but the supplied32-mode spectrum includes a larger head. Calling the whole spectrum near-uniform needs qualification.'},
    ],
    60: [
        {'quote': 'high head share (86.8%)', 'assessment': 'value supported', 'basis': 'Current top-eight sensory head share is86.8085186%, correctly rounded to86.8%.'},
        {'quote': 'suggests a significant focus on spatial information', 'assessment': 'not established', 'basis': 'No spatial interpretation of modes, input semantics, or spatial task is supplied. Spectral head share alone does not establish a spatial focus.'},
        {'quote': 'relatively low RMS', 'assessment': 'unsupported comparative description', 'basis': 'Current RMS0.79972495 is much larger than the0.226 quoted in retained prior memory; prompt also supplies changeL2=4.63319480. No low threshold is stated.'},
        {'quote': 'shifts in the eigenvector distribution', 'assessment': 'not observable from supplied evidence', 'basis': 'The prompt supplies recurrent coordinates and sensory eigenvalues, not eigenvectors.'},
        {'quote': 'consistent eigenvalue values; this uniformity', 'assessment': 'overgeneralized', 'basis': 'Near-equal tail values coexist with a strongly unequal spectrum from27.40278727 to0.01804322; whole-spectrum uniformity is not supported.'},
    ],
    90: [
        {'quote': 'Journal Entry - Observation 61', 'assessment': 'incorrect current observation label', 'basis': 'Actual current global step90;61 is the previous journal first-application boundary in the prompt. That resemblance suggests possible confusion but does not prove why the model wrote it.'},
        {'quote': 'high head share (86.8%)', 'assessment': 'stale numeric value', 'basis': 'Current head share85.5418859%;86.8% matches the prior step60 journal supplied in memory.'},
        {'quote': 'dominant sensory mode (eigenvalue 27.05)', 'assessment': 'value supported', 'basis': 'Current27.04911222 rounds to27.05.'},
        {'quote': 'RMS remains relatively low (0.83)', 'assessment': 'value supported; stability inference not established', 'basis': 'Current RMS0.82976032 rounds to0.83. A similar norm is not evidence of an unchanged state; current changeL2=2.24745510.'},
        {'quote': 'consistent eigenvalue values across all 32 modes', 'assessment': 'contradicted as a whole-spectrum claim', 'basis': 'Current top mode27.04911222 and smallest mode0.01552410 are strongly unequal. Repeated tail values do not make all32 modes consistent with one another.'},
        {'quote': 'reduced active-mode fill percent (12.35%)', 'assessment': 'value supported', 'basis': 'Current12.34829247% rounds to12.35%.'},
        {'quote': 'changes in the eigenvector distribution', 'assessment': 'not observable from supplied evidence', 'basis': 'No eigenvectors are supplied.'},
    ],
    120: [
        {'quote': 'Journal Entry - Observation 61', 'assessment': 'incorrect current observation label', 'basis': 'Actual current global step120; the same mistaken heading appears in supplied prior memory.'},
        {'quote': 'dominant sensory mode (27.09)', 'assessment': 'value supported', 'basis': 'Current27.09103048 rounds to27.09.'},
        {'quote': 'high head share (86%)', 'assessment': 'value supported at coarse precision', 'basis': 'Current85.6189676% rounds to86% at whole-percent precision; this is not the earlier stale86.8% error.'},
        {'quote': 'RMS of 0.83', 'assessment': 'stale or inaccurate at stated precision', 'basis': 'Current RMS0.82242177 rounds to0.82 to two decimals;0.83 is the value written in prior step90 memory.'},
        {'quote': 'remarkably consistent eigenvalue distribution across all 32 modes', 'assessment': 'misleading or unresolved interpretation', 'basis': 'If this means equality across modes, current27.09103048 versus0.01335669 contradicts it. If temporal shape stability was intended, that different claim needs an explicit comparison; the sentence does not distinguish it.'},
        {'quote': 'reduced active-mode fill (17.32%)', 'assessment': 'value supported', 'basis': 'Current17.31500249% rounds to17.32%.'},
        {'quote': 'plateau in learning or a deliberate suppression of dynamic responses', 'assessment': 'not established', 'basis': 'No learning measure, controlled causal comparison or evidence of deliberate suppression is supplied. Prompt explicitly says the text codec is not a learned embedding and writing does not train model or reservoir weights.'},
    ],
}


def main():
    receipt = read(OUT / 'receipt.json')
    assert receipt['status'] == 'passed' and receipt['originalUnchanged']
    material = read(OUT / 'quality-review-material.json')
    assert [j['identity']['observedStep'] for j in material['journals']] == [30, 60, 90, 120]
    rows = []
    for j in material['journals']:
        obs = j['observation']; sensory = obs['sensory']; step = obs['step']
        assert all(a['quote'] in j['journalText'] for a in ANNOTATIONS[step])
        rows.append({'identity': j['identity'], 'readability': 'Readable paragraph(s), ending in a complete sentence; no visibly cut-off ending.',
                     'presentation': 'Assistant-preface/quoted prose or Markdown headings remain exact, inert saved text; not cleaned or rewritten.',
                     'measurementBasis': {'rms': obs['rms'], 'l2': obs['l2'], 'previousObservationStep': obs['previousObservationStep'], 'changeL2': obs['changeL2'],
                                          'sensoryTopEigenvalue': sensory['eigenvalues'][0], 'sensorySmallestEigenvalue': sensory['eigenvalues'][-1], 'sensoryHeadToSmallestRatio': sensory['eigenvalues'][0] / sensory['eigenvalues'][-1],
                                          'sensoryEntropyTopEight': sensory['entropy'], 'sensoryHeadSharePercentTopEight': sensory['headShare'] * 100, 'reducedActiveModeFillPercent': sensory['fillPercent']},
                     'annotations': ANNOTATIONS[step]})
    names = ['owned-model-server-start.json', 'real-model-created.json', 'real-model-reading-first.json', 'real-model-minimized.json', 'real-model-before-restore.json', 'real-model-service-stop-request.json', 'owned-model-cleanup-supplement-01.json', 'qualification.json', 'source-before-build-final.json']
    result = {'schema': 'reservoir-real-model-prose-close-reading-v1', 'reviewedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'All4 retained journals from one bounded actual Gemma3:4b session, judged against their current exact app-retained prompt/observation and prior supplied memory. Exploratory close reading, not a blinded benchmark or automated quality score.',
              'reviewer': 'Codex app_parity_inventory; independent read-only core-agent cross-check also read all4 texts/observations and confirmed main contrary evidence.',
              'modelsContactedByReview': False, 'script': {'path': str(Path(__file__)), 'sha256': sha(Path(__file__))},
              'inputReceipt': {'path': str(OUT / 'receipt.json'), 'sha256': sha(OUT / 'receipt.json')}, 'material': {'path': str(OUT / 'quality-review-material.json'), 'sha256': sha(OUT / 'quality-review-material.json')},
              'contextReceipts': {name: {'path': str(V / name), 'sha256': sha(V / name)} for name in names},
              'journals': rows, 'mechanicalResult': '4 complete replies,4 exact saves,4 unique next-step applications,3 exact latest-applied full-text memory links; pinned whole-bundle replay passed.',
              'proseResult': 'Readable and mechanically complete, with several correct measurements, but repeated stale/incorrect labels and numeric values plus unsupported spectral, spatial, stability and learning interpretations.',
              'memoryResult': 'Exact prior text is supplied. Repeated errors are consistent with carried prose influencing later wording, but no no-memory comparison establishes that causal effect or comprehension.',
              'limits': ['One finite episode;4 dependent journal entries are not4 independent replications.', 'No independent wire request/response log for owned Ollama; app-retained request and timing evidence only.', 'No model-weight training, causal benefit, consciousness, intent, power-loss durability or long-run real-model reliability result.', 'Cleanup supplement records original supervisor EPERM plus later exact-process/group absence, not an error-free original cleanup.']}
    with (V / 'real-model-prose-review.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps({'receipt': str(V / 'real-model-prose-review.json'), 'journalsReviewed': len(rows), 'annotations': sum(len(r['annotations']) for r in rows), 'inputIntegrityPassed': True}))


if __name__ == '__main__':
    main()
