"""Offline S-007 compatibility for additive notebook fields and absent transport replies.
No source-system writes or changes to selection. Historical report versions remain frozen.
"""
import json, re, hashlib
from .inputs import DailyError, require
from reservoir_research.study_sequences import NOTEBOOK, RECALLED_NOTEBOOK

def notebook_exposure(text):
    start = max((text.rfind('\n\n' + heading) for heading in (NOTEBOOK, RECALLED_NOTEBOOK)))
    if start < 0:
        return dict(status='absent')
    body_start = text.find('\n', start + 2) + 1
    end = text.find('\nEnd of study notebook.', body_start)
    if not body_start or end < 0:
        return dict(status='malformed', start=start)
    try:
        value = json.loads(text[body_start:end])
        allowed = {'note', 'question', 'previous', 'recent', 'source_findings'}
        require(isinstance(value, dict) and {'note', 'question', 'previous'} <= set(value) <= allowed, "Evidence check failed: isinstance(value, dict) and {'note', 'question', 'previous'} <= set(value) <= allowed")
        recent = value.get('recent', [])
        require(isinstance(recent, list) and all((isinstance(e, dict) for e in recent)), 'Evidence check failed: isinstance(recent, list) and all((isinstance(e, dict) for e in recent))')
        for entry in [value['note'], value['question'], value['previous'], *recent]:
            if entry is None:
                continue
            require(isinstance(entry, dict) and all((isinstance(entry.get(k), str) for k in ('origin', 'response_sha256', 'text'))), "Evidence check failed: isinstance(entry, dict) and all((isinstance(entry.get(k), str) for k in ('origin', 'response_sha256', 'text')))")
            require('complete' not in entry or type(entry['complete']) is bool, "Evidence check failed: 'complete' not in entry or type(entry['complete']) is bool")
            require('prose_bytes' not in entry or (type(entry['prose_bytes']) is int and entry['prose_bytes'] >= 0), "Evidence check failed: 'prose_bytes' not in entry or (type(entry['prose_bytes']) is int and entry['prose_bytes'] >= 0)")
        if 'source_findings' in value:
            extra = value['source_findings']
            require(isinstance(extra, dict) and set(extra) == {'authored', 'supplied_locations', 'updates'}, "Evidence check failed: isinstance(extra, dict) and set(extra) == {'authored', 'supplied_locations', 'updates'}")
            require(all((isinstance(extra[k], list) for k in extra)), 'Evidence check failed: all((isinstance(extra[k], list) for k in extra))')
            require(all((isinstance(e, dict) for k in ('authored', 'supplied_locations') for e in extra[k])), "Evidence check failed: all((isinstance(e, dict) for k in ('authored', 'supplied_locations') for e in extra[k]))")
            require(all((isinstance(e, str) for e in extra['updates'])), "Evidence check failed: all((isinstance(e, str) for e in extra['updates']))")
    except (ValueError, TypeError, DailyError):
        return dict(status='malformed', start=start, end=end)
    return dict(status='included_in_submitted_user_text', start=start, end=end, sha256=hashlib.sha256(text[start:end].encode()).hexdigest(), fields=value)

def failed_wire(d, study, user_text):
    require(study['status'] == 'error', "Evidence check failed: study['status'] == 'error'")
    request_part = d['request']
    raw = request_part['text'].encode()
    require(not request_part['truncated'], "Evidence check failed: not request_part['truncated']")
    require(request_part['bytes'] == request_part['retained_bytes'] == len(raw), "Evidence check failed: request_part['bytes'] == request_part['retained_bytes'] == len(raw)")
    require(hashlib.sha256(raw).hexdigest() == request_part['sha256'], "Evidence check failed: hashlib.sha256(raw).hexdigest() == request_part['sha256']")
    request = json.loads(request_part['text'])
    require(user_text(request) == study['user_text'] and request['model'] == study['model'], "Evidence check failed: user_text(request) == study['user_text'] and request['model'] == study['model']")
    if d['source_study_failure'] == 'transport_error':
        require(d.get('response') is None, "Evidence check failed: d.get('response') is None")
        require(d.get('native_finish') is None and d.get('http_status') is None, "Evidence check failed: d.get('native_finish') is None and d.get('http_status') is None")
        require(d['error_type'] == study['error'], "Evidence check failed: d['error_type'] == study['error']")
        require(study['eval_tokens'] is None, "Evidence check failed: study['eval_tokens'] is None")
        return dict(generation_id=study['id'], failure='transport_error', request_verified=True, response_absent=True, native_finish=None, response_chars=None, error_type=d['error_type'])
    part = d['response']
    raw = part['text'].encode()
    require(not part['truncated'], "Evidence check failed: not part['truncated']")
    require(part['bytes'] == part['retained_bytes'] == len(raw), "Evidence check failed: part['bytes'] == part['retained_bytes'] == len(raw)")
    require(hashlib.sha256(raw).hexdigest() == part['sha256'], "Evidence check failed: hashlib.sha256(raw).hexdigest() == part['sha256']")
    response = json.loads(part['text'])
    require(response['done_reason'] == d['native_finish'] and response['eval_count'] == study['eval_tokens'], "Evidence check failed: response['done_reason'] == d['native_finish'] and response['eval_count'] == study['eval_tokens']")
    return dict(generation_id=study['id'], failure=d['source_study_failure'], request_verified=True, response_absent=False, native_finish=d['native_finish'], response_chars=d['raw_content_chars'])
