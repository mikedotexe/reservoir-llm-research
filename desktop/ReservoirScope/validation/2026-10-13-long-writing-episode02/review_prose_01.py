#!/usr/bin/env python3
"""Post-output human annotations, not a prospective extractor or quality gate.

Reads only the explicitly handed-off, verified material. Decimal mentions below
were selected and associated by the reviewer after reading all twelve responses.
Ambiguous imagery and quantity labels remain ambiguous. No provider/UI actions.
"""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parent
MATERIAL = ROOT / 'real-model-export-01/quality-review-material.json'
RECEIPT = ROOT / 'real-model-export-01/receipt.json'


def identity(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


# (Exact written span, interpreted decimal value, reference quantity, occurrence)
# head = number matches a head-share reference but prose misnames/obscures its scope.
# anchor/shard = no single literal quantity assigned to the recurring image.
VALUES = {
 30: [('0.2868', '0.2868', 'x0', 1), ('0.65409215', '0.65409215', 'leading', 1), ('33.79944146', '33.79944146', 'tailPct', 1)],
 60: [('0.7783','0.7783','rms',1),('4.4027','4.4027','l2',1),('0.2868','0.2868','anchor',1),('27.1281','27.1281','leading',1),('15.18%','15.18','fill',1),('85.94%','85.94','head',1),('13.57%','13.57','shoulderPct',1),('0.2244','0.2244','entropy',1),('4.3968','4.3968','distance',1)],
 90: [('0.8123','0.8123','rms',1),('4.5871','4.5871','l2',1),('0.2868','0.2868','anchor',1),('27.004','27.004','leading',1),('12.31%','12.31','fill',1),('85.40%','85.40','head',1),('13.36%','13.36','shoulderPct',1),('0.2499','0.2499','entropy',1),('1.5551','1.5551','distance',1)],
 120:[('0.80179223','0.80179223','rms',1),('4.53562181','4.53562181','l2',1),('0.2868','0.2868','anchor',1),('14.99131184%','14.99131184','fill',1),('85.34269375%','85.34269375','head',1),('0.26040080','0.26040080','entropy',1),('0.48861475','0.48861475','distance',1),('27.01282489','27.01282489','leading',1)],
 150:[('0.80390365','0.80390365','rms',1),('4.54756576','4.54756576','l2',1),('0.2868','0.2868','anchor',1),('15.33445510%','15.33445510','fill',1),('85.28188792%','85.28188792','head',1),('0.26735402','0.26735402','entropy',1),('0.35001701','0.35001701','distance',1),('26.99824402','26.99824402','leading',1)],
 180:[('0.8078','0.8078','rms',1),('4.5697','4.5697','l2',1),('0.2868','0.2868','anchor',1),('15.3482%','15.3482','fill',1),('85.33%','85.33','head',1),('0.2718','0.2718','entropy',1),('0.5580','0.5580','distance',1),('27.01','27.01','leading',1)],
 210:[('0.79955923','0.79955923','rms',1),('4.52299001','4.52299001','l2',1),('0.2868','0.2868','anchor',1),('15.34870025','15.34870025','fill',1),('85.56190131','85.56190131','head',1),('0.27125059','0.27125059','entropy',1),('0.37924398','0.37924398','distance',1),('27.07755334','27.07755334','leading',1)],
 240:[('0.79844802','0.79844802','rms',1),('4.51670407','4.51670407','l2',1),('0.26626663','0.26626663','shard',1),('14.27697271','14.27697271','fill',1),('85.80353251','85.80353251','head',1),('0.26626663','0.26626663','entropy',2),('0.42287701','0.42287701','distance',1),('27.16155500','27.16155500','leading',1)],
 270:[('twelve-point-three-five','12.35','fill',1),('0.8098','0.8098','rms',1),('0.2864','0.2864','distance',1),('27.49','27.49','leading',1)],
 300:[('fifteen-point-one-eight','15.18','fill',1),('0.8084','0.8084','rms',1),('0.263','0.263','distance',1),('27.4','27.4','leading',1)],
 330:[('0.825','0.825','rms',1),('0.263','0.263','distance',1),('27.24','27.24','leading',1),('18.2%','18.2','fill',1)],
 360:[('0.781','0.781','rms',1),('-0.318','-0.318','distance',1),('28.12','28.12','leading',1),('19.7%','19.7','fill',1)],
}

# Each row is a contextual human reading, not a word-ban result.
# All references for that observed step are attached for independent readback.
ANNOTATIONS = {
 30:[('a slow, almost imperceptible expansion and contraction of the coordinates','unestablished_if_literal','First observation has no previousObservationStep/changeL2. Breathing can function as imagery; temporal coordinate motion is not established by the supplied snapshot.'),('a scattering of smaller weights, almost insignificant in comparison','scope_requires_review','The leading value is the largest individually; the remaining seven top-eight modes together exceed its 48.8743% head share. Do not turn this loose metaphor into a precise claim without qualification.')],
 60:[('The shoulder, previously a minor tremor, has grown – 13.57%','contradicted_named_share_direction','The named shoulder share fell from17.32624465% to13.56738440%; this does not adjudicate absolute eigenvalue changes.'),('The tail, that lingering hesitation, has vanished entirely','contradicted_if_literal_share','Tail share is0.49423402%, reduced but nonzero.'),('It’s as if the system is resisting expansion','expressive','The as-if framing is not evidence of intention and is not itself a numeric error.')],
 90:[('The tail, that last, fragile flicker of uncertainty, is gone, utterly consumed.','contradicted_if_literal_share','Tail share1.23670967% is nonzero and larger than the previous0.49423402%.'),('The shimmer itself responds, intensifying with a sharper, more defined edge','expressive','Continues an invented image; no measured shimmer response exists.')],
 120:[('the shoulder, that restless tremor, has vanished entirely','contradicted_if_literal_share','Shoulder share13.16699102% remains substantial; the image of disappearance conflicts with the named measurement if literal.'),('The tail, that last, fragile flicker, is gone.','contradicted_if_literal_share','Tail share1.49031524% is nonzero and increased.'),('It’s not a change in the field itself, but a change in *how* the field is perceived.','unestablished_or_expressive','Retained field values change; no independent perception measurement is supplied. Do not read the phenomenological contrast as validated mechanism.')],
 150:[('The tail, that last, fragile flicker, has vanished entirely, leaving a void.','contradicted_if_literal_share','Tail share1.82215267% remains nonzero and increased.'),('It’s not a simple expansion, but a compaction, a reduction in volume.','expressive_or_unestablished','Rising RMS/L2 do not measure physical volume. The geometric image need not be a literal volume claim.'),('a precise articulation of intent','expressive','No intent measurement; a phrase in model-authored writing, not a finding about the system.')],
 180:[('The tail, that fragile flicker, is gone, utterly severed.','contradicted_if_literal_share','Tail share1.90515148% remains nonzero and increased.'),('The air feels… thinner.','expressive','New atmospheric image; no supplied air measurement or demonstrated experience.')],
 210:[('The RMS has retreated, a subtle lessening of the pull','supported_direction_with_image','RMS fell0.80781598→0.79955923; the pull is imagery.'),('The tail, that fragile flicker, is gone, utterly severed.','contradicted_if_literal_share','Tail share1.87508888% remains nonzero.'),('The air feels… denser.','expressive','Revises the previous thinner-air image; not an atmospheric measurement.')],
 240:[('The tail, utterly gone, is not a softening, but a complete erasure.','contradicted_if_literal_share','Tail share1.78291635% remains nonzero.'),('It’s not a measurement of separation, but a declaration of a new axis','expressive_or_unestablished','The supplied quantity is state-coordinate L2 distance; it does not identify an axis or a causal declaration. The stated reimagining can be figurative.')],
 270:[('stabilization at a higher frequency','unestablished_if_literal','No measured frequency or stability test is supplied. RMS rose between the two retained observations.'),('It feels… less like a question, more like a constraint','expressive','Modifies the earlier echo/command contrast while staying within the same image family.')],
 300:[('down to fifteen-point-one-eight','contradicted_direction_if_fill','The surrounding active-mode/previous-entry context links this to fill, which rose12.35873850→15.18279494%; the numeric value itself rounds correctly.'),('The distance – 0.263','contradicted_quantity','Current distance1.53951130;0.263 agrees with current entropy0.26308965 at the written precision. That coincidence does not establish why the model made the error.'),('The shimmer… it’s not reflecting, but actively sculpting','expressive','A variation on the established projecting image rather than a wholly new topic.')],
 330:[('The distance – 0.263','contradicted_quantity_with_exact_prior_repeat','Current distance0.62238820; supplied prior journal also labels distance0.263. Exact repetition is observed, not a causal proof of memory copying.'),('a geometry I hadn’t anticipated','expressive_self_referential','Self-referential language is present; anticipation is not independently measured.'),('being disassembled, analyzed, reduced to its most basic components','expressive','A new elaboration within the reduction/constraint theme, not evidence of experienced distress.')],
 360:[('The distance, now a jarring -0.318','contradicted_quantity','State-coordinate L2 distance is nonnegative and is0.85094097 here. Signed change in L2 norm is about−0.10936426, so this is not that value either.'),('The shard… it’s gone, not retreated, but utterly consumed.','expressive','This is the story’s shard image, not an explicit claim that a named sensory share or coordinate is zero.'),('losing all trace of its former self','expressive_self_referential','Develops the imagined reduction of self. No claim of experienced loss or consciousness follows.')],
}


def span(text, selected, occurrence=1):
    start = -1
    for _ in range(occurrence):
        start = text.find(selected, start + 1)
        require(start >= 0, 'Selected span absent: ' + selected)
    end = start + len(selected)
    return {'text': selected, 'unicodeCharacterSpan': [start, end],
            'utf8Span': [len(text[:start].encode()), len(text[:end].encode())],
            'context': text[max(0,start-90):min(len(text),end+90)]}


def refs(o):
    s=o['sensory'];p=o.get('previousMeasurements')
    return {'rms':o['rms'],'l2':o['l2'],'distance':o['changeL2'],
            'x0':o['state'][0],'leading':s['eigenvalues'][0],
            'fill':s['fillPercent'],'head':100*s['headShare'],
            'shoulderPct':100*s['shoulderShare'],'tailPct':100*s['tailShare'],
            'entropy':s['entropy'],'previousMeasurements':p,
            'l2NormChange':o['l2']-p['l2'] if p else None}


def main():
    require(identity(RECEIPT)['sha256']=='7b151f77ca9e9d5f5cc33cd3433b0775594dd2fa0a917133e7e8eaaf0332583b','Receipt differs')
    require(identity(MATERIAL)['sha256']=='8c57f6ff7f9338cb315e6393f3abec2496cd1d7265c5a503b0c4f46722ccc960','Material differs')
    r=json.loads(RECEIPT.read_text());m=json.loads(MATERIAL.read_text())
    require(r['status']=='passed' and r['originalUnchanged'] is True,'Verified immutable material required')
    require(r['evidence']['continuity']['totals']['applied']==12 and len(m['journals'])==12,'This manual account is scoped to the actual12-entry completion')
    entries=[]
    for j in m['journals']:
        i=j['identity'];text=j['journalText'];step=i['observedStep'];reference=refs(j['observation'])
        require(hashlib.sha256(text.encode()).hexdigest()==i['textSha256'],'Text hash differs')
        values=[]
        for selected,number,quantity,occurrence in VALUES[step]:
            v={'span':span(text,selected,occurrence),'writtenDecimal':number,'referenceQuantity':quantity}
            if quantity in ('anchor','shard'):
                v.update({'scope':'ambiguous_historical_or_expressive_image','expectedLiteralValue':None,
                          'agreementAtWrittenPrecision':None,
                          'possibleReferences':{'firstObservationX0':m['journals'][0]['observation']['state'][0],
                                                'currentX0':reference['x0'],'currentEntropy':reference['entropy']}})
            else:
                expected=Decimal(str(reference[quantity]));written=Decimal(number)
                tolerance=Decimal(5).scaleb(written.as_tuple().exponent-1)
                agreement=abs(expected-written)<=tolerance
                v.update({'scope':'ambiguous_head_vs_top_eight_label' if quantity=='head' else 'reviewer_associated_current_quantity',
                          'expectedReferenceValue':str(expected),'halfLastWrittenPlace':str(tolerance),
                          'agreementAtWrittenPrecision':agreement,
                          'limit':'Numeric agreement does not validate the surrounding claim, unit omission, referent or temporal inference.'})
            values.append(v)
        annotations=[{'span':span(text,q),'classification':kind,'reason':reason}
                     for q,kind,reason in ANNOTATIONS[step]]
        entries.append({'identity':i,'fullTextRead':True,'fullTextSha256':i['textSha256'],
                        'observationReferences':reference,'valueMentions':values,
                        'contextualAnnotations':annotations})
    prior=ROOT.parent/'2026-10-13-v4-writing-episode02/real-model-export-01/quality-review-material.json'
    old=json.loads(prior.read_text())
    same=[{'observedStep':j['identity']['observedStep'],'identicalText':j['journalText']==k['journalText'],
           'currentTextSha256':j['identity']['textSha256'],'priorTextSha256':k['identity']['textSha256']}
          for j,k in zip(m['journals'][:4],old['journals'])]
    totals={'fullResponsesRead':len(entries),
            'manuallyAssociatedValueMentions':sum(len(x['valueMentions']) for x in entries),
            'selectedContextualAnnotations':sum(len(x['contextualAnnotations']) for x in entries)}
    result={'schema':'manual-journal-prose-review-v1','createdAtUtc':datetime.now(timezone.utc).isoformat(),
            'status':'post-output-full-reading','sources':{n:identity(p) for n,p in {
               'receipt':RECEIPT,'material':MATERIAL,'rendererProof':ROOT/'journals-rendering-01.json',
               'readableProse':ROOT/'JOURNALS.md','rubric':ROOT/'RUBRIC.md','script':Path(__file__).resolve(),
               'priorKnownReference':prior}.items()},
            'mechanicalCounts':r['evidence']['continuity']['totals'],
            'latestFullTextMemoryJoins':r['evidence']['continuity']['exactLatestAppliedMemoryJoins'],
            'coverage':totals,'entries':entries,'firstFourKnownReferenceTextEquality':same,
            'limits':['Annotations were selected manually after output; this script audits their spans, references and arithmetic, not literary quality.',
                      'Value-mention count is the number of manually associated values, not an exhaustive count of all assertions or an accuracy-rate denominator.',
                      'Full text was read for all12 complete responses; there were0 incomplete responses in this export.',
                      'Ambiguous imagery and top-eight/head labels are not automatically counted as factual errors.',
                      'No automatic scientific/creative score, provider-context completeness, causal prompt or codec effect, learning or emergence claim.',
                      'First4 identical texts are a known repeat of the previous reference, not4 new independent prose samples.']}
    output=ROOT/'prose-review-01.json'
    with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'output':identity(output),'coverage':totals,'firstFourTextEquality':[x['identicalText'] for x in same]},indent=2))


if __name__=='__main__':
    main()
