#!/usr/bin/env python3
"""Verify and summarize human/agent close-reading annotations against frozen outputs.

These are selected claim checks within six predeclared responses, not an exhaustive
claim census or a corpus accuracy estimate. Metaphors and felt claims stay unscored.
"""
import argparse,json,hashlib
from collections import Counter
from pathlib import Path

def check(capture,ledger):
 b=json.loads(capture.read_text()); gs={json.loads(r['text'])['generation_id']:json.loads(r['text']) for r in b['records'] if r['kind']=='generation'}
 d=json.loads(ledger.read_text()); rows=[]
 for a in d['claims']:
  text=gs[a['generation_id']]['response_text']; quote=a['quote']; assert text.count(quote)==1,(a['id'],'quote not unique')
  a=dict(a,start=text.index(quote),end=text.index(quote)+len(quote),response_sha256=hashlib.sha256(text.encode()).hexdigest());rows.append(a)
 return dict(schema='source_study_claim_checks_v1',selection=d['selection'],claim_checks=len(rows),categories=dict(Counter(a['category'] for a in rows)),claims=rows,episode_notes=d['episode_notes'],limits='Selected checks only, not all factual claims. No before/after quality score or causal estimate.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('ledger',type=Path);a=p.parse_args();print(json.dumps(check(a.capture,a.ledger),ensure_ascii=False,indent=2))
