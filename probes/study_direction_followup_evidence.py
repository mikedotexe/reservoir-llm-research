"""Join the frozen follow-up's journals to exact response evidence, offline."""
from collections import Counter
import json
import statistics

from study_direction_followup import OUT, load, save, sha


def visible(wire):
    if wire.get('choices'):
        return wire['choices'][0].get('message',{}).get('content') or ''
    return wire.get('response') or wire.get('message',{}).get('content') or ''


def main():
    manifest=json.loads((OUT/'capture-manifest.json').read_text())
    for path, row in manifest['files'].items():assert sha((OUT/path).read_bytes())==row['sha256']
    indexes=[json.loads(line) for line in (OUT/'journal-index.jsonl').read_text().splitlines()]
    report={}
    expected='af059d5e5bbd2ca4340a30a9cdf4f7687979fe1a4878e375ee3dc1faf5d9cdc9'
    for who in ('astrid','minime'):
        receipts=[]
        for kind in ('shared','navigation'):
            for row in load(f'{who}-{kind}.jsonl'):
                data=json.loads(row['text'])
                wire=json.loads(data.get('response_json','{}'))
                response=visible(wire)
                output=data.get('output',{})
                messages=json.loads(data.get('request_json','{}')).get('messages',[])
                page=output.get('page') or data.get('page') or {}
                choices=wire.get('choices') or [{}]
                receipts.append(dict(retained=row['path'],sha256=row['sha256'],response=response,
                     response_sha256=sha(response.encode()),mtime=row['timestamp'],
                     input_kind=output.get('input_kind'),page=page,
                     offered_prompt_sha256=sha(output.get('system_prompt','').encode()),
                     prompt_in_wire=bool(output.get('system_prompt')) and any(m.get('role')=='system' and output['system_prompt'] in str(m.get('content','')) for m in messages),
                     complete_input_in_wire=bool(output.get('text')) and any(output['text'] in str(m.get('content','')) for m in messages),
                     offered_bytes=len(output.get('text','').encode()),
                     checkpoint='OPTIONAL STUDY CHECK-IN' in output.get('text',''),
                     finish=choices[0].get('finish_reason',wire.get('done_reason')),
                     tokens=wire.get('usage',{}).get('completion_tokens',wire.get('eval_count')),
                     generation_evidence=wire.get('coupled_generation_v1',{})))
        generations=[dict(json.loads(r['text']),captured_sha256=r['sha256']) for r in load(f'{who}-generations.jsonl')]
        jobs={json.loads(r['text'])['job_id']:json.loads(r['text']) for r in load(f'{who}-jobs.jsonl')}
        joined=[]
        for row in load(f'{who}-journals.jsonl'):
            index=next(i for i in indexes if i['path']==row['path'])
            if index['mode']!='source_study':continue
            matches=[r for r in receipts if r['response'] and r['response'] in row['text']]
            gens=[g for g in generations if g.get('response_text') and g['response_text'] in row['text']]
            # Keep ambiguous exact matches explicit instead of choosing one.
            match=matches[0] if len(matches)==1 else None
            gen=gens[0] if len(gens)==1 else None
            summary=dict(name=row['name'],path=row['path'],journal_sha256=row['sha256'],
                 timestamp=row['timestamp'],response_matches=len(matches),generation_matches=len(gens),
                 next_text=index['next_raw'],words=index['words'],title=index['metadata']['title'])
            if match:
                page=match['page']
                summary.update(receipt=match['retained'],receipt_sha256=match['sha256'],
                    response_sha256=match['response_sha256'],input_kind=match['input_kind'],
                    source=page.get('source'),revision=page.get('revision'),
                    start=page.get('start'),end=page.get('end'),finish=match['finish'],tokens=match['tokens'],
                    new_prompt=match['offered_prompt_sha256']==expected and match['prompt_in_wire'],
                    complete_input_in_wire=match['complete_input_in_wire'],checkpoint=match['checkpoint'])
            if gen:
                summary.update(generation_id=gen['generation_id'],model=gen.get('model'),
                    generation_status=gen['status'],elapsed_s=gen.get('elapsed_s'),
                    generation_finish=(gen.get('backend_timing') or {}).get('native_finish'),
                    generation_tokens=(gen.get('backend_timing') or {}).get('eval_count'),
                    job_status=jobs.get(gen.get('job_id'),{}).get('status'))
            joined.append(summary)
        joined.sort(key=lambda r:r['timestamp'])
        attempts=[]
        for gen in generations:
            job=jobs.get(gen.get('job_id'),{})
            route='private_write' if gen.get('prompt_class')=='private_writing' or job.get('action_text','').startswith('WRITE ') else gen.get('prompt_class') or gen.get('lane')
            attempts.append(dict(generation_id=gen['generation_id'],route=route,status=gen['status'],
                finish=(gen.get('backend_timing') or {}).get('native_finish'),
                tokens=(gen.get('backend_timing') or {}).get('eval_count'),
                job_id=gen.get('job_id'),job_status=job.get('status'),created_at=gen.get('created_at') or gen.get('created_at_unix_ms')))
        tokens=[r['tokens'] for r in joined if r.get('tokens') is not None]
        report[who]=dict(studies=len(joined),unique_response_receipt_matches=sum(r['response_matches']==1 for r in joined),
            distinct_response_bodies=len({r['response_sha256'] for r in joined if r.get('response_sha256')}),
            new_prompt=sum(r.get('new_prompt',False) for r in joined),
            complete_input_in_wire=sum(r.get('complete_input_in_wire',False) for r in joined),
            source_page_count=sum(bool(r.get('source')) for r in joined),
            input_kinds=dict(Counter(r.get('input_kind','unmatched') for r in joined)),
            source_counts=dict(Counter(r['source'] for r in joined if r.get('source'))),
            finishes=dict(Counter(str(r.get('finish','unmatched')) for r in joined)),
            tokens=dict(n=len(tokens),min=min(tokens) if tokens else None,max=max(tokens) if tokens else None,
                        median=statistics.median(tokens) if tokens else None),
            next_text_counts=dict(Counter((r['next_text'] or 'none').split()[0] for r in joined)),
            generation_routes=dict(Counter(r['route'] for r in attempts)),
            unsuccessful_attempts=[r for r in attempts if r['status']!='ok'],
            private_attempts=[r for r in attempts if r['route']=='private_write'],
            detail=joined,limits='Exact response containment is content association, not independent action dispatch. This frame uses generation filename epochs, not verified request starts; journal/receipt clocks differ. Missing provider failures remain unknown.')
    save(OUT/'followthrough.json',report)
    print(json.dumps({who:{k:v for k,v in result.items() if k not in ('detail','private_attempts')} for who,result in report.items()},indent=2))


if __name__=='__main__':main()
