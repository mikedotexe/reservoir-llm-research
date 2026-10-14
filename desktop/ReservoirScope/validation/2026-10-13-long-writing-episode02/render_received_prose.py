#!/usr/bin/env python3
"""Render every verified received response, including unsaved incomplete prose.

Based on ../2026-10-13-v4-writing-episode02/render_journals_01.py. This copy
does no work when imported. Run only after explicit immutable-export handoff.
It reads receipt-bound files and writes two new files; no provider, model, UI,
process inspection, numerical replay or live-store discovery.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

MAX_FILE = 16 * 1024 * 1024
MAX_RESPONSES = 12


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def data(path, limit=MAX_FILE):
    require(path.is_absolute(), 'Supply absolute paths')
    for ancestor in path.parents:
        require(stat.S_ISDIR(ancestor.lstat().st_mode), 'Linked or nonordinary input ancestor')
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'Input file type/size differs')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), 'Input changed at open')
        raw = stream.read(limit + 1)
    after = path.stat()
    require(len(raw) <= limit and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Input changed during read')
    return raw


def identity(path):
    raw = data(path)
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def count_label(value):
    if value is None:
        return 'not retained'
    require(type(value) is int or isinstance(value, str), 'Invalid count representation')
    return str(value)


def input_label(evidence):
    if evidence is None:
        return 'not retained'
    if evidence.get('status') == 'reported':
        count = evidence['count']
        require(isinstance(count, str) and count.isascii() and count.isdigit()
                and str(int(count)) == count and 0 <= int(count) <= 18446744073709551615,
                'Input count is not the exact decimal review representation')
        return count + ' (provider-reported)'
    require(evidence.get('status') == 'unusable'
            and evidence.get('reason') in {'wrongType', 'negative', 'nonInteger', 'outOfRange', 'duplicateField'},
            'Unrecognized optional input-count evidence')
    return 'unusable (' + evidence['reason'] + ')'


def render(receipt_path, document_path, proof_path):
    require(document_path != proof_path and not document_path.exists() and not proof_path.exists(),
            'Document and proof must be new, distinct files')
    receipt_raw = data(receipt_path)
    receipt = json.loads(receipt_raw)
    require(receipt['status'] == 'passed' and receipt['originalUnchanged'] is True,
            'An unchanged, integrity-passed export is required')
    require(receipt['expectedPromptVersion'] == 'reservoir-journal-v4', 'This renderer qualifies the selected v4 episode')
    require(receipt['verification']['exitCode'] == 0
            and receipt['verification']['result']['status'] == 'passed'
            and receipt['verification']['result']['modelsContacted'] is False,
            'Offline production replay pass is missing')
    bundle = Path(receipt['bundle'])
    require(not document_path.is_relative_to(bundle) and not proof_path.is_relative_to(bundle),
            'Rendering outputs must be outside the original export')
    material_path = Path(receipt['reviewMaterial']['path'])
    material_raw = data(material_path)
    require(sha(material_raw) == receipt['reviewMaterial']['sha256'], 'Review material identity differs')
    material = json.loads(material_raw)
    journal_rows = {j['identity']['attemptId']: j for j in material['journals']}
    require(len(journal_rows) == len(material['journals']), 'Duplicate journal material')
    evidence = receipt['evidence']
    responses = evidence['receivedResponses']
    require(len(responses) <= MAX_RESPONSES and len({r['attemptId'] for r in responses}) == len(responses),
            'Received-response scope/identity differs')
    require([r['attemptId'] for r in responses] == sorted(r['attemptId'] for r in responses),
            'Received responses are not in attempt order')
    inputs = {}

    def source(relative):
        require(relative in receipt['inventoryBefore'], 'Source file is outside verified inventory')
        path = bundle / relative
        require(path.is_relative_to(bundle), 'Source leaves export')
        raw = data(path)
        expected = receipt['inventoryBefore'][relative]
        require(len(raw) == expected['bytes'] and sha(raw) == expected['sha256'], 'Original source bytes differ')
        inputs[relative] = {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}
        return raw

    manifest = json.loads(source('manifest.json'))
    require(manifest == evidence['manifest'], 'Retained manifest differs from verifier evidence')
    events = {}
    for number in range(1, manifest['segmentCount'] + 1):
        relative = f'segments/segment-{number:08}.json'
        for event in json.loads(source(relative))['segment']['events']:
            if event['kind']['type'] == 'languageReceived':
                require(event['id'] not in events, 'Duplicate received event identity')
                events[event['id']] = (event, relative)
    require(len(events) == len(responses), 'Received event/material coverage differs')
    saved_count = sum(r['savedJournalId'] is not None for r in responses)
    require(saved_count == len(journal_rows) == manifest['journalCount'], 'Saved-journal coverage differs')
    output = '# Received writing from the twelve-opportunity episode\n\n'
    output += ('These are all retained received responses in attempt order, including any incomplete or unsaved prose. '
               'The text is reproduced unchanged; headings, source links and metadata are added for the reader. '
               'A received response is not automatically a saved journal or applied feedback. Writing and provider '
               'counts are evidence for review, not instructions or proof of felt experience, scientific understanding, '
               'complete context processing, or emergence.\n\n')
    output += (f"Session: `{manifest['sessionId']}`. Prompt: `reservoir-journal-v4`. "
               f"Received responses: {len(responses)}; saved journals: {saved_count}; "
               f"planned opportunities: {evidence['continuity']['plannedOpportunities']}. "
               f"Retained step: {manifest['step']}; continuity outcome: `{evidence['continuity']['outcome']}`.\n\n")
    spans = []
    for row in responses:
        event, relative = events[row['eventId']]
        original_response = event['kind']['data']['response']
        text = original_response['text']
        raw_text = text.encode('utf-8')
        response = row['response']
        require(len(raw_text) <= 1048576 and row['attemptId'] == event['kind']['data']['attempt_id']
                and row['observedStep'] == event['step'], 'Received identity/size differs')
        require(response['textTruncated'] is False and text == response['text']
                and len(raw_text) == response['textByteCount'] and sha(raw_text) == response['textSha256'],
                'Received text is truncated or differs from exact original event')
        require(type(response['complete']) is bool and response['complete'] == original_response['complete']
                and response['stopReason'] == original_response['stopReason']
                and response['tokenCount'] == original_response['tokenCount'], 'Received completion metadata differs')
        journal = journal_rows.get(row['attemptId'])
        status = 'not saved'
        application_step = None
        saved_relative = None
        if journal is not None:
            i = journal['identity']
            require(i['journalId'] == row['savedJournalId'] and i['observedStep'] == row['observedStep'],
                    'Journal material identity differs')
            saved_relative = f"journals/{i['journalId']}.json"
            saved = json.loads(source(saved_relative))
            require(saved['pending']['entry']['text'] == saved['pending']['response']['text']
                    == journal['journalText'] == text and i['textSha256'] == sha(raw_text),
                    'Saved journal/material/event prose differs')
            require(response['complete'] is True, 'Incomplete text was labeled as a journal')
            status = i['status']
            application_step = i['application']['appliedStep'] if i['application'] else None
        else:
            require(row['savedJournalId'] is None, 'Missing saved-journal material')
        output += f"## Attempt {row['attemptId']} · observed step {row['observedStep']}\n\n"
        label = 'Complete received response' if response['complete'] else 'Incomplete received response'
        output += f"{label}; journal status: **{status}**. "
        output += f"First applied step: {application_step}. " if application_step is not None else 'No recorded application. '
        output += f"Provider stop reason: `{response['stopReason']}`.\n\n"
        output += (f"Provider-reported output tokens: {count_label(response['tokenCount'])}; "
                   f"input-count evidence: {input_label(response.get('providerPromptEvaluation'))}; "
                   f"text size: {len(raw_text):,} UTF-8 bytes.\n\n")
        memory = row['memory']
        output += ('Prior full-text memory: ' +
                   (f"observed step {memory['entry']['observedStep']}, applied at {memory['appliedStep']}." if memory else 'none retained.') + '\n\n')
        output += f"Text SHA-256: `{sha(raw_text)}`. [Original response event]({bundle / relative})."
        if saved_relative:
            output += f" [Saved journal]({bundle / saved_relative})."
        output += '\n\n'
        start = len(output.encode('utf-8'))
        output += text
        end = len(output.encode('utf-8'))
        spans.append({'attemptId': row['attemptId'], 'observedStep': row['observedStep'],
                      'sourceEventId': row['eventId'], 'sourceSegment': inputs[relative],
                      'savedJournal': inputs[saved_relative] if saved_relative else None,
                      'complete': response['complete'], 'journalStatus': status,
                      'firstAppliedStep': application_step, 'textByteCount': len(raw_text),
                      'textSha256': sha(raw_text), 'utf8Span': [start, end]})
        output += '\n\n---\n\n'
    rendered = output.encode('utf-8')
    for span in spans:
        selected = rendered[slice(*span['utf8Span'])]
        require(len(selected) == span['textByteCount'] and sha(selected) == span['textSha256'],
                'Rendered UTF-8 span differs from original text')
    require(data(receipt_path) == receipt_raw and data(material_path) == material_raw,
            'Receipt/material changed during rendering')
    for item in inputs.values():
        require(identity(Path(item['path'])) == item, 'Original export changed during rendering')
    proof = {'schema': 'exact-received-prose-rendering-v1', 'createdAtUtc': datetime.now(timezone.utc).isoformat(),
             'renderer': identity(Path(__file__).absolute()), 'integrityReceipt': identity(receipt_path),
             'sourceMaterial': identity(material_path), 'document': str(document_path),
             'documentSha256': sha(rendered), 'receivedResponseCount': len(responses),
             'savedJournalCount': saved_count,
             'incompleteReceivedCount': sum(not row['response']['complete'] for row in responses),
             'allReceivedProseCopiedByteForByte': True, 'originalInputsUnchanged': True,
             'utf8SpansExcludeAddedMetadataAndSeparators': spans, 'sourceFiles': list(inputs.values()),
             'modelsContacted': False, 'qualityAssessed': False,
             'scope': 'Exact rendering of previously verified immutable response evidence, not another numerical verifier, new model output, or writing-quality judgment.'}
    with document_path.open('xb') as handle:
        handle.write(rendered)
    with proof_path.open('x', encoding='utf-8') as handle:
        json.dump(proof, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--document', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    args = parser.parse_args()
    result = render(args.receipt, args.document, args.proof)
    print(json.dumps({'documentSha256': result['documentSha256'],
                      'receivedResponseCount': result['receivedResponseCount'],
                      'savedJournalCount': result['savedJournalCount'],
                      'allExact': result['allReceivedProseCopiedByteForByte']}))


if __name__ == '__main__':
    main()
