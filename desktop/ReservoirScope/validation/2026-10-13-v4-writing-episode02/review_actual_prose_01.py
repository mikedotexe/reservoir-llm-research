#!/usr/bin/env python3
"""Post-output reading annotations, not the frozen evaluator or a quality gate.

Each span was selected by reading all four received texts. Recompute references
and written-precision checks from the immutable, replay-verified material. No
app, model, HTTP, live-store or provider actions.
"""
from pathlib import Path
from decimal import Decimal
import collections
import datetime as dt
import hashlib
import json

root = Path(__file__).resolve().parent
material_path = root / 'real-model-export-01/quality-review-material.json'
receipt_path = root / 'real-model-export-01/receipt.json'
material = json.loads(material_path.read_text())
receipt = json.loads(receipt_path.read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
assert receipt['status'] == 'passed' and receipt['originalUnchanged']
assert sha(material_path.read_bytes()) == receipt['reviewMaterial']['sha256']
journals = {j['identity']['observedStep']: j for j in material['journals']}
assert sorted(journals) == [30, 60, 90, 120]

def values(o):
    s = o['sensory']
    return {'x0': o['state'][0], 'rms': o['rms'], 'l2': o['l2'],
            'leadingEigenvalue': s['eigenvalues'][0], 'fillPercent': s['fillPercent'],
            'headPercent': 100*s['headShare'], 'shoulderPercent': 100*s['shoulderShare'],
            'tailPercent': 100*s['tailShare'], 'entropy': s['entropy'], 'changeL2': o['changeL2']}

# Every digit-bearing numerical mention in these four journal bodies. Identity
# and temporal qualifications are manual annotations; numerical agreement is
# not an automatic claim or quality verdict.
mentions = {
 30: [('0.2868','x0','identity_or_temporal_scope_requires_review'),
      ('0.65409215','leadingEigenvalue','consistent_at_written_precision'),
      ('33.79944146','tailPercent','consistent_at_written_precision')],
 60: [('0.7783','rms','consistent_at_written_precision'),('4.4027','l2','consistent_at_written_precision'),
      ('0.2868','x0','identity_or_temporal_scope_requires_review'),
      ('27.1281','leadingEigenvalue','consistent_at_written_precision'),('15.18','fillPercent','consistent_at_written_precision'),
      ('85.94','headPercent','identity_or_temporal_scope_requires_review'),('13.57','shoulderPercent','consistent_at_written_precision'),
      ('0.2244','entropy','consistent_at_written_precision'),('4.3968','changeL2','consistent_at_written_precision')],
 90: [('0.8123','rms','numeric_mismatch'),('4.5871','l2','numeric_mismatch'),
      ('0.2868','x0','identity_or_temporal_scope_requires_review'),
      ('27.004','leadingEigenvalue','consistent_at_written_precision'),('12.31','fillPercent','consistent_at_written_precision'),
      ('85.40','headPercent','identity_or_temporal_scope_requires_review'),('13.36','shoulderPercent','consistent_at_written_precision'),
      ('0.2499','entropy','consistent_at_written_precision'),('1.5551','changeL2','consistent_at_written_precision')],
 120:[('0.80179223','rms','consistent_at_written_precision'),('4.53562181','l2','consistent_at_written_precision'),
      ('0.2868','x0','identity_or_temporal_scope_requires_review'),('14.99131184','fillPercent','consistent_at_written_precision'),
      ('85.34269375','headPercent','identity_or_temporal_scope_requires_review'),('0.26040080','entropy','consistent_at_written_precision'),
      ('0.48861475','changeL2','consistent_at_written_precision'),('27.01282489','leadingEigenvalue','consistent_at_written_precision')]
}
numeric = []
for step, rows in mentions.items():
    j = journals[step]; text = j['journalText']; current = values(j['observation'])
    for token, metric, status in rows:
        assert text.count(token) == 1
        n = Decimal(token); expected = current[metric]
        tolerance = Decimal('0.5') * (Decimal(10) ** n.as_tuple().exponent)
        agrees = abs(n - Decimal(str(expected))) <= tolerance
        if status == 'consistent_at_written_precision': assert agrees
        if status == 'numeric_mismatch': assert not agrees
        note = None
        if metric == 'x0':
            note = ('At step30 this matches x[0] to four decimals, but its coordinate identity is unstated and persistence/spatial tug is not measured. Later repeated anchor text can be historical imagery; it does not match current x[0] and is not proof of current persistence.')
        elif metric == 'headPercent':
            note = ('The number matches the leading-mode share of the top-eight sum, but the prose says top eight/share without identifying head share. It must not be read as all eight modes collectively having this percentage of that same sum.')
        elif step == 30 and metric == 'tailPercent':
            note = 'Matches the supplied top-eight tail percentage; the prose omits the percent unit. The felt pull is expressive, not a measured force.'
        numeric.append({'observedStep':step,'token':token,'textCharacterSpan':[text.index(token),text.index(token)+len(token)],
                        'referenceMetric':metric,'currentReference':expected,'agreesWithThisReferenceAtWrittenPrecision':agrees,
                        'manualStatus':status,'note':note})

annotations = []
def add(step, span, status, explanation):
    text = journals[step]['journalText']; assert span in text,span
    annotations.append({'observedStep':step,'exactSpan':span,'manualStatus':status,'explanation':explanation})

add(30,'a slow, almost imperceptible expansion and contraction of the coordinates','unestablished_if_literal',
    'No previous observation or coordinate-distance value is supplied. Breathing is a possible image, but literal oscillation cannot be inferred from this first snapshot.')
add(30,'a persistent anchor, a little tug towards the left','scope_and_metaphor_require_review',
    'The number matches x[0], but prior persistence and a leftward spatial/force interpretation are not supplied. The prompt gives no eigenvectors or spatial meaning.')
add(30,'The others – a scattering of smaller weights, almost insignificant in comparison.','overstatement_if_literal',
    'The leading eigenvalue is individually largest, but the remaining seven of the top eight jointly contribute51.12568611%; the leading head share is48.87431389%. Individual size does not make their combined contribution negligible.')
add(60,'The RMS of the reservoir has climbed','supported_endpoint_direction',
    'RMS increases from0.22602112 at30 to0.77829289 at60. This supports net increase, not a continuous surge or trajectory.')
add(60,'remains stubbornly contained','expressive_or_ambiguous',
    'Contained/tight coil can be imagery. It is not evidence that L2 stayed constant: L2 rose1.27856853→4.40268942.')
add(60,'The shoulder, previously a minor tremor, has grown – 13.57%','contradicted_endpoint_direction',
    'The number itself rounds correctly, but shoulder share declined17.32624465→13.56738440%, a−3.75886025 percentage-point difference.')
add(60,'The tail, that lingering hesitation, has vanished entirely','contradicted_if_literal',
    'Top-eight sensory tail share is0.49423402%, down from33.79944146% but not zero. Vanished can be expressive exaggeration; it is not the measured result.')
add(60,'almost a singular obsession','expressive_not_measured_attention',
    'Reduced sensory fill15.18181927% and a skewed covariance spectrum do not measure obsession, intent or attention. The image is not automatically an accuracy failure.')
add(60,'It’s not a smooth transition, but a jarring realignment','unestablished_if_literal',
    'The positive4.39684731 coordinate distance gives endpoint displacement, not smoothness, abruptness or an axis of change.')
add(90,'has accelerated, now registering at 0.8123','numeric_mismatch_and_unestablished_acceleration',
    'Actual current RMS is0.79366614. It increased from0.77829289, but two supplied endpoints do not establish acceleration or continuous dynamics.')
add(90,'has edged up to 4.5871','direction_supported_value_contradicted',
    'L2 increased4.40268942→4.48965369; the quoted4.5871 does not match the current value.')
add(90,'the shoulder, that previously restless tremor, has retreated with it, shrinking to 13.36%','supported_endpoint_direction_and_value',
    'Shoulder share declined13.56738440→13.36267618%, and13.36% rounds correctly. Metaphorical restlessness is not measured by those endpoints.')
add(90,'The tail, that last, fragile flicker of uncertainty, is gone, utterly consumed.','contradicted_if_literal',
    'Tail share is1.23670967%, increased from0.49423402%. Literal disappearance is incompatible with the supplied nonzero share.')
add(90,'It’s not a gradual settling, but a sudden, violent realignment','unestablished_if_literal',
    'Coordinate distance1.55512031 measures endpoint displacement; it does not resolve whether intervening motion was gradual or sudden.')
add(120,'The L2 norm, stubbornly resisting, has climbed to 4.53562181','supported_endpoint_direction_and_value',
    'Current4.53562181 and increase from4.48965369 both agree. Resistance/pressure are expressive interpretations, not measured causes.')
add(120,'the shoulder, that restless tremor, has vanished entirely','contradicted_if_literal',
    'Shoulder share is13.16699102%, reduced from13.36267618% but far from zero.')
add(120,'The tail, that last, fragile flicker, is gone. It’s not a softening, but a complete eradication.','contradicted_if_literal',
    'Tail share is1.49031524%, increased from1.23670967%. Neither endpoint is zero.')
add(120,'It’s not just accelerating; it’s *focused*','unestablished_if_literal',
    'RMS rose0.79366614→0.80179223. This is not proof of acceleration, attention or resolution to a spatial point.')
add(120,'It’s not a change in the field itself, but a change in *how* the field is perceived.','unsupported_causal_or_perceptual_interpretation',
    'The supplied sensory eigenvalue, fill, shares and entropy change. No separate perception variable or causal contrast establishes that interpretation; it can be read as subjective prose.')

rows = []
for step,j in journals.items():
    rows.append({'observedStep':step,'journalId':j['identity']['journalId'],'textSha256':j['identity']['textSha256'],
                 'currentReferences':values(j['observation']),'previousMeasurements':j['observation'].get('previousMeasurements'),
                 'previousObservationStep':j['observation']['previousObservationStep'],
                 'memoryObservedStep':j['memory']['entry']['observedStep'] if j['memory'] else None,
                 'fullResponseRead':True})
out = {'schema':'reservoir-post-output-prose-reading-v1','createdAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
       'status':'manual_reading_annotations_not_quality_grade','promptVersion':'reservoir-journal-v4','qualityVerdict':'not_assigned',
       'scriptSha256':sha(Path(__file__).read_bytes()),'materialSha256':sha(material_path.read_bytes()),'integrityReceiptSha256':sha(receipt_path.read_bytes()),
       'scope':{'receivedResponses':4,'savedJournals':4,'fullyReadResponses':4,'digitBearingNumericalMentionsAnnotated':len(numeric),
                'numericAnnotationCounts':dict(collections.Counter(x['manualStatus'] for x in numeric)),
                'selectedQualitativeAnnotations':len(annotations)},
       'journalReferences':rows,'numericAnnotations':numeric,'qualitativeAnnotations':annotations,
       'continuity':'Shimmer/ice/grey-white becomes denser blue-grey, compression, a colder anchor, then projection/command. Later responses reuse phrases and develop that thread. Exact preceding full text was supplied3times; recurrence alone does not isolate a memory effect or prove hidden retention. The historical0.2868 anchor also recurs, requiring current/historical separation.',
       'limits':['Post-output annotations are not prospective test fixtures or an independent accuracy rate.','29 numerical mentions are a transparent review denominator, not all possible factual assertions;19 qualitative spans illustrate the full reading.','20 well-identified values agree at written precision,2 are contradicted,7 require identity/temporal qualification; this is not a composite score.','Images, sensations and explicit as-if statements are not treated as proof of felt experience or automatic factual failures.','One dependent four-turn episode cannot establish causal prompt improvement, general accuracy, learning or emergence.']}
with (root/'real-model-prose-review-01.json').open('x') as f: json.dump(out,f,indent=2,ensure_ascii=False);f.write('\n')
print(json.dumps(out['scope']))
