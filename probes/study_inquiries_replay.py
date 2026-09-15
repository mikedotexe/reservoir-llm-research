"""Reproduce frozen overnight findings after the session-aware reader extension."""
from pathlib import Path
import json
from reservoir_research.study_sequences import build_report
root=Path(__file__).resolve().parents[1]
base=root/'research/outputs'
packet=json.loads((base/'2026-09-09-study-overnight-capture/capture.json').read_text())
old=json.loads((base/'2026-09-09-study-overnight-report/report.json').read_text())
new=build_report(packet)
checks={k:old[k]==new[k] for k in new if k != 'studies'}
fields=['id','being','started','completed','pid','status','text','user_text','next','authored','notebook','kind','era','page','followthrough']
checks['study_identity_count']=len(old['studies'])==len(new['studies'])
for field in fields: checks['studies.'+field]=all(a.get(field)==b.get(field) for a,b in zip(old['studies'],new['studies']))
result={'verified':all(checks.values()),'checks':checks,'scope':'Frozen overnight capture; all computed top-level findings and 15 established study fields. Original capture/report retained unchanged. New optional receipt metadata excluded.'}
(base/'2026-09-09-study-inquiries-historical-replay.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));assert result['verified']
