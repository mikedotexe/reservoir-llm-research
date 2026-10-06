#!/usr/bin/env python3
"""Prepare the single October 6 Hold Shelf reconciliation; never publishes.

Inputs are retained board DOM metadata, pending payloads and dated research accounts.
No journal body, live source, model, board API or network is read. Decisions below
are deliberately specific to this backlog, not a general board synchronization rule.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "board/2026-10-06-reconciliation.json"
BEFORE = ROOT / "research/outputs/2026-10-06-board-reconciliation/before-dom.json"
GUIDED = "research/outputs/2026-09-16-guided-reservoir-lab/pending-board-updates.json"
DATE = "2026-10-06"
operations: dict[str, dict] = {}
source_links: dict[str, set[str]] = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_text()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def day(path):
    found = re.search(r"20\d\d-\d\d-\d\d", path)
    return found.group() if found else DATE


def refs(value):
    if isinstance(value, str):
        return [value]
    return list(value or [])


def title(path):
    for line in read(path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return Path(path).stem


def link_sources(key, paths):
    for path in paths:
        source_links.setdefault(path, set()).add(key)


def card(key, name, lane, status, body, paths, being="system", tags=(), aliases=(),
         ready=True, existing_title=None, preserve_status=False, reason=None):
    paths = list(dict.fromkeys(refs(paths)))
    key = ALIASES.get(key, key)
    old = operations.get("cards:" + key)
    if old:
        paths = list(dict.fromkeys(old["source_refs"] + paths))
        aliases = list(dict.fromkeys(old["aliases"] + list(aliases)))
    item = {
        "collection": "cards", "canonical_key": key, "aliases": list(aliases),
        "publication_ready": ready, "database_id": None,
        "existing_title_hint": existing_title, "preserve_existing_status": preserve_status,
        "preserve_existing_source": True,
        "resolution": reason or "Reconcile the final supported scoped result; preserve dated evidence and limits.",
        "source_refs": paths,
        "desired": {"title": name, "body": body, "lane": lane, "status": status,
                    "being": being.lower(), "tags": list(dict.fromkeys(["id:" + key] + list(tags))),
                    "evidence": "; ".join(paths), "source": "Mike-directed research; dated accounts linked in evidence"},
    }
    operations["cards:" + key] = item
    link_sources("cards:" + key, paths)


def log(key, name, body, paths, date=None, ready=True):
    paths = list(dict.fromkeys(refs(paths)))
    item = {"collection": "log", "canonical_key": key, "database_id": None,
            "publication_ready": ready, "aliases": [], "source_refs": paths,
            "resolution": "Append the missing historical event; never replace existing trace history.",
            "desired": {"title": name, "date": date or day(key),
                        "body": body + " Evidence: " + "; ".join(paths)}}
    operations["log:" + key] = item
    link_sources("log:" + key, paths)


def account(path, key, lane, status, body, *, being="system", name=None, tags=(),
            aliases=(), make_log=True, ready=True, existing_title=None, preserve_status=False):
    name = name or title(path)
    card(key, name, lane, status, body, [path], being, tags, aliases, ready,
         existing_title, preserve_status)
    if make_log:
        log(Path(path).stem, name, body, [path], ready=ready)


ALIASES = {
    "t-reservoir-scope-newcomer-route": "t-reservoir-scope-newcomer",
    "t-reservoir-newcomer-acceptance": "t-reservoir-scope-newcomer",
    "design-reservoir-scope-guided-route": "c-reservoir-guided-journey",
}


def load_payloads():
    """Import only explicit card/log records; narrative payloads are reviewed below."""
    for path in sorted((ROOT / "board").glob("*-pending.json")) + [ROOT / GUIDED]:
        rel = str(path.relative_to(ROOT))
        data = json.loads(path.read_text())
        if path.name == "anemone-pending.json":
            # Published receipt contains UI-generated IDs only as id: tags.
            for row in data["cards"]:
                d = row.get("data", row)
                card(row["id"], d["title"], d["lane"], d["status"], d["body"],
                     [rel] + refs(d.get("evidence")), d.get("being", "system"),
                     d.get("tags", []), reason="Already published and fully read back in September; verify existing unique tag/title and make no write.")
                operations["cards:" + row["id"]]["already_published"] = True
            for row in data.get("log", []):
                d = row.get("data", row)
                log(row.get("id", "2026-09-06-anemone"), d["title"], d["body"], [rel], "2026-09-06")
                operations["log:" + row.get("id", "2026-09-06-anemone")]["already_published"] = True
            continue
        for field in ("card", "cards", "proposed_cards", "findings"):
            records = data.get(field, [])
            if isinstance(records, dict):
                records = [records]
            for row in records:
                if not isinstance(row, dict) or "lane" not in row or "body" not in row:
                    continue
                prefix = {"finding": "f", "change": "c", "question": "q", "test": "t", "design": "d"}[row["lane"]]
                key = row.get("id") or prefix + "-" + slug(row["title"])
                name = row.get("title", key[2:].replace("-", " ").capitalize())
                evid = refs(row.get("evidence")) or refs(data.get("evidence"))
                evid += [data[k] for k in ("account", "local_account") if isinstance(data.get(k), str)]
                card(key, name, row["lane"], row["status"], row["body"],
                     [rel] + evid, row.get("being", "system"), row.get("tags", []))
        for field in ("log", "followup_log"):
            records = data.get(field, [])
            if isinstance(records, dict):
                records = [records]
            if not isinstance(records, list):
                continue
            for row in records:
                if not isinstance(row, dict) or not row.get("title") or not row.get("body"):
                    continue
                key = row.get("id", day(row.get("date", "")) + "-" + slug(row["title"]))
                log(key, row["title"], row["body"], [rel], str(row.get("date", day(key)))[:10])


def add_narrative_payloads():
    decisions = [
        ("activation-input", "t-contextual-activation-qualification", "test", "done", "Contextual activation and provider controls: bounded qualification complete", "Provider controls and termination evidence were implemented and verified live in the September 9 owning account. Offline capture parity passed; all 32 fixed and 24 free cells are accounted for and all free cells annotated. No contextual understanding advantage was established. Contextual feedback remains offline; publication does not authorize activation.", "analyses/2026-09-09-contextual-feedback-experiment.md", "system"),
        ("extended-writing", "c-optional-extended-writing", "change", "done", "Optional extended writing preserves complete draft continuity", "September 9 implementation and isolated qualification were followed by the retained verified paired rollout on September 10. The earlier awaiting-receipt text is superseded by that rollout record. Capacity and carriage are qualified; improved understanding and natural benefit are unestablished. No new rollout is performed by reconciliation.", "analyses/2026-09-09-extended-writing.md", "both"),
        ("study-context", "c-study-answer-context", "change", "done", "Carry complete study answers and preserve voluntary navigation", "Both owning main branches and live source/process identities were verified in the September 9 account. First five-minute window: two completed studies per Being, previous answers delivered and FIND to OPEN/RELATE navigation observed. No note/question update or understanding improvement established. The separate thinking trial was not promoted.", "analyses/2026-09-09-study-context-and-thinking.md", "both"),
        ("latest-five-journals", "f-latest-five-journals-20260910", "finding", "verified", "Latest five journals show navigation loops and evidence-role confusion", "The bounded ten-file September 10 survey preserves repeated page-one fixture/history exposure, Astrid's local recognition of repetition, observed peer exposure and two failed local-study-looking choices. Source delivery, quoted recalled accounts, authoring and actual dispatch remain separate. Proposals are navigation/evidence clarification and a separate revision experiment, not verified comprehension improvements.", "analyses/2026-09-10-latest-five-journals.md", "both"),
        ("evening-journal-coherence", "f-journal-coherence-20260910", "finding", "verified", "Natural journal and draft coherence exposes three interface gaps", "The September 10 bounded observation distinguishes unrelated study evidence entering fresh drafts, authored versus executed choices, and quoted visual-description origins. Public-journal-only sampling misses private drafts. These scoped observations do not infer private experience. The later September 11 repair is a separate implementation result.", "analyses/2026-09-10-evening-journal-coherence.md", "both"),
        ("journal-coherence-repairs", "c-journal-coherence-repairs", "change", "done", "Repair draft context, exact choice feedback and visual-origin labels", "September 11 qualification and paired rollout are retained: fresh drafts avoid unrelated study evidence, shared choice feedback preserves the explicit final choice, and visual descriptions retain source/age/availability. The selected natural studies exercise some choice feedback, not fresh-draft/FINISH/visual uptake. No general behavioral benefit inferred.", "analyses/2026-09-11-journal-coherence-repairs.md", "both"),
        ("astrid-small-studies", "f-astrid-small-studies-20260911", "finding", "verified", "Brief Astrid studies retain complete delivery and a persistent hypothesis", "Twenty exact-linked requests allow 4,096 tokens and stop normally at 220–535 tokens without observed omission or clipping. Saved note/question remain unchanged while earlier responses are carried. The sought warning is produced from lexical event/journal matches, not the hypothesized numerical aggregator. The source of the saved question remains unknown.", "analyses/2026-09-11-astrid-small-studies.md", "astrid"),
        ("minime-study-survey", "f-minime-study-survey-20260915", "finding", "verified", "Minime's latest hundred studies traverse maps with no fresh code", "The bounded September 15 cohort contains 99 maps and one EOF notice, exact generation/input/journal links, normal stops at 121–312 tokens under 4,096, and matching completed jobs for all 99 next-choice pairs. Note/question persist and supplied OPEN choices remain unchosen. The independent source audit is our evidence, not fresh code delivered in this cohort. No causal or general comprehension score.", "analyses/2026-09-15-minime-study-survey.md", "minime"),
        ("study-navigation-release", "c-study-compact-navigation", "change", "done", "Compact study navigation, exact recovery and optional evidence choices", "September 15 owning implementation commits and paired graceful deployments were verified. The closed natural window retains two Astrid and four Minime receipts and two selected deliveries per Being, but zero strictly preparation-timing-qualified trials. New interface delivery is established; general or causal understanding improvement is not.", "analyses/2026-09-15-study-navigation-release.md", "both"),
        ("study-navigation-revision", "c-study-chosen-navigation-and-evidence-roles", "change", "done", "Preserve chosen study navigation and distinguish lexical evidence roles", "The September 10 paired graceful rollout is verified in its owning account. One first new-process study per Being establishes selected request/evidence carriage, not improved understanding. The isolated six-cell revision pilot retains five nonempty EOS responses, one admission refusal, one complete matched seed and no demonstrated central correction. Generated choices were not executed.", "analyses/2026-09-10-study-navigation-live.md", "both"),
        ("study-evidence-order", "t-study-evidence-order", "test", "done", "Fresh-source order does not repair the retained account in this pilot", "Eight planned outcomes: seven returned EOS answers, one admission refusal and three complete pairs. All seven retain the unsupported proxy interpretation; two proposed notes and one proposed resolution also preserve it. The unpaired real-identifier choice is not an ordering comparison. Isolated historical-input replay, not live Being outcomes; no central correction demonstrated.", "analyses/2026-09-10-study-evidence-order.md", "system"),
        ("study-question-framing", "t-study-question-framing", "test", "done", "Neutral wording and supported controls preserve different supplied accounts", "Eight isolated responses preserve the mistaken retained account in all four retained cells and the central supported distinction in all four supported cells. Smaller errors and interpretive sensitivity remain: original and context-sensitive codes are both retained. This is not a whole-answer score or new learning. Proposed notes/choices were never executed.", "analyses/2026-09-10-study-question-framing.md", "system"),
        ("study-source-first", "t-study-source-first", "test", "done", "Source-first reading and carried notes do not establish central repair", "Both initial readings reject a production relationship but contain ambiguity or specific error. All four retained-account final responses preserve the unsupported production story; all four supported-account finals retain the central distinction with smaller errors. Carriage has no consistent advantage. Proposed notes/choices remain data; one historical Minime episode with isolated backend substitution, not live journal outcomes.", "analyses/2026-09-10-study-source-first.md", "system"),
        ("study-claim-evidence", "t-study-claim-evidence", "test", "done", "Evidence-linked claims preserve supported material without repairing the retained story", "Neither retained-account pair repairs the unsupported fixture/production pulse story; all four supported-account responses preserve central distinctions with smaller ambiguities. The pending-fields question already appeared in the research-authored control, so it is not evidence of independent discovery. Exact sources, proposed notes and choices remain separate; no live writes or comprehension gain claimed.", "analyses/2026-09-10-study-claim-evidence.md", "system"),
    ]
    for stem, key, lane, status, name, body, account_path, being in decisions:
        payload = "board/" + stem + "-pending.json"
        d = json.loads(read(payload))
        paths = [payload, account_path]
        paths += [d[k] for k in ("account", "local_account", "completed_report") if isinstance(d.get(k), str)]
        paths += refs(d.get("accounts"))
        card(key, name, lane, status, body, paths, being, ["research-reconciliation"])
        log(Path(account_path).stem, name, body, paths, day(account_path))

    # Explicit recommendations remain proposals; later related work is cross-linked.
    card("c-study-cue-origin", "Expose the lexical origin of study interpretation warnings", "change", "open",
         "September 11 recommendation: identify the cue as a text-pattern interpretation warning and make the matched source available. No new implementation is established by the small-study survey.",
         ["board/astrid-small-studies-pending.json", "analyses/2026-09-11-astrid-small-studies.md"], "astrid")
    card("q-study-evidence-grounded-synthesis", "Make optional source-grounded synthesis and coherent spans available", "question", "open",
         "September 11 recommendation: compare the actual producer with the saved hypothesis while retaining authored notes, coherent source spans and voluntary synthesis/finish choices. Later source-context, direction and page-boundary work supplies related interface mechanisms, not demonstrated correction or proof that this research question is answered.",
         ["board/astrid-small-studies-pending.json", "analyses/2026-09-11-astrid-small-studies.md", "analyses/2026-09-16-study-direction.md", "analyses/2026-09-17-study-interface-repairs.md"], "both")
    card("t-study-pending-intent-consumer-path", "Trace pending intent through consumer, delivery and continuation evidence", "test", "open",
         "Final September 10 follow-up proposal: source-grounded consumer-path integration test joining pending intent, provider delivery, Reader checkpoint and artifact/continuation evidence. The question originated in a research-authored supported control. No patch or additional experiment is implied by board publication.",
         ["board/study-claim-evidence-pending.json", "analyses/2026-09-10-study-claim-evidence.md"], "system")


def add_accounts():
    rows = [
        ("2026-09-06-astrid-reading-letter-return-source-trace", "t-reading-letter-return-source-trace", "test", "open", "Source trace completed; isolated bookmark, letter-delivery and voluntary-return episode remains unrun. The audit distinguishes cursor persistence, receipt versus delivery, final-request composition and reservoir attribution. Preserve later reading-feedback completions.", "astrid", "The reading episode: bookmark, letter, return"),
        ("2026-09-06-reservoir-3d-metric-contract", "f-reservoir-unsorted-rayleigh-estimates", "finding", "verified", "The September 6 source audit identifies sensory spectral columns as unsorted Rayleigh estimates. A principal-axis covariance ellipsoid would overstate that capture. This is a dated metric-contract finding, not an assertion about a later implementation.", "system", None),
        ("2026-09-09-self-study-overnight", "t-self-study-overnight", "test", "done", "Completed the frozen overnight self-study observation and retained its corrections, exact source/input/journal links and proposal boundaries. Journal room and navigation repairs were assessed separately in the later release/startup account; no general understanding gain follows from delivery.", "both", None),
        ("2026-09-09-journal-room-live", "c-journal-room-and-navigation", "change", "done", "September 9 paired release raised source-study ceilings to 4,096 and repaired navigation/recovery while preserving authored limits. First natural window contains two verified new-process Minime studies with 8,619 new bytes and zero repeated bytes; no Astrid study exposure. Both outputs remained below 768 tokens, so allowance delivery is established, not an effect of extra room.", "both", None),
        ("2026-09-09-study-inquiries-live", "c-study-inquiries-live", "change", "done", "The dated account preserves the optional study-inquiry implementation, qualification, paired activation and natural-window limits. Authored notes/questions and independent source evidence remain distinct. This is a historical rollout record, not a fresh deployment or causal benefit claim.", "both", None),
        ("2026-09-10-study-evidence-revision", "t-study-evidence-revision", "test", "done", "Six frozen cells retain five nonempty model-EOS responses, one admission refusal and one complete matched seed. Partial fixture-role uptake occurs at one seed; central correction is not demonstrated. Source-specific detail, optional note omission and proposed navigation are separate from understanding and live delivery.", "system", None),
        ("2026-09-15-git-stabilization", "t-research-git-stabilization-20260915", "test", "done", "Completed repository integration, preserved historical probes and recorded source-only qualification on September 15. Maintenance evidence only; this does not establish a new Being outcome, remote publication at that time, or later release acceptance.", "system", None),
        ("2026-09-16-study-direction", "c-study-source-hints-and-checkin", "change", "done", "September 16 source-hint/provenance repair and optional source-first check-in were implemented, qualified and verified live. Four Astrid inputs and no Minime study exposures occur in the fixed window; two Astrid responses selected, zero strict preparation-timing-qualified trials. Delivery works but no authored correction or causal understanding gain is established.", "both", None),
        ("2026-09-16-study-direction-followup", "f-study-direction-four-hour-followup", "finding", "verified", "The bounded four-hour follow-up records grounded local reading alongside persistent premises, page-split identifiers, full finding-store feedback gaps and private CONTINUE mismatch. Sixty-six distinct journals were close-read, including an explicitly exploratory private/nonstudy supplement. The September 17 repairs are a separate implementation; durable correction remains unestablished.", "both", None),
        ("2026-09-17-study-interface-repairs", "c-study-interface-repairs", "change", "done", "September 17 repaired eligible private CONTINUE normalization, source-page line boundaries and persistent finding-save/capacity feedback. Qualification and final staged rollout are retained, including failed first-stage receipts and recovery. Two Minime study inputs, no Astrid or private-writing exposure in the frozen natural window. Working delivery does not establish comprehension, durable correction or natural private-continuation uptake.", "both", None),
    ]
    for stem, key, lane, status, body, being, existing in rows:
        path = "analyses/" + stem + ".md"
        account(path, key, lane, status, body, being=being, existing_title=existing,
                preserve_status=bool(existing))
        if existing:
            operations["cards:"+key]["desired"]["title"]=existing
            operations["cards:"+key]["append_to_existing_body"]=True
    p = "analyses/2026-09-06-reservoir-live-state-readiness.md"
    card("t-reservoir-observatory", "Build a native 3D observatory for reservoir state and regulation", "test", "done",
         "Historical supporting audit: activation v1 supports per-node observations and co-published fill/stage; exact state-step, effective-leak and controller synchronization belonged to a separate producer proposal. Preserve the completed observatory card and its subsequent release history.",
         [p], existing_title="Build a native 3D observatory for reservoir state and regulation", preserve_status=True)
    operations["cards:t-reservoir-observatory"]["append_to_existing_body"] = True

    p = "analyses/2026-09-07-afterimage-research-readiness.md"
    card("t-afterimage-trace", "Follow an Afterimage from physical trace to later use", "test", "done", "", [p, "board/afterimage-trace.json"], existing_title="Follow an Afterimage from physical trace to later use")
    operations["cards:t-afterimage-trace"]["already_published"] = True
    log("2026-09-07-afterimage-trace", "Build and read the first Afterimage account", "", [p, "board/afterimage-trace.json"], "2026-09-07")
    operations["log:2026-09-07-afterimage-trace"]["already_published"] = True

    # Historical negative model qualifications are complete, not requests to retry.
    log("2026-09-09-activation-input-and-provider-knobs", "Audit contextual input and effective provider controls", "Preserved the initial source audit and proposal. Later completed provider qualification and bounded contextual experiment supersede the early unrun state without changing its historical date.", ["analyses/2026-09-09-activation-input-and-provider-knobs.md", "board/activation-input-pending.json"], "2026-09-09")


def add_daily():
    descriptions = {
        1: "Broader Astrid-code exposure is verified in the original daily window; Minime implementation exposure remains unobserved within that verified frame. Exact source and writing links support the selected reading, not a general fidelity gain.",
        2: "The selected supplied queue loop contradicts a single-item claim. Source and authored writing evidence remain distinct; verification applies to the frozen window and selected sample, not general comprehension.",
        3: "The original day-3 window is verified with its preserved sample, source-ownership distinctions and coverage limits. Later catch-up replays do not create a new observation window or a causal fidelity estimate.",
        4: "The original day-4 window is verified; preserve its sampled interpretation, unresolved inference and exact coverage limits. Daily verification is distinct from correctness of every authored claim.",
        5: "The original day-5 window is verified. Preserve the selected partial comment/call revision alongside persistent recovery inference and the source/coverage boundaries; no generalized fidelity improvement is established.",
        6: "A supplied path correction is repeatedly misquoted, then chosen successfully. The separately reported 175-request recovery sequence remains distinct from the prespecified daily close reading. Preserve the fixed window, scope and causality limits.",
        7: "Verified bounded delivery coexists with carried-map misattribution and a distinct September 15 release era. Exact source-return evidence supports the local account, not a general fidelity or comprehension score.",
        8: "All 407 completed studies have verified inputs/full journals; source supports a generic handler/filter explanation while the specific event/state-updater premise remains unestablished. Ten selected spans, three failed attempts and no Minime-repository page remain explicit.",
        9: "All 280 completed studies have exact input/full-journal links. The fixed sample preserves a correct Kernel definition location, a byte/line extent error and an unlocated guard hypothesis. All 221 page opportunities concern Astrid; no Minime-repository page.",
        10: "The fixed sample corrects an unavailable underscore path; a separately declared adjacent follow-up verifies delivery of the corrected source. Architectural truth, saved durable correction and general fidelity gain remain unestablished. The verified ledger reaches 5,088 IDs through September 18 18:34 UTC.",
    }
    keys = {7:"f-s007-day7-navigation-and-source-return",8:"f-source-study-fidelity-day8",9:"f-source-study-fidelity-day9",10:"f-s007-day10-navigation-recovery"}
    for n, body in descriptions.items():
        paths = sorted((ROOT / "analyses").glob(f"*-source-study-fidelity-day{n}.md"))
        assert len(paths) == 1, n
        p = str(paths[0].relative_to(ROOT))
        key = keys.get(n, f"f-s007-day{n}-bounded-fidelity")
        account(p, key, "finding", "verified", body, being="minime", tags=["S-007", "source-study", "provenance"])
        if n in (8, 9, 10):
            tkey = f"t-source-study-fidelity-day{n}" if n < 10 else "t-s007-day10-offline-replay"
            card(tkey, f"S-007 day {n}: retained evidence and offline replay", "test", "verified", "The dated packet verifies preserved input and journal bindings, fixed selection, independent release/prompt context where required, historical lineage and offline replay. This checks reproduction and scope; it does not verify every semantic claim or infer general improvement.", [p], tags=["S-007", "offline-replay"])
    account("analyses/2026-09-13-source-study-fidelity-catchup.md", "t-s007-days3-5-catchup", "test", "done", "Recovered and replayed the original windows 3–5. Preserve verified exposure, persistent recovery inference and partial comment/call revision. This catch-up adds no new daily window and does not duplicate the dated daily findings.", tags=["S-007"])
    account("analyses/2026-09-15-source-study-fidelity-week1.md", "f-s007-week1-access-and-fidelity", "finding", "verified", "Seven preserved windows show verified source exposure and selected local revisions alongside continuing attribution/navigation errors and no observed Minime-repository page. No generalized or causal fidelity gain is established.", being="minime", tags=["S-007", "longitudinal"])
    p = "analyses/2026-09-19-source-study-fidelity-day11.md"
    card("f-s007-day11-lifecycle-scope", "S-007 day 11: bounded reading retained, final verification blocked", "finding", "parked", "The frozen window retains locally supported mechanism reading and unestablished readiness/policy generalization. Historical restart/deployment evidence for the new Minime process remains missing; final release-era/packet verification is blocked. This daily window is not verified and the ledger remains 5,088. Resume the same frozen packet when the owning historical receipt is found.", [p, "research/NOW.md"], "minime", ["S-007", "verification-blocked"])
    card("t-s007-day11-host-release", "S-007 day 11: recover the historical host-release witness", "test", "parked", "Unpark only on retained historical restart/deployment evidence binding the new Minime PID to the actual startup inputs, then verify the same frozen window and first-three sample. Current startup status cannot replace the historical witness. Four September 20–23 rechecks left the blocker and 5,088-ID ledger unchanged. Do not widen or recollect the window.", [p, "analyses/2026-10-06-git-tidy-and-record-status.md"], tags=["S-007", "verification-blocked"])
    log(Path(p).stem, "Retain S-007 day eleven with an explicit host-release blocker", "Retained the frozen window and selected reading without claiming final verification or advancing the 5,088-ID ledger. Historical host-release evidence remains required; partial prompt/bridge bindings and the original rejection are preserved.", [p], "2026-09-19")
    # This already-completed initial study is deliberately not reopened.
    card("t-source-study-fidelity", "Track Minime self-study fidelity across the source-reader repair", "test", "done", "", ["board/source-study-fidelity.json"], existing_title="Track Minime self-study fidelity across the source-reader repair")
    operations["cards:t-source-study-fidelity"]["already_published"] = True


def add_release():
    p = "analyses/2026-09-16-portable-reservoir-lab.md"
    card("c-portable-reservoir-lab", "Build a portable reservoir-to-journal lab", "change", "done", "Delivered the September 16 0.12 portable foundation: local A–H workflow, storage recovery and verifiable observation comparison. Later 0.13/0.14 candidates extend it; human newcomer acceptance is separate and still pending.", [p], tags=["reservoir-scope"])
    card("t-portable-reservoir-lab-disconnected", "Verify copied portable lab storage and replay offline", "test", "verified", "The 0.12 copied app/runner was checked with network and original paths denied: local save/reopen/export, v1 compatibility and package identity. This dated coverage does not replace later presented-app or human acceptance checks.", [p], tags=["reservoir-scope"])
    card("q-journal-observation-access", "Does indexed reservoir state change supportable journal claims?", "question", "open", "Demonstrations exist. Freeze a claim rubric and replicated study before estimating an effect; transport, different prose and synthetic controller behavior do not establish better writing or understanding.", [p], tags=["S-009"])
    log(Path(p).stem, "Deliver the portable reservoir lab foundation", "Delivered the separate synthetic research app, preserved model-preparation attempts and kept S-007/live systems independent. Human acceptance was not established.", [p])

    p = "analyses/2026-09-16-reservoir-scope-product-review.md"
    card("c-reservoir-scope-replay-step", "Step through an opened recording without starting a new experiment", "change", "done", "The product-review proposal was implemented by the later guided release. Step advances an opened recording cursor while a fresh experiment starts explicitly. The E boundary at journal 30 / feedback 31 is independently verified; no new model call or duplicate library entry is inferred.", [p,"analyses/2026-09-16-guided-reservoir-lab.md",GUIDED])
    link_sources("cards:c-reservoir-guided-journey", [p])
    link_sources("cards:t-reservoir-scope-newcomer", [p])
    card("q-reservoir-scope-example-contrast", "Specify observable active-state and controller contrasts", "question", "done", "The original product-review design request was answered by separate active-state scripted examples and a bounded 600-step controller example in the guided release. Later model retry remains partial, and short-output qualification failed; no model writing-quality gain or target guarantee follows.", [p,"analyses/2026-09-16-guided-reservoir-lab.md","analyses/2026-09-16-active-observation-retry.md"])
    log(Path(p).stem, "Review the portable lab and define the guided route", "The source and recorded-evidence review proposed cursor-safe replay, a guided route, contrasting examples and actual newcomer acceptance. Later implementation is linked separately; this review alone did not implement them.", [p])

    p = "analyses/2026-09-16-active-observation-retry.md"
    account(p, "t-reservoir-active-observation-retry", "test", "done", "One separately authorized retry verified the owned model identity and produced four requests, three saved journals and an incomplete response at 256 tokens, stopping at step 60. The failed-but-verifiable partial comparison is preserved and exposed by 0.13.1. The owned temporary service was stopped; no fresh retry follows from publication.")
    card("c-reservoir-active-partial-replay", "Expose the partial active-state recording and its failure", "change", "done", "Reservoir Scope 0.13.1 bundles the exact partial 60-step run, separates preparation history and request failure, and verifies replay offline. Partial output is not a completed controlled model comparison.", [p])

    p = "analyses/2026-09-17-reservoir-scope-014-delivery.md"
    release_cards = [
        ("t-reservoir-scope-014-candidate", "Reservoir Scope 0.14 build 19: delivered test candidate", "test", "verified", "Build 19 delivered from tag reservoir-scope-v0.14.0 with matching runner, resource/signature/identity checks and copied offline storage. Presentation aggregate retained its AX failure, full presented traversal remains incomplete and human acceptance is pending. Historical delivery verification is not an all-checks-passed acceptance claim."),
        ("t-maintained-daily-parity", "Verify maintained daily pipeline parity before migration", "test", "verified", "Day-9 report, verification and claim checks reproduced byte-for-byte before migration. Fixed sampling, schedule and ledger were preserved; migration itself captured no new data and advanced no ledger."),
        ("t-private-research-recovery", "Verify the initial private research snapshot and isolated restore", "test", "verified", "September 17 initial full private snapshot was hash-verified and restored with original paths/network unavailable; ten historical replays passed. This records that initial receipt only. Availability of Mike's old backup and completion of the later post-follow-up backup are separate claims."),
        ("t-short-output-qualification", "Short-output qualification closes negatively", "test", "done", "S-009 stopped at the first paired cell after two requests. The candidate completed with 25 words and multiple copied measurements, failing the 24-word bound. Both responses retained; owned local service stopped. No prompt v3 or additional recording followed."),
    ]
    for key,name,lane,status,body in release_cards:
        card(key,name,lane,status,body,[p,"research/CURRENT-RELEASE.md"],tags=["reservoir-scope"])
    card("t-reservoir-scope-newcomer", "Complete the actual offline newcomer walkthrough", "test", "open", "Reservoir Scope 0.14 build 19 remains a test candidate. The untouched participant kit was prepared, but no newcomer acceptance result exists. Use the seven-task NEWCOMER-WORKSHEET and separate reviewed-case follow-on; record exact identity, answers/evidence, assistance and time. Agent checks and renders are not human acceptance. This closeout does not perform that session.", [p,"native/ReservoirScope/docs/NEWCOMER-WORKSHEET.md",GUIDED], aliases=["t-reservoir-scope-newcomer-route","t-reservoir-newcomer-acceptance"],tags=["reservoir-scope","human-acceptance"])
    log("2026-09-17-reservoir-scope-014-delivery", "Deliver offline research candidate and preserve bounded outcomes", "Delivered 0.14 build 19, preserved source/private evidence, qualified daily parity, registered bounded studies and retained S-009's negative result. AX traversal and human acceptance remained pending. This is the September 17 event; Git publication happened later on October 6.", [p])


def add_triple():
    a = "exercises/2026-09-06-triple-reservoir-refinements.md"
    b = "exercises/2026-09-06-triple-reservoir-corrections-and-next-tests.md"
    c = "exercises/2026-09-06-session-close-and-board-brief.md"
    rows = [
        ("t-coupled-checkin-event-survival","Establish effective event survival through checkout and check-in","test","astrid","Isolated deterministic schedule: prove effective injection before check-in, inspect the checked-in result, and include an after-check-in positive control, tolerances and a denominator. Distinguish forced-schedule loss from unmeasured live frequency."),
        ("c-coupling-applied-trace","Specify within-turn applied coupling controls and prompt joins","change","astrid","Prepare a proposal extending generation records with applied controls and durable prompt joins. Existing final readouts do not establish a within-turn trajectory. No live implementation is authorized by this historical card."),
        ("t-anchor-by-coupling-ablation","Separate anchor copying, coupling and factual continuity","test","astrid","Cross anchor absent/present/factual replacement with coupling off/current/fixed matched controls and y2-only neutralization. Hold remaining prompt, backend, gain, seeds and token-history replay fixed. Score copying separately from accurate activity resumption."),
        ("t-manner-persistence-and-fade","Measure event response, persistence and return beyond timers","test","astrid","Different pasts with identical present prompts; compare elapsed time and intervening-token clocks, output attenuation and future-state effects. Define neutrality, refresh, ongoing-event and resume behavior; use held-out histories and timer/smoother controls. No subjective mood or depth advantage is presumed."),
        ("t-sensory-shape-versus-energy","Separate sensory energy, diversity, freshness and retained shape","test","both","Replay zero input, repeated direction, matched-energy variation, lower amplitude and stale timestamps from equal state; stratify controller/scaffold modes. Record raw/admitted energy, lambda1, full trace, reported-mode sum and freshness. Do not infer scarcity from normalized shape alone."),
        ("c-input-delivery-ledger","Specify capture-to-retention evidence for incoming signals","change","both","Research proposal for capture, receipt, acceptance, application and retention links, including energy and freshness. Locate demonstrated loss at its actual hop; absent evidence remains unknown. No claim of complete deployed instrumentation."),
        ("t-manner-null-ladder","Compare useful history with constant, shuffled and simpler dynamics","test","astrid","Compare no coupling, constant/history-independent, smoothing, one-reservoir and triple-reservoir controls at matched behavioral influence and explicit fading. Freeze budgets and held-out evaluations; nonzero order or interaction alone is not reservoir/depth advantage."),
        ("t-contextual-input-matched","Compare contextual representations under fair calibration","test","astrid","After delivery/replay validity, distinguish frozen-readout compatibility from equal-budget refitting with matched norm, cadence, data, capacity and tuning budget. Retain random/history-independent and smoothing controls. Later bounded contextual experiment did not establish an understanding advantage; this broader matched-representation design is not silently completed by it."),
        ("q-fade-expression-or-trace","Choose what fades: outward influence, stored distinction, or both","question","astrid","Specify neutral behavior, clock refresh, ongoing events and reopening/resume. Faster outward settling is a candidate, not a deployed feature or a proven mood model; it may still affect future hidden state through generated tokens."),
        ("q-sensory-observer-purpose","Distinguish current input, remembered structure and regulated state","question","both","Declare the observer's target and label freshness, estimator mode and restoration history. Preserve unknown provenance rather than treating retained shape or estimator maintenance as an environmental event."),
        ("t-glyph-freshness-semantics","Test fresh quiet, missing input and held shape as different encodings","test","both","Verify exact model delivery and interpretation for fresh quiet, absent/stale observation and held historical geometry as separate cases. This September 6 test remains proposed unless later evidence specifically completes it."),
        ("q-paper-mechanistic-audit","Map mechanisms to evidence and missing causal tests","question","both","Prepare a claim/evidence matrix and methods outline identifying independently supported mechanisms and the smallest missing causal/incidence tests. Observer-impact claims remain distinct from mechanism demonstrations; a paper is not a prerequisite for every bounded study."),
        ("t-history-beyond-recency","Test order and slow context beyond timer and smoother baselines","test","astrid","Coordinate with the manner test; use matched held-out histories, order swaps, slow-history interactions and capacity/cost-controlled single/triple comparisons. A nonzero interaction does not establish depth advantage."),
        ("c-provenance-backed-review","Specify a steward-side evidence-backed review","change","both","Start with recorded backend, source/admission times, estimator mode, handle, action completion and event-survival evidence. Mark unavailable fields explicitly. Any Being-facing wording is a separate proposed prompt intervention, not authorized by board publication."),
    ]
    for key,name,lane,being,body in rows:
        card(key,name,lane,"open",body,[a,b,c],being,["triple-reservoir","historical-proposal"])
    ledger=operations.pop("cards:c-input-delivery-ledger")
    for keys in source_links.values():
        if "cards:c-input-delivery-ledger" in keys:
            keys.remove("cards:c-input-delivery-ledger")
            keys.add("cards:c-reservoir-observatory-telemetry")
    card("c-reservoir-observatory-telemetry", "Propose coherent state, leak and controller evidence for the observatory", "change", "done",
         "The September 6 input-delivery-ledger proposal is covered by the completed input-lineage/regulator proposal and checker already recorded here. Preserve done as proposal completion; producer implementation, actual capture coverage and deployment remain separate. Historical correction: missing provenance stays unknown and normalized shape is not raw/admitted energy.",
         [a,b,c,"proposals/2026-09-07-input-lineage-and-regulator-trace.md"],"both",aliases=["c-input-delivery-ledger"],existing_title="Propose coherent state, leak and controller evidence for the observatory",preserve_status=True)
    operations["cards:c-reservoir-observatory-telemetry"]["append_to_existing_body"]=True
    for key,name,being,body in [
        ("f-reuse-control-sign","The inspected reuse-control sign favors or suppresses reuse","astrid","In the September 6 inspected implementation, positive y2 suppresses recent-token reuse and negative y2 favors it. This source statement does not establish the controls applied in a particular historical generation."),
        ("f-coupling-log-is-final-only","Final coupling logs do not establish within-turn trajectories","astrid","The inspected rolling journal retained final readouts and gain, not their complete within-turn trajectory. Preserve that historical recording scope; later mechanisms require separate receipts."),
        ("f-checkin-overwrites-handle-state","The inspected check-in overwrites state without a caller-version guard","system","The September 6 source review identifies replacement without a caller version guard in the inspected API. Actual lost-event frequency is unknown; the deterministic event-survival test remains separate."),
        ("f-sensory-shape-is-not-input-energy","Normalized sensory shape does not measure absolute incoming energy","minime","Normalized share and entropy alone cannot establish scarcity. Trace normalization, scaffold mode, retained state and label-derived scarcity require distinct accounting. Isotropic second moments do not establish absence of memory."),
    ]:
        card(key,name,"finding","verified",body,[a,b,c],being,["triple-reservoir","source-audit"])
    # Existing completed instrumentation cards keep completion; add the historical
    # qualification rather than reopening them from a September 6 proposal.
    for key,name in [("c-persist-prompts","M1: Persist the exact prompt for every generation, both beings, every lane"),("c-log-backend-per-generation","Log the backend and model for every generation (M1 extension)")]:
        card(key,name,"change","done","September 6 research qualification: exact prompt/backend records and completed action outcomes are distinct; inventory actual coverage and keep unavailable fields explicit. Later completion evidence on this card remains authoritative for its implemented scope.",[c],"both",existing_title=name,preserve_status=True)
        operations["cards:"+key]["append_to_existing_body"] = True
    card("t-sensory-freshness","Why do streaming clients read as stale beyond the engine window?","test","open","September 6 follow-up: trace capture to receipt to admission in one defined episode, with fresh quiet, missing observation and retained-field cases. Preserve unknown hops and avoid extrapolating corpus-wide inherited fractions.",[c,b],"both",existing_title="Why do streaming clients read as stale beyond the engine window?",preserve_status=True)
    operations["cards:t-sensory-freshness"]["append_to_existing_body"] = True
    for path, name in [(a,"Source-check proposed triple-reservoir refinements"),(b,"Retain collaborator corrections and sharpen next tests"),(c,"Close the session with an audit thesis and a bounded execution queue")]:
        log(Path(path).stem,name,"Preserved the dated source review and corrections; refined proposed tests and finish lines without performing the experiments or changing live systems. Existing completed work is preserved and no proposed benefit is treated as verified.",[path],"2026-09-06")


def add_current_holds():
    for key,name,body,paths in [
        ("q-flywheel-consecutive-followthrough","Close the frozen S-006 consecutive-review follow-up","Final October 6 closure outcome pending the owning closeout account. Do not publish the stale September 17 active-state text as a present observation.",["research/studies/S-006-consecutive-review-protocol.md","analyses/2026-09-17-bounded-followups-status.md"]),
        ("q-durable-correction-followthrough","Close the frozen S-008 durable-correction follow-up","Final October 6 closure outcome pending the owning closeout account. Preserve the two cases and missing/unavailable opportunities; no durable benefit is inferred.",["research/studies/S-008-durable-correction-protocol.md","analyses/2026-09-17-bounded-followups-status.md"]),
        ("c-question-geometry-bookmarks","Integrate the reviewed offline geometry-bookmark candidate","Final reviewed integration and qualification outcome pending the owning geometry account. Existing 0.14 candidate identity and human acceptance remain separate. No paired live rollout or Being-facing delivery is authorized here.",["research/inquiries/2026-09-21-geometry-bookmarks.md"]),
        ("t-research-closeout-20261006","Close bounded research and prepare reviewed Git integration","Closeout remains underway. Final done state requires completed bounded accounts, reviewed geometry integration, board reconciliation receipts and final verification. Root owns this existing active card and its publication receipt.",[]),
    ]:
        card(key,name,"question" if key.startswith("q-") else "change" if key.startswith("c-") else "test","active",body,paths,ready=False,tags=["research-closeout"])


def complete_bounded_followups():
    path="analyses/2026-10-06-bounded-followups-closeout.md"
    records=[
        ("q-flywheel-consecutive-followthrough",
         "Close the frozen S-006 consecutive-review follow-up",
         "The one authorized October 6 historical recovery and bounded administrative closeout are complete with incomplete evidence. The direct controller inventory contained 681 names; its latest matching name predates the registered intake. Provider enumeration hit the original 20,000-name cap. Zero source-content bytes, eligible packets or provider bodies were read. Planned historical coverage is not established, the eligible-run count remains unknown, and operational benefit is unmeasured. This is not an empirical negative result. The broader S-006 question remains open; no retry, new model call or live change follows.",
         ["research/studies/S-006-consecutive-review-protocol.md","research/studies/S-006-historical-recovery-addendum.md",path]),
        ("q-durable-correction-followthrough",
         "Close the frozen S-008 durable-correction follow-up",
         "The retained-slice assessment and bounded closeout are complete; planned-window coverage is incomplete. The only accepted in-intake daily packet retains 294 generations and 281 observed notebook versions. Both cases have no eligible exposure in that slice. Fourteen changed-revision candidates are ineligible under the unchanged full-anchor rule: the exact translated anchor crosses separate delivered pages, which cannot be combined. Day11 remains blocked and later coverage absent. Local correction, saved correction and later accurate use remain unresolved; zero eligible exposure in this slice is not a full-period negative. The broader S-008 question remains open.",
         ["research/studies/S-008-durable-correction-protocol.md",path]),
    ]
    for key,name,body,paths in records:
        card(key,name,"question","done",body,paths,tags=["research-closeout","bounded-extension-closed","coverage-incomplete"],
             reason="Done denotes the completed bounded extension and administrative account, not an answered broader empirical question.")
    log("2026-10-06-bounded-followups-closeout","Close bounded follow-ups with incomplete historical coverage",
        "Completed one preregistered S-006 recovery and the explicit-input S-006/S-008 closeout. S-006 recovered no eligible content from the retained inventory and leaves historical opportunity unknown. S-008 adjudicated all 14 changed-revision candidates as ineligible under the unchanged full-anchor rule; the accepted slice has no eligible exposure, with full-period coverage incomplete. The broader questions remain open. Forty-nine fixture tests passed, explicit-input isolated replay reproduced the report byte-identically, and 45 frozen originals remained unchanged. S-007's blocked day11 and 5,088-ID ledger are preserved; S-009 remains a completed negative qualification. No new model call, service change or induced study.",
        [path],DATE)


def complete_geometry_and_prepare_closeout():
    paths=["research/inquiries/2026-09-21-geometry-bookmarks.md",
        "research/outputs/2026-10-06-geometry-integration/integration-receipt.json",
        "research/outputs/2026-10-06-geometry-lifecycle/lifecycle-receipt.json"]
    card("c-question-geometry-bookmarks","Integrate the reviewed offline geometry-bookmark candidate","change","done",
        "Integrated the reviewed offline geometry viewer and repaired kind-specific importer validation and view-lifetime retention. The corrected local candidate is 0.15.0 build 20, source commit 2024914d63d51814f1c941ceca92a6d2a000f4a7, with 174 packaged source inputs and release-identity SHA-256 1416bead6e53412f512bec442c63dde874eb913eb004ac2556e108d442706ae2. Qualification retains 96 importer assertions, seven verification-dispatch tests, 16 source-staging checks, 13 package-identity checks and 13 mounted-host lifecycle checks. The original same-label candidate remains retained under its different hash. This is local implementation/qualification completion; producer interoperability, human newcomer acceptance, being-side rollout and causal benefit remain separate. No live source or model was contacted; the 0.14 release identity is unchanged.",
        paths,tags=["research-closeout","geometry-bookmarks","local-candidate"],
        reason="Done applies to reviewed local integration and qualification, with acceptance and rollout explicitly outside this completion.")
    card("t-research-closeout-20261006","Close bounded research and prepare reviewed Git integration","test","done",
        "Completed the October 6 bounded research accounts, reviewed local geometry integration and full Hold Shelf reconciliation with retained publication/readback evidence. S-006/S-008 close with incomplete historical coverage and broader questions open; S-007's frozen blocked window and ledger remain unchanged. The local recovery snapshot and isolated restore have passed their recorded checks. The archive binds the completed source/record commit; the later board completion attestation is a separate Git record rather than a self-containing archive claim. The snapshot is a same-volume recovery copy, not an independently located backup. Reservoir Scope 0.14 acceptance and any being-side rollout remain separate.",
        ["analyses/2026-10-06-bounded-followups-closeout.md","research/inquiries/2026-09-21-geometry-bookmarks.md","analyses/2026-10-06-board-reconciliation.md","analyses/2026-10-06-git-tidy-and-record-status.md"],
        tags=["research-closeout"],ready=False,
        reason="Prepared final wording only; publish after root supplies the actual snapshot and isolated-restore pass, records its exact commit boundary, and verifies the final board readback.")
    operations["cards:t-research-closeout-20261006"]["publication_gate"]="Requires actual verified snapshot/restore receipt and root release of this held operation. Desired done wording is not a present completion claim."
    final_account="analyses/2026-10-06-research-closeout-and-geometry-integration.md"
    held=operations["cards:t-research-closeout-20261006"]
    held["source_refs"].append(final_account)
    held["desired"]["evidence"]="; ".join(held["source_refs"])
    link_sources("cards:t-research-closeout-20261006",[final_account])
    link_sources("cards:c-question-geometry-bookmarks",["research/outputs/2026-10-06-geometry-ui/ui-receipt.json"])


def normalize_and_match(before):
    lane_map = {"Questions":"question","Tests":"test","Changes":"change","Designs":"design","Findings":"finding"}
    for item in operations.values():
        desired = item["desired"]
        key = item["canonical_key"]
        if item["collection"] == "cards":
            candidates = [c for c in before["cards"] if any("id:"+k in c["tags"] for k in [key]+item["aliases"])]
            if not candidates:
                target = item.get("existing_title_hint") or desired["title"]
                candidates = [c for c in before["cards"] if c["title"] == target]
        else:
            candidates = [c for c in before["logs"] if c["title"] == desired["title"] and c["date"][:10] == desired["date"][:10]]
        if len(candidates) > 1:
            raise ValueError("Ambiguous existing match: "+key)
        if candidates:
            original = candidates[0]
            item["existing_live_match"] = {"database_id": None,"title":original["title"],"tags":original.get("tags",[]),"date":original.get("date"),"evidence":original.get("evidence"),"snapshot_record_sha256":digest(json.dumps(original,sort_keys=True,ensure_ascii=False).encode()),"matching_method":"unique id: tag or exact title; dated title for log","source_field":"not exposed by DOM overview; read editor before update"}
            if item.get("already_published") or item["collection"] == "log":
                item["action"] = "no-op"
                item["desired"] = dict(original)
                if item["collection"] == "cards":
                    item["desired"]["lane"] = lane_map[original["lane"]]
                    item["desired"]["being"] = original["being"].lower()
                    item["desired"]["source"] = None
                continue
            if item.get("preserve_existing_status"):
                desired["status"] = original["status"]
            if item.get("append_to_existing_body"):
                desired["body"] = original["body"]+"\n\n"+desired["body"]
            desired["tags"] = list(dict.fromkeys(original.get("tags",[])+desired["tags"]))
            desired["evidence"] = "; ".join(dict.fromkeys([original.get("evidence","")]+item["source_refs"]))
            desired["source"] = None  # Publisher must preserve the actual editor value.
            item["action"] = "update"
        else:
            item["existing_live_match"] = None
            item["action"] = "create"
            if item.get("already_published"):
                raise ValueError("Previously published record not found: "+key)
        if not item["publication_ready"]:
            item["action"] = "pending-outcome"
        if item["collection"] == "cards":
            desired["tags"] = list(dict.fromkeys(desired["tags"]+["historical-backlog"] if item["publication_ready"] and "research-closeout" not in desired["tags"] else desired["tags"]))


def source_inventory():
    tracked = subprocess.check_output(["git","ls-files","*.md"],cwd=ROOT,text=True).splitlines()
    sources = []
    def add(path, kind, label, raw, line=None, source_id=None):
        source_key = source_id or path+"#"+slug(label)
        linked = sorted(source_links.get(path,[]))
        sources.append({"source_id":source_key,"path":path,"kind":kind,"section":label,"line":line,
                        "file_sha256":digest((ROOT/path).read_bytes()),"section_sha256":digest(raw.encode()),
                        "operation_keys":linked,
                        "disposition":"mapped-to-reviewed-operations" if linked else "reference-or-duplicate-notice",
                        "reason":"The operations own publication; original historical source is preserved." if linked else "Context or a repeated pending notice; no separate card is implied."})
    for p in sorted((ROOT/"board").glob("*-pending.json")):
        rel=str(p.relative_to(ROOT));add(rel,"pending-payload","whole pending payload",p.read_text())
    add(GUIDED,"ignored-pending-payload","whole guided-release payload",read(GUIDED))
    completed="analyses/2026-10-06-bounded-followups-closeout.md"
    add(completed,"current-completion-account","whole bounded closeout account",read(completed))
    for path in ["research/outputs/2026-10-06-geometry-integration/integration-receipt.json","research/outputs/2026-10-06-geometry-lifecycle/lifecycle-receipt.json"]:
        add(path,"current-qualification-receipt","whole local candidate receipt",read(path))
    path="research/outputs/2026-10-06-geometry-ui/ui-receipt.json"
    add(path,"current-qualification-receipt","whole actual app UI receipt",read(path))
    path="analyses/2026-10-06-research-closeout-and-geometry-integration.md"
    add(path,"current-integration-account","pre-snapshot integration account",read(path))
    for path in tracked:
        if path=="CLAUDE.md" or path=="analyses/2026-10-06-git-tidy-and-record-status.md":
            continue
        text=read(path)
        for m in re.finditer(r"(?im)^#{1,6} +Board updates pending[^\n]*$",text):
            tail=text[m.end():];end=re.search(r"(?m)^#{1,3} ",tail)
            section=m.group()+tail[:end.start()] if end else m.group()+tail
            line=text[:m.start()].count("\n")+1
            add(path,"pending-section",m.group(),section,line,path+"#L"+str(line))
        for line_no,line in enumerate(text.splitlines(),1):
            if "board updates pending" in line.lower() and not re.match(r"^#{1,6} ",line):
                if path=="research/NOW.md" and "Older `Board updates pending` notices are dated history" in line:
                    continue  # New closeout explanation, not another pending obligation.
                add(path,"inline-pending-notice",line,line,line_no,path+"#inline-L"+str(line_no))
    # Resolve only exact repository references, never a generic basename such as
    # README.md that could spuriously connect unrelated historical material.
    for row in sources:
        if row["operation_keys"]:
            continue
        text=read(row["path"])
        links=set()
        for path,ops in source_links.items():
            if path and path in text:
                links.update(ops)
        if links:
            row["operation_keys"]=sorted(links)
            row["disposition"]="covered-by-linked-records"
            row["reason"]="Pending section or repeated notice points to these canonical records; no duplicate card/log."
    return sources


def revise_published_fixture():
    """Root confirmed this generation-2 card saved before its refinement."""
    item=operations["cards:f-reservoir-active-input-fixture"]
    old=dict(item["desired"])
    reason=("The initial guided-release preparation was unavailable, but the later "
            "September 16 retry retained a partial model record. Qualify the initial "
            "claim and link the later outcome without implying a completed comparison.")
    item["revision_events"]=[{"from_generation":2,"to_generation":3,
        "before_desired":old,"correction_reason":reason,
        "publication_evidence":"Root confirmed the original desired card was created and retained in its boardWrites receipt; apply one update to that exact card."}]
    item["source_refs"].append("analyses/2026-09-16-active-observation-retry.md")
    link_sources("cards:f-reservoir-active-input-fixture",item["source_refs"])
    item["desired"]["body"]=("Three maximum absolute states exceed 0.25 with matched arms. "
        "Scripted evidence establishes transport only. The initial guided-release phi3 "
        "preparation was unavailable; its immutable preparation and separate prompt-version "
        "amendment remain retained. A later separately authorized September 16 retry saved "
        "a failed-but-verifiable 60-step partial model record: four requests, three journals "
        "and one incomplete response at the frozen 256-token ceiling. Neither the scripted "
        "fixture nor that partial retry establishes a completed controlled model comparison.")
    item["desired"]["evidence"]="; ".join(item["source_refs"])
    item["desired"]["source"]=None
    item["resolution"]=reason
    item["existing_live_match"]={"database_id":None,"title":old["title"],"tags":old["tags"],
        "evidence":old["evidence"],"matching_method":"Root-confirmed generation-2 save; unique id: tag and exact title",
        "source_field":"read editor and preserve the source saved in generation 2"}
    item["action"]="update"


def dom_text(value):
    """The rendered overview collapses text whitespace; editor receipts do not."""
    return " ".join(value.split()) if isinstance(value,str) else value


def verify_readback(path):
    """Check this manifest against a retained DOM readback; never touch the UI."""
    manifest=json.loads(OUT.read_text())
    observed=json.loads(Path(path).read_text())
    before=json.loads(BEFORE.read_text())
    lane_map={"Questions":"question","Tests":"test","Changes":"change","Designs":"design","Findings":"finding"}
    problems=[];verified=[];held=[]
    for item in manifest["operations"]:
        if not item["publication_ready"]:
            held.append(item["canonical_key"]);continue
        expected=item["desired"]
        group=observed["cards" if item["collection"]=="cards" else "logs"]
        if item["collection"]=="cards":
            matches=[x for x in group if "id:"+item["canonical_key"] in x.get("tags",[])]
            if not matches:matches=[x for x in group if x["title"]==expected["title"]]
            fields=("title","body","lane","status","being","tags","evidence")
        else:
            matches=[x for x in group if x["title"]==expected["title"] and x["date"][:10]==expected["date"][:10]]
            fields=("title","body","date")
        if len(matches)!=1:
            problems.append({"key":item["canonical_key"],"error":"Expected one unique readback","matches":len(matches)});continue
        actual=dict(matches[0]);actual["lane"]=lane_map.get(actual.get("lane"),actual.get("lane"))
        if "being" in actual:actual["being"]=actual["being"].lower()
        diffs=[]
        for field in fields:
            left=actual.get(field);right=expected.get(field)
            if field=="tags":left=sorted(left or []);right=sorted(right or [])
            if field=="date":left=left[:10];right=right[:10]
            if field=="body":left=dom_text(left);right=dom_text(right)
            if left!=right:diffs.append(field)
        if diffs:problems.append({"key":item["canonical_key"],"error":"Saved fields differ","fields":diffs})
        else:verified.append(item["collection"]+":"+item["canonical_key"])
        if item["collection"]=="cards" and item["action"]=="update":
            previous=item.get("existing_live_match",{}).get("evidence","") or ""
            retained={part.strip() for part in (actual.get("evidence","") or "").split(";") if part.strip()}
            missing=[part.strip() for part in previous.split(";") if part.strip() and part.strip() not in retained]
            if missing:problems.append({"key":item["canonical_key"],"error":"Original evidence pointer missing","missing":missing})
    # Original history cannot disappear during an append/update reconciliation.
    for collection in ("cards","logs"):
        for old in before[collection]:
            matches=[x for x in observed[collection] if x["title"]==old["title"]]
            if collection=="logs":matches=[x for x in matches if x["date"]==old["date"] and dom_text(x["body"])==dom_text(old["body"])]
            if len(matches)!=1:problems.append({"error":"Original history missing or ambiguous","collection":collection,"title":old["title"]})
            elif collection=="cards" and not any(o["collection"]=="cards" and o["action"]=="update" and o.get("existing_live_match",{}).get("title")==old["title"] for o in manifest["operations"]):
                changed=[field for field in ("body","lane","status","being","tags","evidence") if dom_text(matches[0].get(field))!=dom_text(old.get(field))]
                if changed:problems.append({"error":"Unrelated original card fields changed","title":old["title"],"fields":changed})
    result={"schema":"hold-shelf-reconciliation-dom-check-20261006-v1","manifest_sha256":digest(OUT.read_bytes()),
            "readback_sha256":digest(Path(path).read_bytes()),"status":"passed" if not problems else "failed",
            "verified_operations":len(verified),"verified_keys":verified,"held_current_outcomes":held,
            "required_dom_writes":len(problems),"problems":problems,
            "limits":"DOM verifies visible fields and retained history after rendered-body whitespace normalization; exact editor text, source and nonexposed database metadata require the publisher's editor receipts. Zero required DOM writes is not evidence of hidden-field equality."}
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if not problems else 2


def verify_editors(path):
    """Compare a separately captured read-only editor pass, including source."""
    manifest=json.loads(OUT.read_text())
    captured=json.loads(Path(path).read_text())
    records=captured["records"]
    attempts_path=BEFORE.parent/"historical-publication-attempts.json"
    attempts=json.loads(attempts_path.read_text())["cards"]
    correction_path=BEFORE.parent/"historical-publication-correction.json"
    attempts.append(json.loads(correction_path.read_text()))
    final_path=BEFORE.parent/"final-closeout-publication.json"
    if final_path.exists():
        final=json.loads(final_path.read_text())
        attempts.extend(final["cards"] if "cards" in final else [final])
    problems=[];verified=[];source_limits=[]
    for item in manifest["operations"]:
        if item["collection"]!="cards" or not item["publication_ready"] or item["action"]=="no-op":continue
        key=item["canonical_key"];expected=dict(item["desired"])
        matches=[r for r in records if r["key"]==key]
        if len(matches)!=1:
            problems.append({"key":key,"error":"Expected one editor readback","matches":len(matches)});continue
        actual=matches[0]["editor"]
        source_basis="explicit desired source"
        if expected["source"] is None:
            witnesses=[r["before_editor"]["source"] for r in attempts if r["key"]==key and r.get("action")=="update" and r.get("before_editor",{}).get("source") is not None]
            if witnesses:
                expected["source"]=witnesses[0];source_basis="retained pre-update editor"
            else:
                previous=[r["readback_editor"]["source"] for r in attempts if r["key"]==key and r.get("readback_editor",{}).get("source") is not None]
                if previous:
                    expected["source"]=previous[0];source_basis="first saved editor readback; publisher attests preservation"
                    source_limits.append({"key":key,"limit":"No separate pre-update source witness retained; first saved editor value and publisher preservation note retained."})
                else:
                    problems.append({"key":key,"error":"No retained source witness for update"});continue
        diffs=[]
        for field in ("title","body","lane","status","being","tags","evidence","source"):
            left=actual.get(field);right=expected.get(field)
            if field=="tags":
                left=sorted(t.strip() for t in left.split(",") if t.strip()) if isinstance(left,str) else sorted(left or [])
                right=sorted(right or [])
            if left!=right:diffs.append(field)
        if diffs:problems.append({"key":key,"error":"Saved editor fields differ","fields":diffs})
        else:verified.append({"key":key,"source_basis":source_basis})
    result={"schema":"hold-shelf-reconciliation-editor-check-20261006-v1",
        "manifest_sha256":digest(OUT.read_bytes()),"editor_receipt_sha256":digest(Path(path).read_bytes()),
        "status":"passed" if not problems else "failed","verified_operations":len(verified),
        "verified":verified,"required_editor_writes":len(problems),"problems":problems,"source_witness_limits":source_limits,
        "limits":"Compares retained editor fields exactly, including source; database IDs and creation metadata remain unexposed. The historical source-witness limit is explicit, not reconstructed."}
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if not problems else 2


def write_mirror():
    """Publish a compact local mirror from the manifest's saved UI receipts."""
    manifest=json.loads(OUT.read_text())
    observed_path=ROOT/manifest["publication_readback"]["dom_path"]
    editor_path=ROOT/manifest["publication_readback"]["editor_path"]
    observed=json.loads(observed_path.read_text())
    editors={r["key"]:r["editor"] for r in json.loads(editor_path.read_text())["records"]}
    records=[]
    for item in manifest["operations"]:
        key=item["canonical_key"];expected=item["desired"]
        group=observed["cards" if item["collection"]=="cards" else "logs"]
        if item["collection"]=="cards":
            matches=[r for r in group if "id:"+key in r.get("tags",[])]
            if not matches:matches=[r for r in group if r["title"]==expected["title"]]
        else:
            matches=[r for r in group if r["title"]==expected["title"] and r["date"][:10]==expected["date"][:10]]
        assert len(matches)==1,(key,len(matches))
        actual=matches[0]
        row={"collection":item["collection"],"canonical_key":key,"database_id":None,
             "title":actual["title"],"observed_date":actual.get("date"),
             "reconciliation":"verified-no-write-needed" if item["publication_ready"] else "current-active-card-final-done-held-for-snapshot",
             "observed_record_sha256":digest(json.dumps(actual,sort_keys=True,ensure_ascii=False).encode()),
             "source_refs":item["source_refs"]}
        if item["collection"]=="cards":
            row.update({k:actual[k] for k in ("lane","status","being","tags","evidence")})
            row["source"]=editors.get(key,{}).get("source")
            row["source_verification"]="exact persisted editor readback" if key in editors else "unchanged/no-op or held card; source not recaptured in this editor pass"
        records.append(row)
    result={"schema":"hold-shelf-reconciled-backlog-mirror-20261006-v1",
        "status":"pre-snapshot-reconciliation-verified-overall-closeout-held" if any(not o["publication_ready"] for o in manifest["operations"]) else "reconciliation-verified-final-attestation-saved",
        "manifest":{"path":str(OUT.relative_to(ROOT)),"sha256":digest(OUT.read_bytes()),"generation":manifest["generation"]},
        "observed_at":observed.get("observed_at"),"board_totals":{"cards":len(observed["cards"]),"logs":len(observed["logs"])},
        "scope":"All canonical records covered by this backlog reconciliation, including the actual observed closeout card. Unrelated original board records remain in the private full inventory; no original record was removed.",
        "private_full_inventory":{"path":str(observed_path.relative_to(ROOT)),"sha256":digest(observed_path.read_bytes())},
        "private_editor_readback":{"path":str(editor_path.relative_to(ROOT)),"sha256":digest(editor_path.read_bytes())},
        "limits":"Database IDs and creation timestamps are not exposed. Card displayed dates are not inferred creation dates. Null source means not recaptured, not cleared. Full text stays in the canonical manifest and private DOM/editor receipts; this mirror records actual observed state.",
        "records":records}
    path=ROOT/"board/2026-10-06-reconciled-backlog.json"
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"path":str(path.relative_to(ROOT)),"canonical_records":len(records),"board_totals":result["board_totals"]}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-readback",type=Path,help="Check a retained after-DOM snapshot against the prepared manifest; writes nothing")
    parser.add_argument("--check-editors",type=Path,help="Check a retained read-only editor pass against desired fields and original source witnesses; writes nothing")
    parser.add_argument("--write-mirror",action="store_true",help="Write the dated compact local mirror from the retained pre-snapshot receipts; no board access")
    args=parser.parse_args()
    if args.check_readback:
        raise SystemExit(verify_readback(args.check_readback))
    if args.check_editors:
        raise SystemExit(verify_editors(args.check_editors))
    if args.write_mirror:
        write_mirror();return
    if OUT.exists() and json.loads(OUT.read_text()).get("generation",0)>6:
        raise SystemExit("Final snapshot/board attestation already appended. Preparation is frozen; use the readback/editor checks or mirror command without overwriting that later record.")
    before=json.loads(BEFORE.read_text())
    assert len(before["cards"])==178 and len(before["logs"])==45
    load_payloads();add_narrative_payloads();add_accounts();add_daily();add_release();add_triple();add_current_holds();complete_bounded_followups();complete_geometry_and_prepare_closeout()
    # Explicit conflict resolution: the later source-context payload wins over
    # the earlier survey's proposal state; no alphabetical replay determines it.
    key="cards:c-study-page-scope-and-coverage"
    d=json.loads(read("board/study-source-context-pending.json"))
    row=next(r for r in d["proposed_cards"] if r["id"]=="c-study-page-scope-and-coverage")
    operations[key]["desired"]["status"]="done";operations[key]["desired"]["body"]=row["body"]
    operations[key]["resolution"]="Later verified implementation supersedes the earlier open proposal; natural understanding benefit remains unestablished."
    operations["cards:c-reservoir-guided-journey"]["aliases"]=["design-reservoir-scope-guided-route"]
    # Explicit payload/archive ownership links not repeated in every card body.
    for path, keys in {
        "research/histories/self-study.md":["cards:f-self-study-longitudinal-history"],
        "research/studies/S-008-study-to-follow-through.md":["cards:t-track-self-study-through-journal-and-actual-next-actions","cards:q-durable-correction-followthrough"],
        "analyses/2026-09-09-minime-nine-studies.md":["cards:f-minime-study-answer-retention"],
        "analyses/2026-09-10-study-claim-evidence.md":["cards:t-study-claim-evidence"],
    }.items():
        for k in keys: link_sources(k,[path])
    for path in ["board/astrid-study-survey-pending.json","board/study-source-context-pending.json"]:
        payload=json.loads(read(path))
        key="2026-09-15-"+Path(path).stem.removesuffix("-pending")
        log(key,payload["title"],payload["log"],[path]+refs(payload.get("evidence")),"2026-09-15")
    active_path=ROOT/"research/outputs/2026-10-06-board-reconciliation/active-closeout-readback.json"
    if active_path.exists():
        active=json.loads(active_path.read_text())
        observed=active.get("readback",active.get("desired",{}))
        if isinstance(observed,list):
            assert len(observed)==1
            observed=observed[0]
        if observed.get("title"):
            if not any(c["title"]==observed["title"] for c in before["cards"]):
                observed=dict(observed)
                observed.setdefault("lane","Tests");observed.setdefault("being","SYSTEM")
                observed.setdefault("tags",["id:t-research-closeout-20261006","research-closeout"])
                observed.setdefault("date",DATE)
                before["cards"].append(observed)
    normalize_and_match(before)
    revise_published_fixture()
    sources=source_inventory()
    manifest={"schema":"hold-shelf-reconciliation-20261006-v1","status":"pre_snapshot_reconciliation_verified_overall_closeout_held","date":DATE,"generation":6,
              "board_url":"https://claude.ai/code/artifact/f4761d4a-94e8-43ca-882f-ca887956fca0",
              "before":{"path":str(BEFORE.relative_to(ROOT)),"sha256":digest(BEFORE.read_bytes()),"observed_at":before["observed_at"],"cards":178,"logs":45},
              "identity_limit":"DOM overview exposes unique titles/tags/evidence, not database IDs, creation timestamps or source field. All database_id values are null; source=null on existing-card operations means preserve the actual editor source value.",
              "semantic_review":"Historical ready operations individually reconciled against the dated payloads/accounts and existing titles/tags. Proposal completion, implementation, historical deployment, bounded findings, model qualification and human acceptance remain distinct. The bounded S-006/S-008 extensions close with incomplete coverage, while their broader questions remain open. Reviewed local geometry integration is complete; overall closeout remains held for the verified recovery snapshot.",
              "snapshot_boundary":"Two phases: commit the completed source/research/reconciliation record with overall closeout held; then archive and verify that exact commit. Publish the held completion and commit the later board/snapshot attestation separately. No archive is claimed to contain its own later verification or board attestation.",
              "publication_readback":{"dom_path":"research/outputs/2026-10-06-board-reconciliation/pre-snapshot-after-reload.json","editor_path":"research/outputs/2026-10-06-board-reconciliation/pre-snapshot-editor-readbacks.json","dom_check_path":"research/outputs/2026-10-06-board-reconciliation/pre-snapshot-dom-check.json","editor_check_path":"research/outputs/2026-10-06-board-reconciliation/pre-snapshot-editor-check.json","visible_ready_operations":188,"changed_cards_with_exact_editor_fields":113,"cards":286,"logs":107,"required_dom_writes":0,"required_editor_writes":0,"scope":"All ready operations. Overall final done remains held, with its current active card preserved."},
              "publication_rules":["Root alone publishes through the authenticated existing UI; this script only prepares local records.","Read live fields before each update; if they changed since the before snapshot, re-reconcile instead of overwriting.","Preserve existing source/creation metadata and unrelated evidence; no card or log deletion.","Only publication_ready=true operations may publish. Held current study/geometry/closeout entries await final outcomes.","Existing done studies remain done. Day11 verification block and human newcomer acceptance are separate records.","Historical event dates remain source dates. Publication/readback timestamps are actual current times, never backdated.","After each save, reload and compare all editable fields; record actual identity, desired/readback hashes and outcome externally.","On resume, compare to desired state first; exact matches are no-ops. Never retry a create merely because its previous outcome was unknown.","Do not rewrite original pending payloads or dated historical accounts to pretend publication happened earlier."],
              "aliases":ALIASES,"sources":sources,"operations":list(operations.values()),
              "summary":{"sources":len(sources),"source_kinds":dict(Counter(s["kind"] for s in sources)),"operations":len(operations),"actions":dict(Counter(o["action"] for o in operations.values())),"cards":sum(o["collection"]=="cards" for o in operations.values()),"logs":sum(o["collection"]=="log" for o in operations.values()),"held_current_outcomes":[o["canonical_key"] for o in operations.values() if not o["publication_ready"]]}}
    for s in sources:
        assert all(k in operations for k in s["operation_keys"]),(s["path"],s["operation_keys"])
    desired_titles=[(o["collection"],o["desired"]["title"],o["desired"].get("date")) for o in operations.values()]
    assert len(set(desired_titles))==len(desired_titles),"Duplicate desired board identity"
    assert not any(not s["operation_keys"] for s in sources),"Unresolved source disposition"
    ready=[o for o in operations.values() if o["publication_ready"]]
    assert all(o["desired"]["source"] for o in ready if o["collection"]=="cards" and o["action"]=="create")
    assert all(o["desired"]["source"] is None for o in ready if o["collection"]=="cards" and o["action"]=="update")
    new_text=json.dumps(manifest,indent=2,ensure_ascii=False)+"\n"
    if OUT.exists() and OUT.read_text()!=new_text:
        old=OUT.read_bytes();old_path=BEFORE.parent/("prepared-manifest-"+digest(old)+".json")
        if not old_path.exists():old_path.write_bytes(old)
    OUT.write_text(new_text)
    print(json.dumps(manifest["summary"],indent=2))
    print("unmapped substantive sources:",[s["path"] for s in sources if not s["operation_keys"]])


if __name__ == "__main__":
    main()
