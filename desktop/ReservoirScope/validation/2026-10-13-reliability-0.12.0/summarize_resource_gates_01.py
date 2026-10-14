from pathlib import Path
import collections,datetime,hashlib,json,xml.etree.ElementTree as ET
b=Path('validation/2026-10-13-reliability-0.12.0')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=[json.loads(l) for l in (b/'samples-01.jsonl').read_text().splitlines()]; rows=[r for r in raw if r.get('type')=='sample']; head=raw[0]
phase=json.loads((b/'final-phase-analysis-02.json').read_text()); marks=[json.loads(l) for l in (b/'primary-markers-final-01.jsonl').read_text().splitlines()]
mi=next(m for m in marks if m['phase']=='minimized'); end=next(m for m in marks if m['event']=='before-restore'); start=next(m for m in marks if m['event']=='start-observed'); pause=marks[-1]
lo=(int(mi['monotonicNs'])-int(head['monotonicNs']))/1e9; hi=(int(end['monotonicNs'])-int(head['monotonicNs']))/1e9
sel=[r for r in rows if lo<=r['elapsedSeconds']<=hi]; intervals=[]; i=0
while i<len(sel):
 j=i
 while j+1<len(sel) and sel[j+1]['manifest']['durableStep']==sel[i]['manifest']['durableStep']: j+=1
 lower=sel[i-1]['elapsedSeconds'] if i else lo; upper=sel[j+1]['elapsedSeconds'] if j+1<len(sel) else hi
 intervals.append({'firstEqualSequence':sel[i]['sequence'],'lastEqualSequence':sel[j]['sequence'],'durableStep':sel[i]['manifest']['durableStep'],'bracketingSeconds':upper-lower,'edgeCensored':i==0 or j==len(sel)-1})
 i=j+1
changed=[sel[0]]
for r in sel[1:]:
 if r['manifest']['durableStep']>changed[-1]['manifest']['durableStep']: changed.append(r)
step_gaps=[{'seconds':z['elapsedSeconds']-a['elapsedSeconds'],'fromSequence':a['sequence'],'toSequence':z['sequence'],'fromStep':a['manifest']['durableStep'],'toStep':z['manifest']['durableStep']} for a,z in zip(changed,changed[1:])]
regressions=[]
for a,z in zip(rows,rows[1:]):
 for k in ('durableStep','journalCount','segmentCount','revision'):
  if int(z['manifest'][k])<int(a['manifest'][k]):regressions.append({'sequence':z['sequence'],'field':k})
windows={w['id']:w for w in phase['windows']}; early=windows['prospective-early-minutes10-25']; late=windows['prospective-late-minutes110-125']; comparisons={}
for typ in ('allObservedResources','documentedLoadExcludedResources'):
 a=early[typ]['metrics']; z=late[typ]['metrics']; er=a['rssBytes']['statistics']['median']; lr=z['rssBytes']['statistics']['median']; threshold=max(64*1048576,.25*er)
 comparisons[typ]={'earlyRssMedianBytes':er,'lateRssMedianBytes':lr,'changeBytes':lr-er,'changePercent':(lr-er)/er*100,'investigationIncreaseThresholdBytes':threshold,'rssIncreaseTriggerReached':lr-er>threshold,'earlyThreadMedian':a['threadCount']['statistics']['median'],'lateThreadMedian':z['threadCount']['statistics']['median'],'earlyFdMedian':a['fdCount']['statistics']['median'],'lateFdMedian':z['fdCount']['statistics']['median'],'finalSettledCountTriggerStatus':'incomplete; no samples after operator Pause marker','earlyCpuDurationWeightedMeanPercent':a['cpuIntervalPercent']['durationWeightedMeanPercent'],'lateCpuDurationWeightedMeanPercent':z['cpuIntervalPercent']['durationWeightedMeanPercent']}
