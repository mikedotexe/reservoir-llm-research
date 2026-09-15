"""Offline wire budgets and predeclared startup readings from the frozen journal-room packet."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reservoir_research.study_sequences import verify_records
BASE=Path(__file__).resolve().parents[1]/'research/outputs'
CAPTURE=BASE/'2026-09-09-journal-room-startup-capture/capture.json'
REPORT=BASE/'2026-09-09-journal-room-startup-report/report.json'
packet=json.loads(CAPTURE.read_text());verify_records(packet)
report=json.loads(REPORT.read_text());by={r['path']:r for r in packet['records']};rows=[]
for study in report['studies']:
    if not study.get('receipt_verified'):continue
    receipt=json.loads(by[study['receipt']]['text'])
    request=json.loads(receipt['request_json']);response=json.loads(receipt['response_json'])
    generation=json.loads(by[study['source_record']]['text'])
    rows.append(dict(id=study['id'],era=study['era'],kind=study['kind'],
        options=request.get('options'),eval_count=response.get('eval_count'),
        done_reason=response.get('done_reason'),elapsed_s=generation['elapsed_s'],
        words=len(study['text'].split()),response=study['text'],user_text=study['user_text'],page=study.get('page')))
output=REPORT.parent
(output/'wire-and-selected.json').write_text(json.dumps(rows,indent=2)+'\n')
metrics={'verified_after':sum(s['era']=='after' for s in report['studies'] if s.get('receipt_verified')),
         'new_source_bytes':sum(r['new_bytes'] for r in report['source_progress']),
         'repeated_source_bytes':sum(r['repeated_bytes'] for r in report['source_progress']),
         'rows':[{k:v for k,v in r.items() if k not in ('response','user_text','page')} for r in rows]}
(output/'wire-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
(output/'wire-probe.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(metrics,indent=2))
