"""Replay only frozen variety evidence; separate WRITE and verify action links."""
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
import statistics
import sys

from minime_study_variety import LOCAL, digest, load, write_json


def main(out):
    manifest = json.loads((out / "capture-manifest.json").read_text())
    for name, row in manifest["files"].items():
        assert digest((out / name).read_bytes()) == row["sha256"]
    derived = json.loads((out / "analysis-manifest.json").read_text())
    assert derived["capture_manifest_sha256"] == digest((out / "capture-manifest.json").read_bytes())
    for name in ("summary.json", "journal-index.jsonl", "reading-pack.jsonl"):
        assert digest((out / name).read_bytes()) == derived["files"][name], name
    journals = {r["name"].lstrip("!"):r for r in load(out / "journals.jsonl")}
    index = {r["name"].lstrip("!"):r for r in map(json.loads, (out / "journal-index.jsonl").read_text().splitlines())}
    private_manifest = json.loads((out / "private-manifest.json").read_text())
    assert digest((out / "private-journals.jsonl").read_bytes()) == private_manifest["sha256"]
    for row in load(out / "private-journals.jsonl"):
        key = row["name"].lstrip("!")
        assert key not in journals
        journals[key] = row
        index[key] = dict(row, day=datetime.fromtimestamp(row["timestamp"], LOCAL).date().isoformat(),
            prose_candidate=True, prefix="private_writing", word_count=None)
    jobs = {json.loads(r["text"])["job_id"]:json.loads(r["text"]) for r in load(out / "jobs.jsonl")}
    generations = [dict(json.loads(r["text"]), retained_sha256=r["sha256"], retained_path=r["path"]) for r in load(out / "generations.jsonl")]
    am = json.loads((out / "actions-manifest.json").read_text())
    assert digest((out / "actions.jsonl").read_bytes()) == am["sha256"]
    actions = [json.loads(line) for line in (out / "actions.jsonl").read_text().splitlines()]
    by_job, children, daily_actions = defaultdict(list), defaultdict(list), defaultdict(Counter)
    for action in actions:
        payload = json.loads(action["payload"])
        action["decoded"] = payload
        by_job[payload.get("llm_job_id")].append(action)
        children[payload.get("parent_action_id")].append(action)
        stamp = int(action["action_id"].split("_")[2]) / 1000
        day = datetime.fromtimestamp(stamp, LOCAL).date().isoformat()
        daily_actions[day][action["canonical_action"].split()[0]] += 1
    linked, unlinked, daily_generations = {}, [], defaultdict(list)
    for gen in generations:
        job = jobs.get(gen.get("job_id"), {})
        route = ("private_write" if job.get("action_text", "").startswith("WRITE ") else
                 "source_study" if gen.get("lane") == "self_study" else gen.get("lane", "unknown"))
        gen["resolved_route"] = route
        day = datetime.fromisoformat(gen["created_at"]).astimezone(LOCAL).date().isoformat()
        daily_generations[day].append(gen)
        response = gen.get("response_text") or ""
        matches = []
        for artifact in gen.get("linked_artifacts", []):
            name = Path(artifact.get("path", "")).name.lstrip("!")
            if name in journals and response and response in journals[name]["text"]:
                matches.append(name)
        if not matches and gen.get("lane") == "self_study" and response:
            # Exact whole-response containment, restricted to two seconds either side.
            stamp = datetime.fromisoformat(gen["created_at"]).timestamp()
            matches = [name for name, row in journals.items() if abs(row["timestamp"]-stamp)<2 and response in row["text"]]
        if len(set(matches)) == 1:
            name = matches[0]
            if name in linked:
                raise ValueError("Ambiguous generation/journal link")
            linked[name] = gen
        elif gen.get("lane") == "self_study":
            unlinked.append(dict(id=gen["generation_id"], status=gen["status"], matches=matches))
    latest = [json.loads(line) for line in (out / "reading-pack.jsonl").read_text().splitlines() if json.loads(line)["group"] == "latest120"]
    detail = []
    for row in latest:
        gen = linked.get(row["name"].lstrip("!"))
        assert gen is not None, row["name"]
        own = by_job.get(gen.get("job_id"), [])
        child = [c for a in own for c in children[a["action_id"]]]
        user = "\n".join(m.get("content", "") for m in gen.get("messages", []) if m.get("role") == "user")
        boundary = re.search(r"Source revision: sha256:([a-f0-9]+); bytes (\d+)\.\.(\d+)", row["text"])
        controls = gen.get("generation_controls", {}).get("adapter_sent", {})
        timing = gen.get("backend_timing") or {}
        detail.append(dict(name=row["name"], generation_id=gen["generation_id"], route=gen["resolved_route"],
            action_ids=[a["action_id"] for a in own], action_statuses=[a["status"] for a in own],
            generated_next=gen.get("next_action_parsed"),
            child_choices=[dict(action_id=c["action_id"], command=c["canonical_action"], status=c["status"], parent=c["decoded"].get("parent_action_id")) for c in child],
            tokens=timing.get("eval_count"), finish=timing.get("native_finish"), allowance=controls.get("num_predict",timing.get("effective_num_predict")),
            elapsed_s=gen.get("elapsed_s"), source_title=row["metadata"]["title"],
            interval=([boundary[1],int(boundary[2]),int(boundary[3])] if boundary else None),
            input_chars=len(user), input_blocked_mentions=user.count("blocked"),
            study_question_directives=row["question"], model=gen.get("model")))
    daily = []
    for day in sorted({r["day"] for r in index.values()}):
        entries = [r for r in index.values() if r["day"]==day and r["prose_candidate"]]
        drafts = [r for r in entries if r["prefix"]=="private_writing"]
        studies = [r for r in entries if r["prefix"]=="self_study" and r not in drafts]
        gens = daily_generations[day]
        source_gens = [g for g in gens if g["resolved_route"]=="source_study"]
        daily.append(dict(day=day, prose_candidates=len(entries), private_write=len(drafts), source_study=len(studies),
            source_study_median_words=statistics.median(r["word_count"] for r in studies) if studies else None,
            ordinary_prose=len(entries)-len(drafts)-len(studies),
            study_journals_with_generation=sum(r["name"].lstrip("!") in linked for r in studies),
            source_attempts=len(source_gens), source_generation_statuses=dict(Counter(g["status"] for g in source_gens)),
            generation_routes=dict(Counter(g["resolved_route"] for g in gens)),
            private_write_files_with_verified_generation=sum(linked.get(r["name"].lstrip("!"),{}).get("resolved_route")=="private_write" for r in drafts),
            recorded_action_choices=dict(daily_actions[day])))
    intervals = Counter((r["source_title"],*r["interval"]) for r in detail if r["interval"])
    matched = sum(any(c["command"]==r["generated_next"] for c in r["child_choices"]) for r in detail)
    report = dict(daily=daily, linked_journals=len(linked), unlinked_study_attempts=unlinked,
        latest120=dict(count=len(detail), models=dict(Counter(r["model"] for r in detail)),
            token_median=statistics.median(r["tokens"] for r in detail if r["tokens"] is not None),
            token_min=min(r["tokens"] for r in detail if r["tokens"] is not None),
            token_max=max(r["tokens"] for r in detail if r["tokens"] is not None),
            finishes=dict(Counter(str(r["finish"]) for r in detail)), allowances=dict(Counter(r["allowance"] for r in detail)),
            with_action_receipt=sum(bool(r["action_ids"]) for r in detail),
            with_linked_child=sum(bool(r["child_choices"]) for r in detail), with_matching_chosen_child=matched,
            source_page_deliveries=sum(intervals.values()), distinct_exact_intervals=len(intervals),
            repeated_exact_intervals=sum(n-1 for n in intervals.values()),
            navigation_or_no_interval=sum(not r["interval"] for r in detail), detail=detail),
        limits=["Day16 is partial; generation capture begins September7; source/draft split uses exact linked response plus job action text.",
                "Each database action has an epoch-prefixed ID; journals and action rows are not independent episodes.",
                "Job outcomes may finish after cutoff; report which journal/attempt was selected, not a completed-opportunity census."])
    write_json(out / "followthrough.json", report)
    print(json.dumps({k:v for k,v in report["latest120"].items() if k!="detail"},indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
