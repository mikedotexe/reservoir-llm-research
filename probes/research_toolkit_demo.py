#!/usr/bin/env python3
"""Reproduce the first toolkit demonstration from the local cache; stdlib only.

No live-source reads, model calls, or writes outside a new research output folder.
Run from the repository root with Python 3.12+; inspect import scopes in coverage.
The reading packs are tooling demonstrations, not a completed S-001 pilot.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research import explore, store
from reservoir_research.cli import coverage, date


def write_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', type=Path, default=store.default_db())
    p.add_argument('--out', type=Path, required=True, help='A new directory; existing outputs are preserved')
    args = p.parse_args()
    with store.connect(args.db) as conn:
        roots = [r[0] for r in conn.execute('SELECT root FROM sources')]
        out = store.guard_output(args.out, roots)
        out.mkdir(parents=True, mode=0o700, exist_ok=False)
        seeds = {}
        for name, filename in [('calibration','moment_2026-09-06T16-06-20.741918.txt'),
                               ('thread_id','reservoir_resonance_2026-09-06T19-29-13.844338.txt')]:
            rows = conn.execute('SELECT id FROM catalog WHERE being=? AND canonical_name=?',
                                ('minime', filename)).fetchall()
            if len(rows) != 1:
                raise ValueError(f'Expected one indexed {name} source, found {len(rows)}. Inspect coverage first.')
            seeds[name] = rows[0][0]
        report = coverage(conn)
        write_json(out/'coverage.json', report)
        packs = {}
        for name, count, ids in [('ordinary-and-calibration',4,[seeds['calibration']]),
                                 ('thread-id',0,[seeds['thread_id']])]:
            manifest = explore.sample(conn,per_being=count,since=date('2026-09-01'),
                                      until=date('2026-09-07'),context=2,curated_ids=ids,
                                      seed='toolkit demonstration, not S-001 completion')
            paths = explore.export_pack(conn,manifest,out/name)
            packs[name] = {**paths,'focal_entries':len(manifest['selected']),
                           'context_entries':len(manifest['context_entries']),
                           'eligibility':manifest['eligibility'],'overlap':manifest['overlap']}
        histories = {}
        for phrase in ('larger hall','thread_id','shared path'):
            histories[phrase] = explore.recurrence(conn,phrase)
        write_json(out/'phrase-histories.json',histories)
        summary = {'purpose':'Tooling demonstration; reader notes remain unfilled.',
                   'database':str(args.db.expanduser().resolve()),'seeds':seeds,
                   'counts':report['counts'],'packs':packs,
                   'phrases':{k:{n:v[n] for n in ('entries','occurrences','distinct_bodies','duplicate_entries')}
                              for k,v in histories.items()}}
        write_json(out/'summary.json',summary)
        print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
