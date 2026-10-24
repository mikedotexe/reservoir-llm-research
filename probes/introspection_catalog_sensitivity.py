#!/usr/bin/env python3
"""Source-only lexical sensitivity definitions; never alter the frozen primary.

Freeze inventories before inspecting catalog outcomes. Literal A admits only
phrases that actually occur with literal spaces in full source text. Tokenized B
uses the same word tokenizer for source, concise/common exclusion, and output.
Neither is a semantic, action, or experiential measure.
"""
from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_experiments import runner
from reservoir_experiments.attribution_catalog import WORDS, OPEN_CONTRACT, _prose_and_next
from reservoir_experiments.statistics import paired_contrast, summarize


def bigrams(text):
    words = WORDS.findall(text.lower())
    return Counter(' '.join(pair) for pair in zip(words, words[1:]))


def literal_count(phrase, text):
    return len(re.findall(r'\b' + re.escape(phrase) + r'\b', text.lower()))


def derive(bundle):
    original = set(bundle['phrase_inventory'])
    concise_pairs = bigrams(bundle['concise'])
    candidates = set()
    for row in bundle['correspondence']:
        candidates.update(p for p in bigrams(row['removed_description'])
                          if all(len(w) >= 4 for w in p.split()))
    return {
        'literal_a': sorted(p for p in original if literal_count(p, bundle['full'])
                            and not literal_count(p, bundle['concise'])),
        'tokenized_b': sorted(p for p in candidates if p not in concise_pairs),
    }


def content_hashes(bundle):
    return {k + '_sha256': runner.sha(bundle[k].encode()) for k in ('full', 'concise')}


def freeze(args):
    bundle = runner.read_json(args.catalog)
    result = {'schema_version': 1, 'created_at': runner.now(),
              'status': 'Source-derived sensitivity definitions; original primary retained unchanged.',
              'catalog_sha256': runner.sha(args.catalog.read_bytes()),
              **content_hashes(bundle), 'word_pattern': WORDS.pattern,
              'primary_inventory': bundle['phrase_inventory'], 'inventories': derive(bundle),
              'definitions': {
                  'literal_a': 'Literal boundary-delimited phrases present in full, absent in concise; same literal exclusion for common/history and same literal output count.',
                  'tokenized_b': 'Consecutive WORDS tokens from removed descriptions, both words at least four letters; exclude token pairs in concise and per-node common/history; count output token pairs.',
                  'common': 'Common contract plus node common_text. NEXT lines excluded exactly as in frozen primary. Denominator is WORDS count. Duplicates excluded from paired primary contrast.',
                  'interpretation': 'Two descriptive robustness analyses, not replacements or independent replications. Underscores, hyphens, punctuation and line breaks become word boundaries in B.'},
              'code_sha256': runner.sha(Path(__file__).read_bytes())}
    return result


def score(args):
    runner.verify(args.run)
    _, protocol = runner.load_run(args.run)
    if protocol['study'] != 'S-016':
        raise ValueError('Only S-016 is eligible')
    bundle = runner.read_json(args.catalog)
    frozen = runner.read_json(args.inventory)
    if runner.sha(args.catalog.read_bytes()) != protocol['catalog_bundle_sha256']:
        raise ValueError('Catalog differs from study input')
    if any(frozen[k] != value for k, value in content_hashes(bundle).items()):
        raise ValueError('Source text differs from frozen sensitivity')
    if frozen['word_pattern'] != WORDS.pattern or frozen['inventories'] != derive(bundle):
        raise ValueError('Sensitivity definition differs')
    if frozen['primary_inventory'] != protocol['phrase_inventory']:
        raise ValueError('Frozen primary inventory differs')
    records = runner.read_results(args.run)
    analyses = {}
    for method, inventory in frozen['inventories'].items():
        rows = []
        for node in protocol['nodes']:
            record = records.get(node['id'], {})
            row = {k: node[k] for k in ('episode', 'condition', 'seed')}
            row.update(node_id=node['id'], kind='duplicate' if node['metadata'].get('replicate') else 'catalog',
                       status=record.get('status', 'pending'), valid=False, score=None)
            if record.get('status') == 'complete' and isinstance(record.get('text'), str):
                prose, _ = _prose_and_next(record['text'])
                words = len(WORDS.findall(prose))
                common = OPEN_CONTRACT + ' ' + node['metadata']['common_text']
                if method == 'literal_a':
                    eligible = [p for p in inventory if not literal_count(p, common)]
                    hits = {p: literal_count(p, prose) for p in eligible}
                else:
                    common_pairs, output_pairs = bigrams(common), bigrams(prose)
                    eligible = [p for p in inventory if p not in common_pairs]
                    hits = {p: output_pairs[p] for p in eligible}
                hits = {p: n for p, n in hits.items() if n}
                count = sum(hits.values())
                row.update(valid=words > 0, score=count * 1000 / words if words else None,
                           words=words, phrase_count=count, phrase_hits=hits, inventory_n=len(eligible))
            rows.append(row)
        analyses[method] = {'inventory_n': len(inventory), 'rows': rows,
                            'groups': summarize(rows),
                            'paired': paired_contrast(rows, 'full', 'concise_padded', kind='catalog')}
    return {'study': protocol['study'], 'model': protocol['model'], 'split': protocol['split'],
            'primary_unchanged': True, 'sensitivity_only': True, 'analyses': analyses,
            'inventory_sha256': runner.sha(args.inventory.read_bytes()),
            'manifest_sha256': runner.sha((args.run / 'manifest.json').read_bytes()),
            'code_sha256': runner.sha(Path(__file__).read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('freeze', 'score'):
        p = sub.add_parser(name)
        p.add_argument('--catalog', type=Path, required=True)
        p.add_argument('--out', type=Path, required=True)
        if name == 'score':
            p.add_argument('run', type=Path)
            p.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args) if args.command == 'freeze' else score(args)
    runner.write_json(runner.guard_output(args.out, ROOT), result)
    print({'out': str(args.out), 'sha256': runner.sha(args.out.read_bytes()),
           'inventories': {k: len(v) for k, v in result.get('inventories', {}).items()}})

if __name__ == '__main__':
    main()
