import copy
import json
import tempfile
import unittest
from pathlib import Path

from reservoir_research.research_followups import (SCHEMA, Reader, source_path, encoded, sha, iso, epoch,
    validate_protocol, retained, check_records, capture_runs, capture_provider, analyze_runs,
    analyze_provider, exposure_basis, analyze_durable, load_daily_packet, validate_correction_review)


class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name).resolve()
        self.start=1700000000
        self.case=dict(anchor_generation="old",quote="only processes a single item",source="astrid/example.rs",
            source_sha256="a"*64,critical_byte_start=10,critical_byte_end=40,source_tokens=["while", "recv()"],
            saved_note_origin_sha256=None,historical_storage="authored_prose_not_established_in_saved_note")
        self.p=dict(schema=SCHEMA,qualification=dict(passed=True),frozen_at=iso(self.start-1),t0=iso(self.start),
            intake_end=iso(self.start+7*86400),provider_end=iso(self.start+86400),final_end=iso(self.start+9*86400),
            run_limit=10,provider_attempt_limit=5000,exposure_limit=3,followup_seconds=48*3600,
            provider_collection_allowance_seconds=120,unattended_actor="claude-heartbeat",
            cases={"worker-single-item":copy.deepcopy(self.case),"comment-as-call":copy.deepcopy(self.case)},
            allowlist=dict(authority="read_only_existing_files_no_source_commands",astrid_root=str(self.root),
                runs_directory="runs",notes_directory="notes",provider_spool=str(self.root/"provider")))
        for q in [self.root/"runs",self.root/"notes",self.root/"provider/events"]: q.mkdir(parents=True)

    def tearDown(self): self.tmp.cleanup()

    def put(self,path,value):
        path.parent.mkdir(exist_ok=True,parents=True); path.write_bytes(encoded(value)); return path

    def runfile(self,offset=1,**changes):
        rid=f"run_{(self.start+offset)*10**9}_a"
        data=dict(schema="steward_run_receipt_v1",run_id=rid,actor="claude-heartbeat",adapter_kind="subprocess",
            started_at=iso(self.start+offset),finished_at=iso(self.start+offset+10),status="finished",outcome="success",exit_code=0,
            lease_token="PRIVATE AUTHORITY",nested=dict(secret="PRIVATE"))
        data.update(changes); self.put(self.root/"runs"/(rid+".json"),data); return rid,data

    def provider(self,offset=1,**changes):
        ms=(self.start+offset)*1000; aid=f"provider-{ms}-12-0"
        d=dict(schema="provider_attempt_observation_v1",stage="dispatch_started",attempt_id=aid,pid=12,
            request_sha256="a"*64,created_at_unix_ms=ms,provider="mlx",release_before=dict(manifest_sha256="b"*64))
        d.update(changes); self.put(self.root/"provider/events"/(aid+"-dispatch.json"),d); return aid,d

    def outcome(self,aid,d,**changes):
        out=dict(d,stage="provider_outcome",elapsed_ms=1000,outcome="provider_returned",marker_observed_total=0,
            input_availability="observed_no_markers_raw_not_retained")
        out.update(changes); self.put(self.root/"provider/events"/(aid+"-outcome.json"),out); return out

    def study(self,offset=1,**changes):
        n=dict(status="included_in_submitted_user_text",sha256="n"*64,fields=dict(note=None,question=None,previous=None))
        s=dict(id=f"g{offset}",completed=iso(self.start+offset),record_sha256="r"*64,response_sha256="q"*64,
            text="The source shows a receive loop.",user_text="Numbered source and notebook.",
            actual_route="source_study",receipt_verified=True,notebook=n,system_hashes=["s"*64],era="reviewed",pid=1,
            pages=[dict(source=self.case["source"],revision=dict(sha256="a"*64),start=dict(byte=10),end=dict(byte=40),text="while recv()")])
        s.update(changes); return s

    def daily(self,studies,name="day"):
        folder=self.root/name
        report=dict(schema="source_study_fidelity_daily_v6",studies=studies,capture_errors=[],join_issues=[])
        p=self.put(folder/"final-report/report.json",report)
        v=self.put(folder/"verification.json",dict(schema="s007_daily_verification_v6",report_sha256=sha(p.read_bytes()),replay_identical=True))
        self.put(folder/"packet-manifest.json",{"final-report/report.json":sha(p.read_bytes()),"verification.json":sha(v.read_bytes())})
        return folder

    def test_protocol_rejects_outcome_before_freeze(self):
        validate_protocol(self.p)
        bad=copy.deepcopy(self.p); bad["frozen_at"]=bad["t0"]
        with self.assertRaises(AssertionError): validate_protocol(bad)

    def test_no_live_reads_before_t0(self):
        reader=Reader()
        self.assertEqual(capture_runs(self.p,self.start-1,reader)["status"],"awaiting_window")
        self.assertEqual(capture_provider(self.p,self.start-1,reader)["status"],"awaiting_window")
        self.assertEqual(reader.inventories,[])

    def test_caps_do_not_return_partial_inventory_as_complete(self):
        self.runfile(1); self.runfile(2)
        cap=capture_runs(self.p,self.start+30,Reader(entries=1))
        self.assertTrue(cap["errors"]); self.assertFalse(cap["inventories"][0]["complete"])
        self.assertEqual(cap["selected_run_ids"],[])
        self.assertEqual(analyze_runs(self.p,[cap],self.start+30)["status"],"coverage_blocked")

    def test_stable_reader_file_and_total_caps(self):
        p=self.root/"data";p.write_bytes(b"x"*20)
        with self.assertRaises(ValueError): Reader(file_limit=19).read(p)
        with self.assertRaises(ValueError): Reader(total=19).read(p)

    def test_path_escape_and_symlinks_rejected(self):
        with self.assertRaises(ValueError): source_path(self.root,"../outside")
        p=self.root/"source";p.write_text("data"); (self.root/"link").symlink_to(p)
        with self.assertRaises(ValueError): source_path(self.root,"link")
        with self.assertRaises(ValueError): Reader().read(self.root/"link")

    def test_consecutive_runs_include_failures_and_strip_authority(self):
        ids=[]
        for i in range(1,13): ids.append(self.runfile(i,outcome="failed" if i%2 else "success")[0])
        cap=capture_runs(self.p,self.start+100)
        self.assertEqual(cap["selected_run_ids"],ids[:10])
        self.assertNotIn("PRIVATE",json.dumps(cap))
        result=analyze_runs(self.p,[cap],self.start+100)
        self.assertEqual(result["run_count"],10)
        self.assertEqual(result["runs"][0]["terminal_state"],"failed")
        self.assertTrue(result["runs"][0]["queue_missing"])
        self.assertEqual(result["runs"][0]["benefit"],"unmeasured")

    def test_unknown_controller_schema_blocks(self):
        self.runfile(schema="new_unreviewed_v2")
        self.assertTrue(capture_runs(self.p,self.start+100)["errors"])

    def test_interactive_actor_not_counted_as_unattended(self):
        self.runfile(actor="interactive-user")
        cap=capture_runs(self.p,self.start+100)
        self.assertEqual(cap["selected_run_ids"],[])
        self.assertEqual(analyze_runs(self.p,[cap],self.start+100)["excluded_actor_counts"],{"interactive-user":1})

    def test_late_run_terminal_is_censored(self):
        self.runfile(finished_at=iso(self.start+3*86400))
        cap=capture_runs(self.p,self.start+4*86400)
        row=analyze_runs(self.p,[cap],self.start+4*86400)["runs"][0]
        self.assertEqual(row["terminal_state"],"right_censored")
        self.assertIsNone(row["elapsed_seconds"])

    def test_queue_identity_and_count_verification(self):
        rid,_=self.runfile(); cap=capture_runs(self.p,self.start+100)
        q=dict(schema="flywheel_unprocessed_selected_v1",selected_count=2,processed=["report1"],unprocessed_in_queue_order=["report2"])
        cap["records"].append(retained("/retained/unprocessed_selected.json",encoded(q),"round_packet",run_id=rid))
        self.assertEqual(analyze_runs(self.p,[cap],self.start+100)["runs"][0]["queue"]["unprocessed"],["report2"])
        q["unprocessed_in_queue_order"]=["report1"]
        cap["records"][-1]=retained("/retained/unprocessed_selected.json",encoded(q),"round_packet",run_id=rid)
        with self.assertRaises(ValueError): analyze_runs(self.p,[cap],self.start+100)

    def test_provider_window_and_pending_outcomes(self):
        aid,d=self.provider(); self.provider(-1); self.provider(86400)
        cap=capture_provider(self.p,self.start+86402)
        result=analyze_provider(self.p,[cap],self.start+86402)
        self.assertEqual(result["dispatches"],1);self.assertEqual(result["pending_attempts"],[aid])
        self.assertEqual(result["repair_benefit"],"unmeasured")

    def test_provider_unavailable_input_not_zero(self):
        aid,d=self.provider();self.outcome(aid,d,marker_observed_total=None,outcome="transport_error",input_availability="response_unavailable")
        cap=capture_provider(self.p,self.start+30)
        result=analyze_provider(self.p,[cap],self.start+30)
        self.assertEqual(result["unknown_marker_inputs"],[aid]);self.assertEqual(result["marker_bearing_attempts"],[])

    def test_late_provider_outcome_excluded(self):
        aid,d=self.provider();self.outcome(aid,d,elapsed_ms=86520*1000)
        cap=capture_provider(self.p,self.start+86600)
        self.assertTrue(any(x["kind"]=="late_provider_outcome" for x in cap["records"]))
        self.assertEqual(analyze_provider(self.p,[cap],self.start+86600)["pending_attempts"],[aid])

    def test_provider_identity_and_raw_traversal_rejected(self):
        aid,d=self.provider(); self.outcome(aid,d,pid=999)
        self.assertTrue(capture_provider(self.p,self.start+30)["errors"])
        self.outcome(aid,d,raw_artifact="../../secret",raw_response_sha256="a"*64)
        self.assertTrue(capture_provider(self.p,self.start+30)["errors"])

    def test_provider_immutable_conflict_and_record_tampering(self):
        aid,d=self.provider();cap=capture_provider(self.p,self.start+30)
        bad=copy.deepcopy(cap);v=json.loads(bad["records"][0]["text"]);v["request_sha256"]="z"*64
        bad["records"][0]=retained(bad["records"][0]["path"],encoded(v),"provider_dispatch")
        with self.assertRaises(ValueError): analyze_provider(self.p,[cap,bad],self.start+30)
        bad["records"][0]["text"]+=" "
        with self.assertRaises(ValueError): check_records(bad["records"])

    def test_daily_seal_tamper_unknown_schema_and_unverified_era(self):
        path=self.daily([self.study()]);load_daily_packet(path,Reader(file_limit=64*1024*1024))
        (path/"final-report/report.json").write_text("{}")
        with self.assertRaises(ValueError):load_daily_packet(path,Reader())
        path=self.daily([self.study(era="unverified-pid")],"other")
        with self.assertRaises(ValueError):load_daily_packet(path,Reader())

    def test_source_exposure_requires_actual_receipt(self):
        s=self.study(receipt_verified=False)
        self.assertEqual(exposure_basis(self.case,s),[])
        s=self.study();self.assertIn("verified_anchor_source_interval",exposure_basis(self.case,s))
        s["pages"][0]["revision"]["sha256"]="b"*64
        self.assertEqual(exposure_basis(self.case,s),["changed_source_revision_requires_review"])

    def test_daily_verification_receipt_required_and_bound(self):
        path=self.daily([self.study()]);(path/"verification.json").unlink()
        with self.assertRaises(OSError):load_daily_packet(path,Reader())
        path=self.daily([self.study()],"wrongreceipt")
        v=self.put(path/"verification.json",dict(report_sha256="different",replay_identical=True))
        m=json.loads((path/"packet-manifest.json").read_text());m["verification.json"]=sha(v.read_bytes());self.put(path/"packet-manifest.json",m)
        with self.assertRaises(ValueError):load_daily_packet(path,Reader())

    def test_changed_revision_is_unresolved_not_guessed_exposure(self):
        s=self.study();s["pages"][0]["revision"]["sha256"]="new_revision"
        path=self.daily([s]);result=analyze_durable(self.p,[path],self.start+10)
        c=result["cases"]["worker-single-item"]
        self.assertEqual(c["selected"],[]);self.assertEqual(c["status"],"source_revision_review_required")
        self.assertFalse(c["selection_final"]);self.assertEqual(c["revision_review_candidates"][0]["generation_id"],"g1")

    def test_first_three_and_two_followups_not_future_or_quality_selected(self):
        rows=[self.study(i) for i in [1,2,3,4,5,6,7*86400+1]]
        path=self.daily(rows)
        result=analyze_durable(self.p,[path],self.start+7*86400+2)
        c=result["cases"]["worker-single-item"]
        self.assertEqual([x["generation_id"] for x in c["selected"]],["g1","g2","g3"])
        self.assertEqual(c["followups"][0]["next_relevant_generations"],["g2","g3"])
        self.assertEqual(c["correction"],"not_adjudicated")
        self.assertEqual(len(result["notebook_versions"]),7)

    def test_all_intervening_notebooks_and_null_notes_preserved(self):
        rows=[self.study(1),self.study(2,pages=[]),self.study(3)]
        path=self.daily(rows);d=analyze_durable(self.p,[path],self.start+10)
        self.assertEqual(len(d["notebook_versions"]),3)
        self.assertEqual(d["cases"]["worker-single-item"]["eligible_exposures"],2)

    def test_private_writing_does_not_qualify(self):
        self.assertEqual(exposure_basis(self.case,self.study(actual_route="extended_writing")),[])

    def test_future_timestamp_cannot_enter_notebook_or_exposure(self):
        path=self.daily([self.study(1),self.study(100)])
        result=analyze_durable(self.p,[path],self.start+10)
        self.assertEqual(result["unique_generations"],1)
        self.assertEqual([x["generation_id"] for x in result["notebook_versions"]],["g1"])

    def test_duplicate_generation_changes_and_packet_cap(self):
        p1=self.daily([self.study()],"a");p2=self.daily([self.study(response_sha256="changed")],"b")
        with self.assertRaises(ValueError):analyze_durable(self.p,[p1,p2],self.start+10)
        with self.assertRaises(ValueError):analyze_durable(self.p,[p1]*11,self.start+10)

    def test_prose_only_claim_cannot_be_called_durable_saved_correction(self):
        path=self.daily([self.study(i) for i in range(1,4)]);d=analyze_durable(self.p,[path],self.start+10)
        review=dict(schema="durable_correction_review_v1",case="worker-single-item",generation_id="g1",response_sha256="q"*64,quote="receive loop",durable_correction_observed=True)
        with self.assertRaises(ValueError):validate_correction_review(review,self.p,d)

    def test_durable_review_requires_two_exact_later_exposures_and_persistence(self):
        self.p["cases"]["comment-as-call"]["historical_storage"]="saved_note"
        note=dict(text="This is a comment.",origin="source",response_sha256="wire-revision")
        rows=[self.study(i) for i in range(1,4)]
        for row in rows[1:]:row["notebook"]["fields"]["note"]=note
        path=self.daily(rows);d=analyze_durable(self.p,[path],self.start+10)
        note_hash=sha(encoded(note))
        review=dict(schema="durable_correction_review_v1",case="comment-as-call",generation_id="g1",response_sha256="q"*64,
            quote="receive loop",durable_correction_observed=True,explicit_supported_revision=True,saved_revision_sha256=note_hash,
            later_relevant_generation_ids=["g2","g3"],later_saved_revision_hashes=[note_hash,note_hash],reassertion_observed=False)
        self.assertTrue(validate_correction_review(review,self.p,d))
        bad=copy.deepcopy(review);bad["saved_revision_sha256"]="invented";bad["later_saved_revision_hashes"]=["invented"]*2
        with self.assertRaises(ValueError):validate_correction_review(bad,self.p,d)
        review["later_relevant_generation_ids"]=["g2","g2"]
        with self.assertRaises(ValueError):validate_correction_review(review,self.p,d)


if __name__=="__main__":unittest.main()
