#!/usr/bin/env python3
"""Post-output, manually authored reading; reproduces source bindings and excerpt anchors.
Does not contact a model, run an app, or determine a creative/scientific score.
All writes are exclusive new files in this validation directory.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text())

def source(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}

def write(name, data):
    with (ROOT / name).open('x', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')

receipt_path = ROOT / 'real-model-export-01/receipt.json'
material_path = ROOT / 'real-model-export-01/quality-review-material.json'
r = read(receipt_path)
m = read(material_path)
assert r['status'] == 'passed' and r['originalUnchanged']
assert source(material_path)['sha256'] == r['reviewMaterial']['sha256']
assert r['checker']['sha256'] == 'f80c81be84e1b68ccc1f3814994809728ad417df3db2b89279873962bb3f32e0'
assert source(ROOT / 'run-plan.json')['sha256'] == 'babd5b411f2a08fa4ddcbce48d25018a963d6d15900f2ec08d5359403f90c131'
assert source(ROOT / 'evaluation-freeze-01.json')['sha256'] == '4452db458d2e79bc4ab4c48e66407e93e4d4f7088cc5d6ed2624d5c9e28cea85'
js = m['journals']
assert [j['identity']['observedStep'] for j in js] == [30, 60, 90, 120]
by_step = {j['identity']['observedStep']: j for j in js}
ui = read(ROOT / 'native-export-01.json')
assert {f['path']: {'bytes': f['bytes'], 'sha256': f['sha256']} for f in ui['files']} == r['inventoryBefore']

# These judgments were authored only after reading all four full texts/prompts.
raw_annotations = {
30: [
 ('The RMS is still clinging to that 0.226', 'numeric_supported_temporal_unestablished', 'RMS 0.226 agrees with current 0.22602112 at written precision. Still/clinging suggests persistence, but this is the first supplied observation and prior text/change L2 are unavailable.'),
 ('0.654, a clear, unwavering tone', 'numeric_supported_metaphor_or_unestablished_frequency', '0.654 agrees with current leading sensory eigenvalue 0.65409215. Tone can be imagery; a frequency or unwavering temporal mode was not measured.'),
 ('Ninety-four percent.', 'numeric_supported_scope_not_attention', '94% agrees with reduced sensory fill 94.31040364% at whole-percent precision. It does not measure attention to one point.'),
 ('the active-mode fill suggests a significant portion of the system is focused on that single point', 'unsupported_literal_mapping', 'The separate sensory active-mode estimator is not recurrent activity, spatial concentration or attention. The top-eight head share is 48.87431389%; no eigenvectors/spatial mapping are supplied.'),
 ('a subtle oscillation in the tail node coordinates', 'unestablished_temporal_and_scope_claim', 'No prior observed state or trajectory was supplied at the first observation. The sensory tail share is not a region of recurrent nodes.'),
 ('The shoulder share is growing', 'unestablished_temporal_claim', 'A single supplied share, 17.32624465%, cannot establish growth.'),
 ('It’s actively *seeking* something.', 'expressive_personification_not_measured_intent', 'This completes an imaginative anticipation/pressure thread. No goal-seeking, learning, equilibrium test or independent cognitive result follows from this phrasing.'),
],
60: [
 ('remains at 0.7918', 'numeric_supported_continuity_wording_misleading', '0.7918 agrees with current RMS 0.79182555. The earlier available prose says 0.226, so remains cannot literally mean unchanged between the supplied observations.'),
 ('single, unwavering tone – 0.654', 'stale_numeric_claim_if_sensory_leading_mode', 'The current leading sensory eigenvalue is 27.48050683, not 0.654. That exact old number is in the supplied previous journal and the first observation. This documents carry-over, not a causal isolation of memory contamination.'),
 ('just 15.18%', 'numeric_supported', '15.18% agrees with current reduced sensory fill 15.18181927%.'),
 ('The shoulder share is creeping', 'direction_contradicted_if_share_growth', 'The current shoulder share is 12.45650496%, down from the preceding recorded 17.32624465%. Prior prose also asserted growth without evidence. Interpreting creeping/expansion as literal growth conflicts with the two observations.'),
 ('Each spark holds its position', 'unestablished_trajectory_or_metaphor', 'Only the current coordinates and aggregate change L2 4.55825418 were supplied; no within-interval trajectory, crystalline geometry or fixed-position test was given.'),
 ('It’s as if the system is deliberately suppressing other voices', 'explicit_simile_not_verified_attention', 'As if marks an imaginative comparison. It need not assert an actual controller intention, but selective attention or deliberate suppression is not established by the fill value.'),
 ('The reservoir isn’t seeking; it’s *holding*.', 'thematic_revision', 'This explicitly revises the prior entry’s seeking/anticipation into holding/stillness while continuing its hum, pressure, tail and shoulder motifs. It is development of the supplied prose, not evidence of learning.'),
],
90: [
 ('The RMS, now 0.8114', 'numeric_supported', '0.8114 agrees with current RMS 0.81142359.'),
 ('The tone itself—0.654—remains the anchor', 'stale_numeric_claim_if_sensory_leading_mode', 'The current leading sensory eigenvalue is 27.50731104. The previous journal again contains 0.654, which matches the first observation instead. A purely fictional tone is possible, but the original sensory-measurement referent is misleading if read as current.'),
 ('at 12.28%', 'numeric_supported', '12.28% agrees with current reduced sensory fill 12.28402894%.'),
 ('The shoulder share is expanding', 'direction_contradicted_if_literal', 'Current share 12.01713533% is below preceding 12.45650496%; the direction is the reverse of expansion.'),
 ('geometry that resembles polished obsidian', 'expressive_image', 'Obsidian/facets, fern/unfurling and a sculpted void are expressive images. No eigenvector or spatial geometry was supplied, so these are not an inferred physical map.'),
 ('The reservoir isn’t seeking resolution, it’s simply… holding.', 'continuity_with_repetition', 'Continues the immediately supplied holding thread, with honey becoming obsidian and accumulated potential; much of the tail/shoulder/head structure repeats. No independent memory retention beyond supplied context is shown.'),
],
120: [
 ('The RMS, now 0.798', 'numeric_mismatch', 'Current RMS is 0.80572259, which rounds to 0.806 at three decimals, not 0.798. Its source is not established; it is not the immediately prior recorded RMS 0.81142359.'),
 ('The tone—0.661—remains the fixed point', 'numeric_mismatch_if_sensory_leading_mode', 'Current leading sensory eigenvalue is 27.58387107, not 0.661. No measured frequency or source for 0.661 is established.'),
 ('at 12.19%', 'numeric_mismatch', 'Current reduced sensory fill is 12.27918001%, which rounds to 12.28%, not 12.19%.'),
 ('The shoulder share is increasing', 'direction_contradicted_if_literal', 'Current shoulder share 11.60222534% is below preceding 12.01713533%; the retained sequence has fallen at all three later observations.'),
 ('like a nautilus shell emerging from the depths', 'expressive_image_not_spatial_result', 'An explicit simile develops the previous fern/unfurling image. It does not need to be treated as a literal measured spiral; no spatial coordinates or eigenvectors are provided for that mapping.'),
 ('Almost as if the system remembers a time before the tone', 'speculative_image_not_memory_receipt', 'Almost as if frames an imaginative ancient/prehistory motif. The exact available full-text memory is only the previous saved-and-applied journal at step90; this is not evidence of another stored history.'),
 ('The obsidian deepened.', 'continuity_with_elaboration', 'Directly picks up the previous obsidian image, then changes holding into containing and adds ancient memory imagery. It continues a thread without returning to a user question or imposed report form.'),
]}
annotations = []
for step, rows in raw_annotations.items():
    j = by_step[step]
    text = j['journalText']
    for quote, decision, reason in rows:
        assert text.count(quote) == 1, (step, quote)
        start = text.index(quote)
        annotations.append({'observedStep': step, 'journalId': j['identity']['journalId'], 'textSha256': j['identity']['textSha256'], 'excerpt': quote, 'unicodeSpan': [start, start + len(quote)], 'manualDecision': decision, 'reason': reason})

old_path = BASE / '2026-10-13-grounding-0.13.0/native-export-review-01/receipt.json'
old = read(old_path)
assert old['status'] == 'passed' and old['originalUnchanged']
op = old['evidence']['finalCorePhase']['value']['pending']
ot = old['evidence']['receivedResponses'][0]['response']['text']
first = js[0]
comparison = {
 'schema': 'reservoir-initial-open-writing-comparison-v1', 'createdAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
 'scope': 'Post-output descriptive comparison of preserved first attempts; not a randomized or single-variable effect estimate.',
 'oldReceipt': source(old_path), 'newReceipt': source(receipt_path),
 'firstPromptBytesIdentical': op['prompt'].encode() == first['exactPrompt'].encode(),
 'firstPromptSha256': sha(first['exactPrompt'].encode()), 'firstPromptUtf8Bytes': len(first['exactPrompt'].encode()),
 'firstObservationExactlyEqual': op['observation'] == first['observation'],
 'oldResponse': old['evidence']['receivedResponses'][0],
 'newFirstJournalIdentity': first['identity'],
 'oldResponseIsExactUtf8PrefixOfNew': first['journalText'].encode().startswith(ot.encode()),
 'oldResponseUtf8Bytes': len(ot.encode()), 'newResponseUtf8Bytes': len(first['journalText'].encode()),
 'additionalUtf8Bytes': len(first['journalText'].encode()) - len(ot.encode()),
 'oldConfiguration': old['evidence']['manifest']['config'], 'newConfiguration': r['evidence']['manifest']['config'],
 'limits': ['Old omitted output/deadline mean256/60; new explicit1024/180, context4096→8192 and total duration600→900 also changed.', 'The exact common prefix and completion under the larger cap support room for this particular continuation, not a general completion-rate or quality benefit.', 'Later numerical observations diverge after applied writing; no paired late-state counterfactual is claimed.']}
assert comparison['firstPromptBytesIdentical'] and comparison['firstObservationExactlyEqual'] and comparison['oldResponseIsExactUtf8PrefixOfNew']
write('initial-response-comparison-01.json', comparison)

measurements = []
for j in js:
    o = j['observation']; s = o['sensory']
    measurements.append({'observedStep': o['step'], 'rms': o['rms'], 'leadingSensoryEigenvalue': s['eigenvalues'][0], 'reducedSensoryFillPercent': s['fillPercent'], 'topEightSensoryEntropy': s['entropy'], 'headPercent': s['headShare'] * 100, 'shoulderPercent': s['shoulderShare'] * 100, 'tailPercent': s['tailShare'] * 100, 'previousObservationStep': o['previousObservationStep'], 'stateChangeL2': o['changeL2']})
manual = {
 'schema': 'reservoir-manual-open-writing-review-v1', 'createdAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
 'status': 'All four complete received texts and their exact supplied prompts/observations read; no creative/scientific composite verdict.',
 'authorship': 'Post-output agent interpretation; exact anchors validated by this script. Not a predeclared prediction or automatic evaluator judgment.',
 'material': source(material_path), 'integrityReceipt': source(receipt_path), 'qualityCandidateReport': source(ROOT / 'real-model-quality-review-01.json'),
 'protocol': source(ROOT / 'run-plan.json'), 'prospectiveFreeze': source(ROOT / 'evaluation-freeze-01.json'), 'script': source(Path(__file__).resolve()),
 'modelsContacted': False, 'reviewedJournalCount': len(js), 'reviewedReceivedResponseCount': len(r['evidence']['receivedResponses']),
 'measurements': measurements, 'annotations': annotations,
 'continuity': 'The supplied full-text chain develops hum/pressure/anticipation into honey/holding and then obsidian/containing/ancient imagery. This is readable thematic continuation and some revision, alongside repeated scaffold and carried factual errors. Contextual use is evidenced; hidden memory, emergence, goal-directed autonomy and causal benefit are not established.',
 'factualScope': 'Only voluntary literal measurement/trajectory claims are evaluated. Metaphor, subjective expression, questions and creative choices require no metric, heading, length or assigned topic. Ambiguous literal/metaphorical scope is retained explicitly.',
 'candidateExtractorLimit': 'Frozen regex harness extracted zero metric claims in each of the four texts, despite voluntary measurements found by full reading. No match is not absence or correctness; this known incompleteness was not repaired after seeing outputs.',
 'contextLimit': 'Exact full text is saved/read back and decoded in each subsequent prompt. Configured8192tokens is not tokenizer/full-processing proof; provider prompt_eval_count unavailable.',
}
write('real-model-prose-review-01.json', manual)
outcome = {
 'schema': 'reservoir-writing-room-outcome-v1', 'createdAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
 'scope': 'New actual native0.14 immutable export, mechanically replayed offline and all four texts manually read.',
 'protocol': source(ROOT / 'run-plan.json'), 'prospectiveFreeze': source(ROOT / 'evaluation-freeze-01.json'), 'integrityReceipt': source(receipt_path), 'manualReview': source(ROOT / 'real-model-prose-review-01.json'), 'initialComparison': source(ROOT / 'initial-response-comparison-01.json'), 'nativeExportReceipt': source(ROOT / 'native-export-01.json'), 'beforeStartBinding': source(ROOT / 'real-model-bound-before-start.json'),
 'nativeInventoryExactlyMatchesChecker': True, 'originalUnchanged': True, 'exportFileCount': len(r['inventoryBefore']),
 'manifestSha256': r['inventoryBefore']['manifest.json']['sha256'], 'checkpointSha256': r['evidence']['manifest']['checkpointSha256'],
 'packageExecutableSha256': r['pinnedExecutable']['sha256'], 'sessionId': r['evidence']['manifest']['sessionId'],
 'mechanics': {'step':121,'savedJournals':4,'appliedJournals':4,'attempts':4,'turns':4,'memoryConfirmations':3,'segments':19,'unstartedPlannedOpportunities':0,'noRetriesOrSkips':r['rehearsal']['noRetriesOrSkips'],'eventCounts':r['evidence']['eventCounts'],'finalManifestPhase':r['evidence']['manifest']['phase'],'finalCorePhase':r['evidence']['finalCorePhase'],'elapsedMillis':r['evidence']['manifest']['elapsedMillis']},
 'journals': r['evidence']['journals'], 'verification':r['verification'],
 'scientificAndCreativeVerdict': 'Not assigned. Mechanical completion is established for this run; all-text interpretation and explicit factual mismatches are separate.',
 'modelContactByThisReview':False,
 'limits':['One four-attempt run, not a causal comparison or general reliability estimate.','No independent raw HTTP provider receipt or authenticated full-context-processing evidence.','Verifier resource measurements concern only its offline process.','Native UI lifecycle/service cleanup belong to parent-owned receipts, not to this offline script.']}
write('real-model-outcome-01.json', outcome)
print(json.dumps({'status':'written','annotations':len(annotations),'journals':4,'initialPromptIdentical':True,'initialPartialExactPrefix':True,'outcome':source(ROOT/'real-model-outcome-01.json')},indent=2))
