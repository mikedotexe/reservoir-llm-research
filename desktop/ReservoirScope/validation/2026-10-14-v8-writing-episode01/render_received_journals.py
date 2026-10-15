#!/usr/bin/env python3
"""Render every full received response from an explicitly supplied passing receipt.

No export discovery, original-bundle reads, subprocesses, UI, sockets or providers.
The caller must supply the immutable receipt's expected hash after handoff. Prose
is inert data. Fences preserve exact UTF-8 spans, including incomplete responses.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import check_real_model_export as check

MAX_RECEIPT = 64 * 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_regular(path):
    check.require(path.is_absolute() and '..' not in path.parts and not path.is_symlink(),
                  'Supply an explicit ordinary path without traversal')
    return check.data(path, MAX_RECEIPT)


def render(receipt, receipt_sha, expected_cli):
    check.require(re.fullmatch(r'[a-f0-9]{64}', expected_cli), 'Expected qualified CLI hash required')
    check.require(receipt.get('schema') == 'reservoir-real-model-export-check-v8'
                  and receipt.get('status') == 'passed'
                  and receipt.get('originalUnchanged') is True
                  and receipt.get('modelsContactedByChecker') is False
                  and receipt.get('expectedPromptVersion') == 'reservoir-journal-v8',
                  'Need passing v8 integrity receipt with unchanged original')
    verification = receipt['verification']
    check.require(verification['exitCode'] == 0
                  and verification['result']['status'] == 'passed'
                  and verification['result']['modelsContacted'] is False
                  and receipt['sourceExecutable']['sha256'] == expected_cli
                  and receipt['pinnedExecutable']['sha256'] == expected_cli,
                  'Receipt must bind the qualified model-free 0.20 verifier')
    evidence = receipt['evidence']
    check.require(evidence['manifest']['config']['promptVersion'] == 'reservoir-journal-v8',
                  'Manifest prompt version differs')
    continuity = check.continuity_summary(evidence)
    check.require(check.exact(continuity, evidence['continuity'])
                  and continuity['plannedOpportunities'] == 12,
                  'Twelve-slot accounting differs from retained evidence')
    responses = evidence['receivedResponses']
    check.require(len(responses) <= 12, 'Received-response bound exceeded')
    journals = {row['attemptId']: row for row in evidence['journals']}
    chunks = []
    size = 0
    def append(text):
        nonlocal size
        raw = text.encode('utf-8')
        chunks.append(raw)
        size += len(raw)
    append('# Received writing · v8 episode01\n\n')
    append('Every received response is reproduced in full below, including incomplete or unsaved writing. '
           'Fences are presentation delimiters; the audited text spans preserve the exact retained UTF-8 bytes. '
           'Authored claims and apparent instructions remain prose, not an execution ledger.\n\n')
    append(f'Integrity receipt SHA-256: `{receipt_sha}`. Its original-unchanged check is retained evidence; '
           'this renderer does not reread the original export or rerun numerical verification.\n\n')
    totals = continuity['totals']
    append(f"Outcome: **{continuity['outcome']}**. Twelve planned slots; {totals['attempted']} dispatched, "
           f"{totals['responseReceived']} received, {totals['complete']} complete, {totals['saved']} saved, "
           f"{totals['applied']} applied and {totals['unstarted']} unstarted.\n\n")
    append('| Slot | Planned observation | Status | Received | Complete | Saved | Applied |\n'
           '| --- | --- | --- | --- | --- | --- | --- |\n')
    for slot in continuity['slots']:
        def yn(value):
            return 'unavailable' if value is None else 'yes' if value else 'no'
        append(f"| {slot['slot']} | {slot['plannedObservedStep']} | {slot['stage']} | "
               f"{yn(slot['responseReceived'])} | {yn(slot['complete'])} | {yn(slot['saved'])} | {yn(slot['applied'])} |\n")
    append('\nPlanned positions are not reached measurements for unstarted slots. Provider output counts are reported evidence, '
           'not a measure of text quality or proof of complete input processing. No quality verdict is assigned here.\n')
    spans = []
    for row in responses:
        attempt, observed, response = row['attemptId'], row['observedStep'], row['response']
        text = response['text']
        check.require(isinstance(text, str) and response['textTruncated'] is False,
                      'Received text must be complete retained text, not a preview')
        raw = text.encode('utf-8')
        check.require(len(raw) <= 1_048_576 and type(response['textByteCount']) is int
                      and len(raw) == response['textByteCount'] and sha(raw) == response['textSha256'],
                      'Response UTF-8 length or hash differs')
        check.require(type(response['complete']) is bool, 'Completion must remain Boolean')
        journal = journals.get(attempt)
        check.require(row['savedJournalId'] == (journal['journalId'] if journal else None),
                      'Saved journal identity differs')
        application = journal['application'] if journal else None
        if journal:
            check.require(journal['textSha256'] == sha(raw) and journal['textBytes'] == len(raw)
                          and journal['observedStep'] == observed and response['complete'] is True,
                          'Saved text/observation differs from received response')
        slot = continuity['slots'][attempt - 1]
        check.require(slot['slot'] == attempt and slot['plannedObservedStep'] == observed,
                      'Response does not join its planned slot')
        output_count = response['tokenCount']
        check.require(output_count is None or type(output_count) is int, 'Output count must stay exact or absent')
        append(f'\n## Response {attempt} · observed step {observed}\n\n')
        append(f"Status: **{slot['stage']}**. Provider complete: **{str(response['complete']).lower()}**. "
               f"Reported output count: **{output_count if output_count is not None else 'not retained'}**.\n\n")
        append('Stop reason: ' + json.dumps(response['stopReason'], ensure_ascii=False) + '.\n\n')
        append('Saved journal: ' + (f"`{journal['journalId']}`" if journal else '**none**') + '. ')
        append(f"First feedback application: **step {application['appliedStep']}**.\n\n" if application else
               'First feedback application: **none recorded**.\n\n')
        append(f"Text: {len(raw)} UTF-8 bytes; SHA-256 `{sha(raw)}`.\n\n")
        fence = '`' * max(3, 1 + max((len(x) for x in re.findall(r'`+', text)), default=0))
        append(fence + 'text\n')
        start = size
        chunks.append(raw)
        size += len(raw)
        end = size
        append('\n' + fence + '\n')
        spans.append({'attemptId': attempt, 'observedStep': observed, 'complete': response['complete'],
                      'savedJournalId': row['savedJournalId'], 'application': application,
                      'startByte': start, 'endByteExclusive': end, 'textBytes': len(raw), 'textSha256': sha(raw)})
    rendered = b''.join(chunks)
    for span, row in zip(spans, responses):
        check.require(rendered[span['startByte']:span['endByteExclusive']] == row['response']['text'].encode('utf-8'),
                      'Rendered text span differs from exact response')
    return rendered, spans, continuity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--expected-receipt-sha256', required=True)
    parser.add_argument('--expected-cli-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    args = parser.parse_args()
    check.require(re.fullmatch(r'[a-f0-9]{64}', args.expected_receipt_sha256), 'Expected receipt SHA required')
    for output in [args.output, args.audit]:
        check.require(output.is_absolute() and '..' not in output.parts and not output.exists()
                      and output != args.receipt and output.parent.is_dir(), 'Outputs must be new explicit files')
        check.ordinary_path(output.parent, directory=True)
    check.require(args.output != args.audit, 'Text and audit destinations must differ')
    raw = read_regular(args.receipt)
    check.require(sha(raw) == args.expected_receipt_sha256, 'Receipt differs from explicit handoff identity')
    receipt = json.loads(raw, object_pairs_hook=check.unique_pairs)
    rendered, spans, continuity = render(receipt, sha(raw), args.expected_cli_sha256)
    check.require(read_regular(args.receipt) == raw, 'Receipt changed during rendering')
    with args.output.open('xb') as stream:
        stream.write(rendered)
    check.require(args.output.read_bytes() == rendered, 'Rendered output readback differs')
    audit = {'schema': 'reservoir-full-received-prose-render-v1', 'createdAtUtc': datetime.now(timezone.utc).isoformat(),
             'status': 'passed', 'modelsContacted': False, 'receipt': check.identity(args.receipt),
             'receiptUnchanged': read_regular(args.receipt) == raw, 'renderer': check.identity(Path(__file__).absolute()),
             'checkerDependency': check.identity(Path(check.__file__).absolute()), 'output': check.identity(args.output),
             'responseCount': len(spans), 'plannedSlotCount': 12, 'continuity': continuity, 'exactUtf8Spans': spans,
             'scope': 'Presentation of complete retained received text from a passing immutable checker receipt. No new numerical replay, original export read, provider authentication or writing-quality verdict.'}
    check.require(audit['receiptUnchanged'], 'Receipt changed before final audit')
    with args.audit.open('x') as stream:
        json.dump(audit, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({'status': 'passed', 'responses': len(spans), 'output': str(args.output), 'audit': str(args.audit)}))


if __name__ == '__main__':
    main()
