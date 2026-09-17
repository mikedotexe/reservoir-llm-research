"""Frozen-window day-9 descriptive account. Research copies only; no live reads."""
import argparse,json,re
from collections import Counter
from pathlib import Path
from reservoir_research.study_capture import encoded,sha,epoch

def build(packet):
    report=json.loads((packet/'final-report/report.json').read_bytes())
    protocol=json.loads((packet/'protocol.json').read_bytes())
    rows=report['studies'];source=[s for s in rows if s['actual_route']=='source_study']
    selected=[s for s in rows if s['id'] in report['close_reading_ids']]
    assert len(selected)==3 and all(s['actual_route']=='source_study' for s in selected)
    second,third=selected[1:]
    assert len(second['pages'])==len(third['pages'])==1
    a,b=second['pages'][0],third['pages'][0]
    assert all(a[k]==b[k] for k in ('source','revision','start','end')) and a['id']!=b['id']
    assert a['source']=='astrid/crates/astrid-kernel/src/lib.rs'
    assert a['start']==dict(byte=0,line=1) and a['end']==dict(byte=4540,line=98)
    numbered=[(int(m[1]),m[2]) for line in third['user_text'].splitlines() if (m:=re.fullmatch(r'\s*(\d+) \| (.*)',line))]
    assert min(n for n,_ in numbered)==1 and max(n for n,_ in numbered)==98
    assert any(n==37 and 'pub struct Kernel' in t for n,t in numbered)
    assert any(n==97 and 'impl Kernel' in t for n,t in numbered)
    quote='The current page (lines 1–4540) shows the `Kernel` struct definition and the start of its implementation.'
    assert third['text'].count(quote)==1
    note=next(line.removeprefix('STUDY_NOTE: ') for line in second['text'].splitlines() if line.startswith('STUDY_NOTE: '))
    assert third['notebook']['fields']['note']['text']==note
    after=rows[rows.index(third)+1]
    assert third['next_action']==after['action_text']=='SELF_STUDY CONTINUE'
    assert after['receipt_verified'] and after['pages'][0]['source']==a['source']
    assert after['pages'][0]['revision']==a['revision']
    assert after['pages'][0]['start']['byte']==a['end']['byte']
    own=next((s for s in source if s['receipt_verified'] and any(p['source'].startswith('minime/') for p in s['pages'])),None)
    page_counts=Counter()
    for s in report['sources']:page_counts[s['repository']]+=s['page_opportunities']
    return dict(schema='s007_day9_descriptive_account_v1',report_sha256=sha((packet/'final-report/report.json').read_bytes()),
        window=[protocol['since'],protocol['until_exclusive']],generation_count=len(rows),
        source_statuses=dict(Counter(s['status'] for s in source)),private_writing=len(rows)-len(source),
        source_input_kinds=dict(Counter(s['kind'] for s in source)),
        source_pages_by_repository=dict(page_counts),source_paths=len({s['source'] for s in report['sources']}),
        source_revisions=len(report['sources']),full_revision_hashes=sum(s['full_file_hash_verified'] for s in report['sources']),
        source_wire_matches=sum(s['receipt_verified'] for s in source),full_source_journals=sum(bool(s['writing']) for s in source),
        pids=dict(Counter(str(s['pid']) for s in rows)),models=dict(Counter(s['model'] for s in rows)),
        output_caps=dict(Counter(str(s['effective_tokens']) for s in rows)),cap_hits=sum(s['cap_hit'] is True for s in rows),
        selected_ids=report['close_reading_ids'],same_interval_reread=dict(generations=[second['id'],third['id']],source=a['source'],revision=a['revision'],start=a['start'],end=a['end'],distinct_page_ids=[a['id'],b['id']]),
        line_byte_confusion=dict(generation_id=third['id'],quote=quote,quote_start=third['text'].index(quote),response_sha256=third['response_sha256'],source_byte_end=4540,visible_line_end=98,kernel_definition_line=37,implementation_start_line=97),
        selected_note_carriage=dict(from_id=second['id'],to_id=third['id'],note=note,correctness='Carriage alone does not establish correctness.'),
        next_requested_input=dict(from_id=third['id'],to_id=after['id'],action=after['action_text'],pages=after['pages'],basis='Exact request/response join; continuation supplied. No later-response fidelity judgment.'),
        own_repository_followup=dict(selection=protocol['followup'],observed=own is not None,generation_id=own['id'] if own else None),
        jobs_without_window_generation=report['jobs_without_window_generation'],
        limits=['Descriptive counts are not a fidelity score or independent trials.','No exhaustive later-correction search; recall is not verification.','No pre/post causal effect estimate; live eras remain distinct.'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('packet',type=Path);args=p.parse_args()
    result=build(args.packet)
    with (args.packet/'descriptive-account.json').open('xb') as f:f.write(encoded(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ['jobs_without_window_generation','selected_note_carriage','next_requested_input']},indent=2))
