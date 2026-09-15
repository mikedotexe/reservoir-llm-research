"""Retain current identifier locations only when the source matches the observed revision."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/outputs/2026-09-09-study-inquiries-startup-report'
rows=json.loads((OUT/'wire-and-questions.json').read_text())
source='astrid/crates/astrid-capsule/src/dispatcher.rs'
revisions={r['page']['revision']['sha256'] for r in rows if r.get('page') and r['page']['source']==source}
p=Path('/Users/v/other')/source;raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert revisions=={digest},'Current source no longer matches the observed revision'
lines=[dict(line=i,text=line) for i,line in enumerate(raw.decode().splitlines(),1) if 'fn dispatch_single(' in line or 'tokio::task::spawn(' in line]
(OUT/'implementation-locations.json').write_text(json.dumps(dict(source=source,sha256=digest,matches_observed_revision=True,lines=lines,scope='Current source at the observed revision; no runtime execution inference.'),indent=2)+'\n')
(OUT/'source-link-probe.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(lines))
