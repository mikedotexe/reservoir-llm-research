#!/usr/bin/env python3
"""Offline integrity and negative controls for a frozen S-007 packet."""
import copy, hashlib,json,tempfile
from pathlib import Path
from source_study_fidelity_report import report
from source_study_fidelity_annotations import check
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/outputs/2026-09-08-source-study-fidelity'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def main():
 capture=OUT/'capture.json'; ledger=OUT/'claim-annotations.json';b=json.loads(capture.read_text())
 r=report(capture);assert json.loads(json.dumps(r))==json.loads((OUT/'initial-report/report.json').read_text());assert r==report(capture)
 a=check(capture,ledger);assert a==json.loads((OUT/'verified-claim-checks.json').read_text())
 reload=json.loads(next(x['text'] for x in b['records'] if 'self-study-parity-retry.jsonl' in x['path']).splitlines()[-1])
 for name in ('source_study.py','runtime.py'):
  expected=next(x['sha256'] for x in b['records'] if x['kind']=='source' and '@37ed8b7f153043521cc89fe881ed55fd56b5700f:' in x['path'] and x['path'].endswith('/'+name))
  assert reload['source_inputs']['minime_autonomy/'+name]==expected
 negatives={}
 with tempfile.TemporaryDirectory(dir=OUT) as temp:
  p=Path(temp)/'altered.json'
  bad=copy.deepcopy(b);bad['records'][0]['text']+=' altered';p.write_text(json.dumps(bad))
  try: report(p)
  except AssertionError: negatives['changed_record_hash_rejected']=True
  else: raise AssertionError('corrupted record accepted')
  bad=copy.deepcopy(b);d=next(x for x in bad['records'] if x['kind']=='delivery');wire=json.loads(d['text']);req=json.loads(wire['request_json']);next(m for m in req['messages'] if m['role']=='user')['content']='page removed';wire['request_json']=json.dumps(req);d['text']=json.dumps(wire);d['sha256']=sha(d['text'].encode());p.write_text(json.dumps(bad))
  try: report(p)
  except AssertionError: negatives['missing_page_in_wire_rejected']=True
  else: raise AssertionError('missing delivery page accepted')
  bad=json.loads(ledger.read_text());bad['claims'][0]['quote']='invented unsupported quotation';p.write_text(json.dumps(bad))
  try: check(capture,p)
  except AssertionError: negatives['invented_annotation_quote_rejected']=True
  else: raise AssertionError('invented quote accepted')
 checks=dict(schema='source_study_fidelity_verification_v1',capture_sha256=sha(capture.read_bytes()),retained_records_hash_verified=len(b['records']),repeat_report_identical=True,stored_report_matches=True,annotation_spans_verified=a['claim_checks'],receipt_hashes_verified=r['activation']['receipt_hash_verified'],complete_wire_joins=len([d for d in r['deliveries'] if d.get('generation_id')]),full_source_hash_reconstructions=sum(c['full_file_hash_reconstructed'] for c in r['source_coverage']),negative_controls=negatives,limits='Verifies evidence and computation, not completeness of live records or the semantic annotation judgments.')
 (OUT/'verification.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
