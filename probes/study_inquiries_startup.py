"""Describe the predeclared startup window without turning exposure into an improvement score."""
from pathlib import Path
import json,sys
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reservoir_research.study_sequences import verify_records
BASE=Path(__file__).resolve().parents[1]/'research/outputs'
CAPTURE=BASE/'2026-09-09-study-inquiries-startup-capture/capture.json'
REPORT=BASE/'2026-09-09-study-inquiries-startup-report/report.json'
packet=json.loads(CAPTURE.read_text());verify_records(packet)
report=json.loads(REPORT.read_text());by={r['path']:r for r in packet['records']}
rows=[]
for study in report['studies']:
 if not study.get('receipt_verified'):continue
 receipt=json.loads(by[study['receipt']]['text']);wire=receipt.get('attempt',receipt)
 request=json.loads(wire['request_json']);response=json.loads(wire['response_json'])
 record=json.loads(by[study['source_record']]['text'])
 system='\n'.join(m.get('content','') for m in request.get('messages',[]) if m.get('role')=='system')
 guidance=all(token in system for token in ['QUESTION NEW','SELF_STUDY RELATE','SELF_STUDY SESSION','SELF_STUDY TRACE'])
 rows.append(dict(inquiry_guidance_supplied=guidance,id=study['id'],being=study['being'],era=study['era'],kind=study['kind'],question_id=study.get('question_id'),started_utc=study['started_utc'],completed_utc=study['completed_utc'],output_ceiling=request.get('max_tokens',request.get('options',{}).get('num_predict')),context_tokens=request.get('options',{}).get('num_ctx'),output_tokens=response.get('eval_count',response.get('usage',{}).get('completion_tokens')),native_finish=study.get('native_finish'),elapsed_seconds=record.get('elapsed_s',record.get('elapsed_ms',0)/1000),words=len(study['text'].split()),next=study['next'],writing_matches=len(study['writing']),notebook=study['notebook'],response=study['text'],user_text=study['user_text'],page=study.get('page'),session_pages=study.get('session_pages',[]),followthrough=study['followthrough']))
metrics=dict(selection=report['selection'],verified_by_being_era=dict(Counter(r['being']+':'+r['era'] for r in rows)),kinds=dict(Counter(r['kind'] for r in rows)),guidance_supplied=sum(r['inquiry_guidance_supplied'] for r in rows),named_question_inputs=sum(bool(r['question_id']) for r in rows),session_inputs=sum(bool(r['session_pages']) for r in rows),new_source_bytes=sum(r['new_bytes'] for r in report['source_progress']),repeated_source_bytes=sum(r['repeated_bytes'] for r in report['source_progress']),capture_errors=report['capture_errors'],invalid_receipts=report['invalid_receipts'],join_issues=report['receipt_join_issues'],selected=report['selected'])
(REPORT.parent/'wire-and-questions.json').write_text(json.dumps(rows,indent=2)+'\n')
(REPORT.parent/'startup-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
(REPORT.parent/'wire-probe.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(metrics,indent=2))
