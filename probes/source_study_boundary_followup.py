"""Offline predeclared continuation of a prior-window recovery run; no source-system access."""
import json
from pathlib import Path
from reservoir_research.study_capture import sha

def build(packet):
    root=packet.parents[2]
    tracking=json.loads((packet/'tracking-before.json').read_bytes())
    previous_window=tracking['windows'][-1]
    previous_report_path=root/previous_window['report']
    previous_bytes=previous_report_path.read_bytes()
    assert sha(previous_bytes)==previous_window['report_sha256']
    previous=json.loads(previous_bytes)
    current=json.loads((packet/'final-report/report.json').read_bytes())
    assert previous['selection']['until_exclusive']==current['selection']['since']
    tail=[]
    last=previous['studies'][-1]
    assert last['kind']=='recovery'
    key=(last['kind'],last['action_text'])
    for s in reversed(previous['studies']):
        if (s['kind'],s['action_text'])!=key:
            break
        tail.append(s)
    tail.reverse()
    prefix=[]
    for s in current['studies']:
        if (s['kind'],s['action_text'])!=key:
            break
        prefix.append(s)
    following=current['studies'][len(prefix):]
    first_different=following[0] if following else None
    first_source=next((s for s in following if s['receipt_verified'] and s['pages']),None)
    def compact(s):
        return {k:s[k] for k in ['id','completed','action_text','kind','receipt_verified','pages','next_action','record_sha256','response_sha256']}
    return dict(schema='s007_boundary_recovery_followup_v1',
                selection=json.loads((packet/'protocol.json').read_bytes())['followup'],
                previous_report=previous_window['report'],previous_report_sha256=sha(previous_bytes),
                current_report_sha256=sha((packet/'final-report/report.json').read_bytes()),
                repeated_action=key[1],previous_tail=[compact(s) for s in tail],current_prefix=[compact(s) for s in prefix],
                previous_n=len(tail),current_n=len(prefix),combined_n=len(tail)+len(prefix),
                first=tail[0]['completed'],last=(prefix or tail)[-1]['completed'],
                right_censored=first_different is None,
                first_different=None if first_different is None else compact(first_different),
                first_subsequent_source=None if first_source is None else dict(compact(first_source),text=first_source['text'],user_text=first_source['user_text']),
                limits='Consecutive within the captured study generation frame, not the full action stream. Ending the repeated command or receiving source does not by itself establish a corrected belief or saved note. Prior-window entries are references, not new observations.')
