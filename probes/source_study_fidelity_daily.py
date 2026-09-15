"""Daily S-007 report across retained release eras; all inputs are frozen research files."""
import argparse,json,sys,re
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reservoir_research.study_capture import encoded,sha,epoch
from reservoir_research.study_sequences import receipt_records,matching_generations,release_eras,user_text,writing_match,notebook_exposure,kind_of,source_progress,merge_ranges,range_bytes

def build(folder):
 b=json.loads((folder/'capture.json').read_bytes());s=json.loads((folder/'supplement.json').read_bytes())
 records={};revisions=[]
 for r in b['records']+s['records']:
  assert sha(r['text'].encode())==r['sha256'] and len(r['text'].encode())==r['bytes'],r['path']
  if r['path'] in records and records[r['path']]['sha256']!=r['sha256']:
   revisions.append(r['path']);continue
  records[r['path']]=dict(r,being='minime' if r['kind'] not in ('release','source','commit','research_context') else None)
 assert not revisions,'sources changed between captures: '+str(revisions)
 rs=list(records.values());lo=epoch(b['selection']['since']);hi=epoch(b['selection']['until_exclusive'])
 profiles=['continuity','follow-through','evidence-views','journal-room','study-inquiries']
 eras={profile:release_eras(rs,profile) for profile in profiles}
 gs=sorted([(r,json.loads(r['text'])) for r in rs if r['kind']=='generation'],key=lambda rg:(rg[1]['created_at_unix_ms'],rg[1]['generation_id']))
 jobs={json.loads(r['text'])['job_id']:json.loads(r['text']) for r in rs if r['kind']=='job_job.json'}
 receipts=receipt_records(rs);joined={};join_issues=[]
 for rec in receipts:
  matches=matching_generations(rec,gs)
  if len(matches)>1:join_issues.append({'receipt':rec['path'],'issue':'ambiguous','ids':[g['generation_id'] for _,g in matches]});continue
  if len(matches)==1:
   _,g=matches[0];gid=g['generation_id']
   if gid in joined:join_issues.append({'receipt':rec['path'],'issue':'duplicate logical join','id':gid});continue
   rec['completed']=g['created_at_unix_ms']/1000;rec['clock_basis']='exact request/response/system/model match to generation'
   joined[gid]=rec
 journals={Path(r['path']).name.lstrip('!'):r for r in rs if r['kind']=='journal'}
 initial=json.loads(next(r['text'] for r in rs if r['path'].endswith('source-study-v1-validation/live-rollout.json')))
 basepid=initial['minime']['new_pid']
 rows=[]
 for gr,g in gs:
  text=g.get('response_text') or '';assert sha(text.encode())==g['response_sha256']
  t=g['created_at_unix_ms']/1000;start=int(g['generation_id'].split('-')[0])/1000
  assert lo<=t<hi
  active='shared-reader';expected=basepid;transitions=[]
  for name in profiles:
   e=eras[name]
   if t>=e['minime']['boundary']:active=name;expected=e['minime']['new_pid']
   if start<e['minime']['boundary']<=t:transitions.append(name+':process')
   if start<e['astrid']['boundary']<=t or (e['astrid']['boundary']<=t<e['minime']['boundary']):transitions.append(name+':shared-helper')
  era=active+(':transition' if transitions else '')+('' if g['pid']==expected else ':unverified-pid')
  rec=joined.get(g['generation_id']);supplied=user_text(g);pages=((rec or {}).get('session_pages') or [(rec or {}).get('page')]);pages=[p for p in pages if p]
  writing=[]
  for a in g.get('linked_artifacts',[]):
   if a.get('kind')=='journal':
    j=journals.get(Path(a['path']).name.lstrip('!'));link=writing_match(text,j) if j else None
    if link:writing.append(link)
  bt=g.get('backend_timing',{});cap=bt.get('effective_num_predict');count=bt.get('eval_count')
  row=dict(id=g['generation_id'],record_path=gr['path'],record_sha256=gr['sha256'],response_sha256=g['response_sha256'],
    completed=g['created_at'],started_utc=datetime.fromtimestamp(start,timezone.utc).isoformat(),pid=g['pid'],era=era,transitions=transitions,status=g['status'],
    job_id=g.get('job_id'),job_captured=g.get('job_id') in jobs,backend=g.get('backend'),model=g.get('model'),adapter=g.get('adapter'),
    kind='source_session' if (rec or {}).get('session_pages') else kind_of(supplied),input_kind=(rec or {}).get('input_kind'),
    system_hashes=[m.get('content_sha256') for m in g['messages'] if m['role']=='system'],
    receipt_verified=bool(rec and rec['verified']),receipt_path=(rec or {}).get('path'),receipt_errors=(rec or {}).get('errors'),native_finish=(rec or {}).get('native_finish'),
    pages=[{k:p[k] for k in ['source','revision','id','start','end','eof']} for p in pages],
    notebook=notebook_exposure(supplied),text=text,user_text=supplied,writing=writing,
    next_action=g.get('next_action_parsed'),effective_tokens=cap,requested_tokens=bt.get('requested_max_tokens'),eval_tokens=count,
    cap_hit=(count>=cap if isinstance(cap,int) and cap>0 and isinstance(count,int) else None))
  rows.append(row)
 summaries=[]
 for era in dict.fromkeys(r['era'] for r in rows):
  subset=[r for r in rows if r['era']==era]
  summaries.append(dict(era=era,n=len(subset),pids=dict(Counter(r['pid'] for r in subset)),first=subset[0]['completed'],last=subset[-1]['completed'],
   statuses=dict(Counter(r['status'] for r in subset)),receipt_verified=sum(r['receipt_verified'] for r in subset),writing_matched=sum(bool(r['writing']) for r in subset),
   kinds=dict(Counter(r['kind'] for r in subset)),models=dict(Counter(r['model'] for r in subset)),effective_tokens=dict(Counter(r['effective_tokens'] for r in subset)),
   cap_hits=sum(r['cap_hit'] is True for r in subset),notebook_supplied=sum(r['notebook']['status']=='included_in_submitted_user_text' for r in subset)))
 progress=source_progress(receipts,lo,hi)
 # Reconstruct all unique source intervals in the selected window, not previous-window deliveries.
 source_groups=defaultdict(list)
 for rec in joined.values():
  if rec['verified']:
   for p in rec.get('session_pages') or [rec.get('page')]:
    if p:source_groups[(p['source'],p['revision']['sha256'])].append(p)
 sources=[]
 for (source,digest),pages in sorted(source_groups.items()):
  size=pages[0]['revision']['bytes'];data=bytearray(size);covered=bytearray(size)
  for p in pages:
   start,end=p['start']['byte'],p['end']['byte']
   raw=''.join(m[1]+'\n' for line in p['text'].splitlines() if (m:=re.fullmatch(r'\s*\d+ \| (.*)',line))).encode()
   assert len(raw) in (end-start,end-start+1),(source,start,end,len(raw))
   for i,byte in enumerate(raw[:end-start],start):
    assert not covered[i] or data[i]==byte,'overlap differs'
    data[i]=byte;covered[i]=1
  full=all(covered)
  if full:assert sha(bytes(data))==digest
  sources.append(dict(source=source,repository=source.split('/')[0],revision=digest,page_opportunities=len(pages),unique_bytes=sum(covered),file_bytes=size,file_lines=pages[0]['revision']['lines'],full_file_hash_verified=full))
 gjobs={r['job_id'] for r in rows};missing=[]
 for job in jobs.values():
  if job['job_id'] not in gjobs:
   missing.append({k:job.get(k) for k in ('job_id','action_id','action_text','status','created_at','started_at','finished_at','error','summary','artifact_refs')})
 actions=[]
 for r in rs:
  if r['kind']=='action':
   a=json.loads(r['text'])
   if lo<=a['timestamp']<hi and a.get('route') in ['self_study','research_budget_guard','source_study']:
    actions.append(a)
 baseline=json.loads((ROOT/'research/outputs/2026-09-08-source-study-fidelity/initial-report/report.json').read_bytes())
 seen={g['generation_id'] for g in baseline['generations']}
 selected=[r['id'] for r in rows if r['status']=='ok' and r['text'].strip() and r['id'] not in seen][:3]
 return dict(schema='source_study_fidelity_daily_v1',capture_sha256=sha((folder/'capture.json').read_bytes()),supplement_sha256=sha((folder/'supplement.json').read_bytes()),
  selection=json.loads((folder/'protocol.json').read_bytes()),capture_errors=b['errors']+s['errors'],captured_records=len(rs),
  release_eras=eras,eras=summaries,generation_count=len(rows),jobs_queued=len(jobs),job_statuses=dict(Counter(j['status'] for j in jobs.values())),
  jobs_without_window_generation=missing,duplicate_baseline_ids=[r['id'] for r in rows if r['id'] in seen],close_reading_ids=selected,
  complete_writing_matches=sum(bool(r['writing']) for r in rows),unique_receipt_matches=len(joined),verified_receipt_matches=sum(r['receipt_verified'] for r in rows),
  join_issues=join_issues,unverified_receipts_in_window=[{'path':rec['path'],'errors':rec['errors']} for rec in receipts if not rec['verified'] and lo<=rec['completed']<hi],
  sources=sources,source_progress=progress,selected_actions=actions,studies=rows,
  limits=['Root journals and filename self_study generation/job frames; no unrecorded-opportunity denominator.',
  'Frozen daily selection persists despite related S-008 ad hoc observations; overlapping records are not independent evidence.',
  'Multiple prompt, navigation, notebook and output-budget releases coexist; no pooled causal fidelity score.',
  'Native response clocks only order unjoined receipt history; joined receipt clocks are local generation record times.',
  'Blocked/completed jobs need action and generation evidence separately; later completions are right-censored at cutoff.'])
def main():
 p=argparse.ArgumentParser();p.add_argument('packet',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert a.out.resolve().is_relative_to(ROOT/'research/outputs')
 rep=build(a.packet);a.out.mkdir(mode=0o700)
 (a.out/'report.json').write_bytes(encoded(rep))
 for row in rep['studies']:
  if row['id'] in rep['close_reading_ids']:
   (a.out/(row['id']+'.md')).write_text('# '+row['id']+'\n\n'+row['completed']+'\n\n## Supplied user input\n\n'+row['user_text']+'\n\n## Authored response\n\n'+row['text']+'\n')
 for f in a.out.iterdir():f.chmod(0o600)
 print(json.dumps({k:rep[k] for k in ['generation_count','jobs_queued','job_statuses','complete_writing_matches','verified_receipt_matches','close_reading_ids','sources','capture_errors','join_issues','unverified_receipts_in_window']},indent=2))
if __name__=='__main__':main()
