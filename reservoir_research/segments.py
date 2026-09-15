"""Structural channel hints for supplied journal text, with exact source spans.

An INBOX_REPLY heading may come from a pasted excerpt or a verified journal file.
This parser does not establish its origin, addressedness, delivery, or runtime
thread identity. It retains the target token literally and never acts on it.
Offsets count Python string characters, not encoded bytes.
"""

from __future__ import annotations

import re


_MARKER = re.compile(r"^ {0,3}INBOX_REPLY[ \t]+(\S+)[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def split_channels(body_text: str) -> list[dict]:
    """Return contiguous source-preserving spans, or [] for an empty string.

Every span has channel, start_offset, end_offset, text, reply_target,
marker_start_offset, and marker_end_offset. Unmarked fields are None. Reply
spans include their marker line; marker_end_offset includes its line ending.
Pre-marker text is only 'pre_reply_context', without inferred addressedness.
Marker-like lines inside backtick/tilde fences, blockquotes, inline quotes,
or indentation of four spaces are not boundaries. Targets must be one token.
"""
    if not body_text:
        return []
    markers: list[tuple[int, int, str]] = []
    offset = 0
    fence_character = ""
    fence_length = 0
    for line in body_text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        fence = _FENCE.fullmatch(content)
        if fence:
            run, rest = fence.groups()
            if fence_character:
                if run[0] == fence_character and len(run) >= fence_length and not rest.strip():
                    fence_character = ""
            elif run[0] != "`" or "`" not in rest:
                fence_character, fence_length = run[0], len(run)
        elif not fence_character and (marker := _MARKER.fullmatch(content)):
            markers.append((offset, offset + len(line), marker.group(1)))
        offset += len(line)

    def span(start, end, channel, target=None, marker_end=None):
        return {"channel": channel, "start_offset": start, "end_offset": end,
                "text": body_text[start:end], "reply_target": target,
                "marker_start_offset": start if target is not None else None,
                "marker_end_offset": marker_end}

    if not markers:
        return [span(0, len(body_text), "unlabeled_prose")]
    result = []
    if markers[0][0]:
        result.append(span(0, markers[0][0], "pre_reply_context"))
    for index, (start, marker_end, target) in enumerate(markers):
        end = markers[index + 1][0] if index + 1 < len(markers) else len(body_text)
        result.append(span(start, end, "inbox_reply", target, marker_end))
    return result
