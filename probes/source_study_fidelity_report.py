#!/usr/bin/env python3
"""Offline S-007 report; validates captured bytes and actual source-page delivery."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json,re
from pathlib import Path
from zoneinfo import ZoneInfo

def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def ep(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def user(g): return '\n'.join(m.get('content','') for m in g['messages'] if m['role']=='user')
def report(path):
 b=json.loads(path.read_text()); assert b['schema']=='source_study_fidelity_v1'
 for r in b['records']: assert sha(r['text'])==r['sha256'],r['path']
 rs=b['records'];lo=ep(b['selection']['since']);hi=ep(b['selection']['until_exclusive'])
 reload_record=next(r for r in rs if 'self-study-parity-retry.jsonl' in r['path'])
 reload=json.loads(reload_record['text'].splitlines()[-1]); assert reload['outcome']=='success'
 boundary=datetime.strptime(reload['new_started_at'],'%a %b %d %H:%M:%S %Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()
 rollout=json.loads(next(r['text'] for r in rs if r['path'].endswith('source-study-v1-validation/live-rollout.json')))
 assert rollout['minime']['receipt_sha256']==reload_record['sha256']
 assert rollout['bridge']['receipt_sha256']==next(r['sha256'] for r in rs if r['path']==rollout['bridge']['receipt_path'])
 gs=sorted([(r,json.loads(r['text'])) for r in rs if r['kind']=='generation'],key=lambda rg:rg[1]['created_at_unix_ms'])
 jobs={json.loads(r['text'])['job_id']:json.loads(r['text']) for r in rs if r['kind']=='job_job.json'}
 journals={Path(r['path']).name.lstrip('!'):r for r in rs if r['kind']=='journal'}
 state=json.loads(next(r['text'] for r in rs if r['kind']=='reader_state'))
 deliveries=[]; groups=defaultdict(list)
 for r in [r for r in rs if r['kind']=='delivery']:
  d=json.loads(r['text']); p=d['page'];req=json.loads(d['request_json']);resp=json.loads(d['response_json']);rawtext=resp.get('message',{}).get('content')
  assert p['text'] in '\n'.join(m.get('content','') for m in req['messages'] if m['role']=='user')
  assert resp.get('done') is True and resp.get('done_reason')!='length' and rawtext and not resp.get('error')
  receipt=state['receipts'].get(p['id']); assert receipt and receipt['artifact_sha256']==r['sha256']
  assert receipt['request_sha256']==sha(d['request_json']) and receipt['response_sha256']==sha(d['response_json'])
  matches=[g for _,g in gs if user(g)==next(m['content'] for m in req['messages'] if m['role']=='user') and g['response_text']==rawtext]
  if not matches:
   deliveries.append(dict(page_id=p['id'],source=p['source'],join='outside selected generation frame or unresolved',path=r['path']));continue
  assert len(matches)==1
  g=matches[0]; assert sha(rawtext)==g['response_sha256']
  assert req['model']==g['model']
  sysh=next(m['content_sha256'] for m in g['messages'] if m['role']=='system')
  assert sha(next(m['content'] for m in req['messages'] if m['role']=='system'))==sysh
  row=dict(page_id=p['id'],source=p['source'],revision=p['revision'],start=p['start'],end=p['end'],eof=p['eof'],generation_id=g['generation_id'],created_at=g['created_at'],native_finish_reason=resp.get('done_reason'),complete_page_in_actual_request=True,exact_response_match=True,source_record_sha256=r['sha256'],path=r['path'])
  deliveries.append(row);groups[(p['source'],p['revision']['sha256'])].append(p)
 # Reconstruct exact bytes from numbered line fragments, using retained byte lengths
 # to distinguish renderer-added newlines at partial-line page boundaries.
 coverage=[]
 for (source,rev),pages in groups.items():
  pages=sorted(pages,key=lambda p:p['start']['byte']); raw=b'';end=0;contiguous=True
  for p in pages:
   if p['start']['byte']!=end: contiguous=False
   body=p['text'].split('\n\n',1)[1]
   data=''.join(m[1]+'\n' for line in body.splitlines() if (m:=re.fullmatch(r'\s*\d+ \| (.*)',line))).encode()
   needed=p['end']['byte']-p['start']['byte']; assert len(data) in (needed,needed+1)
   if len(data)==needed+1: assert data.endswith(b'\n');data=data[:-1]
   raw+=data;end=p['end']['byte']
  full=contiguous and end==pages[-1]['revision']['bytes'] and pages[-1]['eof']
  if full: assert sha(raw)==rev
  coverage.append(dict(source=source,revision_sha256=rev,pages=len(pages),delivered_bytes=sum(p['end']['byte']-p['start']['byte'] for p in pages),file_bytes=pages[-1]['revision']['bytes'],file_lines=pages[-1]['revision']['lines'],contiguous=contiguous,full_file_hash_reconstructed=full,last_line=pages[-1]['end']['line'],beyond_line_400_pages=sum(p['end']['line']>400 for p in pages)))
 rows=[]; byid={d.get('generation_id'):d for d in deliveries if d.get('generation_id')}
 for r,g in gs:
  t=g['created_at_unix_ms']/1000;job=jobs.get(g['job_id']);start=ep(job['created_at']) if job else int(g['generation_id'].split('-')[0])/1000
  if start<boundary<=t: era='transition'
  elif t<boundary: era='pre'
  elif g['pid']==reload['new_pid'] and g['adapter'].get('template_mode')=='source_study_intact':era='post_verified_reader'
  else:era='post_unverified'
  assert sha(g['response_text'])==g['response_sha256']
  links=[]
  for a in g['linked_artifacts']:
   if a.get('kind')=='journal':
    j=journals.get(Path(a['path']).name.lstrip('!'))
    links.append(dict(path=a['path'],captured=j is not None,exact_response_contained=bool(j and g['response_text'] in j['text'])))
  u=user(g); bt=g.get('backend_timing',{});cap=bt.get('effective_num_predict');count=bt.get('eval_count')
  d=byid.get(g['generation_id']); old=re.search(r'^This is: (.+)$',u,re.M)
  page_type='source' if u.startswith('SOURCE ') else 'navigation' if u.startswith(('Shared system map','Literal source search:','End of ')) else 'legacy_excerpt'
  rows.append(dict(generation_id=g['generation_id'],created_at=g['created_at'],pid=g['pid'],era=era,source=(d or {}).get('source') or (old[1] if old else None),page_type=page_type,delivery_page_id=(d or {}).get('page_id'),job_id=g['job_id'],captured_job=bool(job),job_status=(job or {}).get('status'),status=g['status'],backend=g['backend'],model=g['model'],fallback_used=g['fallback_used'],adapter=g['adapter'],system_hash=next(m.get('content_sha256') for m in g['messages'] if m['role']=='system'),requested_tokens=bt.get('requested_max_tokens'),effective_tokens=cap,eval_tokens=count,cap_hit=(count>=cap if isinstance(count,int) and isinstance(cap,int) and cap>0 else None),native_finish_reason=(d or {}).get('native_finish_reason'),next_action=g.get('next_action_parsed'),journal_links=links,source_record_sha256=r['sha256'],response_sha256=g['response_sha256']))
 summary={}
 for era in sorted({r['era'] for r in rows}):
  subset=[r for r in rows if r['era']==era]
  summary[era]=dict(generations=len(subset),statuses=dict(Counter(r['status'] for r in subset)),pids=dict(Counter(r['pid'] for r in subset)),models=dict(Counter(r['model'] for r in subset)),compacted=sum(bool(r['adapter'].get('compacted')) for r in subset),cap_hits=sum(r['cap_hit'] is True for r in subset),cap_known=sum(r['cap_hit'] is not None for r in subset),native_stop_known=sum(r['native_finish_reason'] is not None for r in subset),page_types=dict(Counter(r['page_type'] for r in subset)),verified_source_deliveries=sum(bool(r['delivery_page_id']) for r in subset),journal_response_matches=sum(any(a['exact_response_contained'] for a in r['journal_links']) for r in subset),missing_captured_jobs=sum(not r['captured_job'] for r in subset))
 selected=[r['generation_id'] for r in rows if r['era']=='pre' and r['status']=='ok'][-3:]+[r['generation_id'] for r in rows if r['era']=='post_verified_reader' and r['status']=='ok'][:3]
 helper_artifacts=[dict(path=r['path'],manifest_sha256=r['sha256'],artifact=json.loads(r['text'])['artifacts']['source-study-reader']) for r in rs if r['kind']=='release' and r['path'].endswith('manifest.json')]
 return dict(schema='source_study_fidelity_report_v1',capture_sha256=sha(path.read_bytes()),selection=b['selection'],record_counts=dict(Counter(r['kind'] for r in rs)),errors=b['errors'],activation=dict(commit=rollout['minime_commit'],paired_astrid_commit=rollout['astrid_commit'],new_pid=reload['new_pid'],started_at_pacific=reload['new_started_at'],started_at_utc=datetime.fromtimestamp(boundary,timezone.utc).isoformat(),verified_at=reload['recorded_at'],receipt_hash_verified=True),helper_artifacts=helper_artifacts,eras=summary,jobs=dict(total=len(jobs),statuses=dict(Counter(j['status'] for j in jobs.values())),without_generation=[j['job_id'] for j in jobs.values() if j['job_id'] not in {g['job_id'] for _,g in gs}]),close_reading_ids=selected,deliveries=deliveries,source_coverage=coverage,generations=rows,limits=['Filename-selected frames, journals root only; no live database or archive scan.','Generation file time is response recording; jobs selected by queue time. Boundary jobs may be absent.','Reader receipts have no local delivery timestamp or generation ID; exact request/response and system/model matches join them here.','Present reader state is capture-time evidence; do not retrospectively assert when the bookmark was persisted.','All-text/receipt counts do not estimate semantic fidelity or causal improvement.'])
def main():
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rep=report(a.capture)
 repo=Path(__file__).resolve().parents[1]
 if not a.out.resolve().is_relative_to(repo/'research/outputs'):raise ValueError('research output required')
 a.out.mkdir(mode=0o700)
 (a.out/'report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
 b=json.loads(a.capture.read_text());gs={json.loads(r['text'])['generation_id']:json.loads(r['text']) for r in b['records'] if r['kind']=='generation'}
 for gid in rep['close_reading_ids']:
  g=gs[gid]; (a.out/f'{gid}.md').write_text(f'# {gid}\n\n{g["created_at"]}\n\n## Exact adapted user request\n\n{user(g)}\n\n## Exact authored response\n\n{g["response_text"]}\n')
 for f in a.out.iterdir():f.chmod(0o600)
 print(json.dumps({k:rep[k] for k in ('activation','eras','jobs','source_coverage','close_reading_ids','errors')},indent=2))
if __name__=='__main__':main()