ET.parse(b/'final-resources-01.svg')
result={'schema':'reservoir-resource-gates-v1','createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':[{'path':str(p),'sha256':sha(p)} for p in [b/'samples-01.jsonl',b/'primary-markers-final-01.jsonl',b/'final-phase-analysis-02.json',b/'final-load-intervals-02.json',b/'prospective-freeze.json']],
'duration':{'samplerFooterElapsedSeconds':raw[-1]['elapsedSeconds'],'startObservedToPauseObservedSeconds':(int(pause['monotonicNs'])-int(start['monotonicNs']))/1e9,'operatorDeclaredMinimizedConservativeSeconds':(int(end['monotonicNs'])-int(mi['monotonicNs']))/1e9,'sampledMinimizedProgressSpanSeconds':sel[-1]['elapsedSeconds']-sel[0]['elapsedSeconds'],'firstMinimizedSampleUtc':sel[0]['wallUtc'],'lastMinimizedSampleUtc':sel[-1]['wallUtc'],'firstMinimizedDurableStep':sel[0]['manifest']['durableStep'],'lastMinimizedDurableStep':sel[-1]['manifest']['durableStep'],'firstMinimizedJournalCount':sel[0]['manifest']['journalCount'],'lastMinimizedJournalCount':sel[-1]['manifest']['journalCount']},
'coverage':{'sampleCount':len(rows),'sequencesExactly0Through522':[r['sequence'] for r in rows]==list(range(523)),'processMeasurementCount':sum(isinstance(r.get('process'),dict) for r in rows),'manifestMeasurementCount':sum(isinstance(r.get('manifest'),dict) for r in rows),'completeDiskScans':sum(isinstance(r.get('disk'),dict) and r['disk']['complete'] for r in rows),'maxSampleSpacingSeconds':max(z['elapsedSeconds']-a['elapsedSeconds'] for a,z in zip(rows,rows[1:])),'maxSampleMeasurementSeconds':max(r['sampleSeconds'] for r in rows),'manifestMonotonicRegressions':regressions,'minimizedManifestPhaseSamples':dict(collections.Counter(r['manifest']['phase'] for r in sel)),'largestIntervalBetweenObservedDurableIncreases':max(step_gaps,key=lambda v:v['seconds']),'largestConservativeSameDurableRunBracket':max(intervals,key=lambda v:v['bracketingSeconds']),'stallInterpretation':'For each maximal equal-durableStep run, bracket by the previous lower and next higher sampled publication, or the minimized marker at a window edge. This conservatively bounds any unobserved no-increase interval inside this regularly sampled window. It does not prove continuous UI visibility, replay correctness or exact sub-sample scheduling.'},
'comparisonTriggers':comparisons,'otherTriggers':{'maximumObservedRssBytes':phase['base']['metrics']['rssBytes']['maximum'],'observationsAbove512MiB':sum(r['process']['rssBytes']>512*1048576 for r in rows),'maximumIntervalCpuPercent':phase['base']['metrics']['cpuIntervalPercent']['maximum'],'cpuIntervalsAboveOneCore':sum((r['process'].get('cpuIntervalPercent') or 0)>100 for r in rows),'selectedLogicalBudgetBytes':268435456,'maximumScannedLogicalBytes':phase['base']['metrics']['logicalBytes']['maximum'],'maximumScannedBudgetPercent':phase['base']['metrics']['logicalBytes']['maximum']/268435456*100,'scansAtOrAbove90Percent':sum(isinstance(r.get('disk'),dict) and r['disk']['complete'] and r['disk']['logicalBytes']>=.9*268435456 for r in rows),'limits':'Point RSS observations cannot bound short unseen peaks. CPU values average ~15-second intervals; no GPU/energy or total-app-memory claim.'},
'plotInspection':{'png':'final-resources-01.png','svg':'final-resources-01.svg','pngVisuallyInspected':True,'svgXmlParsed':True,'notes':'Three panels legible, phase markers and units visible, capture hash and scope caveats included; raw unfiltered series retained. Prepared/visible markers are close but vertically staggered. SVG follows exact same plotting recipe except export format.'}}
with (b/'final-resource-gates-01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'duration':result['duration'],'maxConservativeStallBracket':result['coverage']['largestConservativeSameDurableRunBracket'],'comparisonTriggers':comparisons},indent=2))
