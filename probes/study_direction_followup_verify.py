"""Verify the frozen September 16 follow-up without touching either live Being."""
import json

from study_direction_followup import OUT, load, save, sha


def verify():
    manifest = json.loads((OUT / 'capture-manifest.json').read_text())
    assert not manifest['errors']
    records = {}
    for name, expected in manifest['files'].items():
        assert sha((OUT / name).read_bytes()) == expected['sha256'], name
        rows = list(load(name))
        assert len(rows) == expected['count'], name
        records.update({row['path']: row for row in rows})

    reading = [json.loads(line) for line in (OUT / 'reading-pack.jsonl').read_text().splitlines()]
    selected = {row['name']: row for row in reading}
    astrid = json.loads((OUT / 'astrid-annotations.json').read_text())
    assert astrid['reading_pack_sha256'] == sha((OUT / 'reading-pack.jsonl').read_bytes())
    assert astrid['manifest_sha256'] == sha((OUT / 'capture-manifest.json').read_bytes())
    assert len(astrid['entries']) == 36
    assert {a['name'] for a in astrid['entries']} == {r['name'] for r in reading if r['being'] == 'astrid'}
    for annotation in astrid['entries']:
        row = selected[annotation['name']]
        assert annotation['journal_sha256'] == row['sha256']
        assert annotation['body_sha256'] == sha(row['body_text'].encode())
        for match in annotation['matches']:
            assert records[match['path']]['sha256'] == match['sha256']

    minime = json.loads((OUT / 'minime-content-annotations.json').read_text())
    for name, expected in minime['input_files_sha256'].items():
        assert sha((OUT / name).read_bytes()) == expected, name
    assert len(minime['primary_annotations']) == 20
    assert len(minime['exploratory_annotations']) == 10
    assert {a['journal_name'] for a in minime['primary_annotations']} == {r['name'] for r in reading if r['being'] == 'minime'}
    seen = set()
    for annotation in minime['primary_annotations'] + minime['exploratory_annotations']:
        path = annotation['journal_path']
        assert path not in seen
        seen.add(path)
        assert records[path]['sha256'] == annotation['journal_sha256']

    audit = json.loads((OUT / 'writing-continuation-audit.json').read_text())
    for row in audit['frozen_inputs']:
        assert sha((OUT / row['path']).read_bytes()) == row['sha256']
    log = (OUT / 'era-minime-log-tail.bin').read_text(errors='replace')
    assert len(audit['cases']) == 5
    for case in audit['cases']:
        assert records[case['generation_source']]['sha256'] == case['generation_source_sha256']
        assert records[case['job_source']]['sha256'] == case['job_source_sha256']
        assert not case['intervening_logged_choices']
        for field in ('selected_log', 'cleared_log', 'unknown_fallback_log'):
            assert case[field]['text'] in log

    joins = json.loads((OUT / 'followthrough.json').read_text())
    for being, expected in [('astrid', 47), ('minime', 55)]:
        report = joins[being]
        for key in ('studies', 'unique_response_receipt_matches', 'distinct_response_bodies', 'new_prompt', 'complete_input_in_wire'):
            assert report[key] == expected, (being, key)
        assert report['finishes'] == {'stop': expected}
    result = dict(status='passed', raw_buckets=len(manifest['files']), raw_records=len(records),
                  annotated_journals=66, exact_study_receipts=102, private_continuation_fallbacks=5,
                  limits='Checks retained identities and scoped log evidence; does not establish model understanding or exhaustive failure coverage.')
    save(OUT / 'verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
