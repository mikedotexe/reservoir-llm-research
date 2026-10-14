use super::*;
use reservoir_core::session::{ProviderPromptEvaluation, ProviderPromptEvaluationIssue};
use serde_json::{json, Value};

fn response_at_boundary(
    response: LanguageResponse,
) -> (tempfile::TempDir, SustainedState, String, String, u64) {
    let (d, s, id, generation) = setup(4, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let Work::Provider(pending) = s.worker_boundary(epoch).unwrap() else {
        panic!("missing held request")
    };
    s.settle(epoch, pending.attempt_id, Ok(response), 1)
        .unwrap();
    (d, s, id, generation, epoch)
}

#[test]
fn prompt_evaluation_metadata_survives_save_export_restore_without_changing_eligibility() {
    for metadata in [
        None,
        Some(ProviderPromptEvaluation::Reported { count: u64::MAX }),
        Some(ProviderPromptEvaluation::Unusable {
            reason: ProviderPromptEvaluationIssue::WrongType,
        }),
    ] {
        let mut response = answer();
        response.provider_prompt_evaluation = metadata.clone();
        let (d, s, id, generation, epoch) = response_at_boundary(response);
        let view = s.inspect("pending".into(), &id).unwrap();
        let wire = serde_json::to_value(&view).unwrap();
        let expected = metadata.as_ref().map(|v| {
            serde_json::to_value(sustained_store::ProviderPromptEvaluationView::from(v)).unwrap()
        });
        assert_eq!(
            wire["checkpoint"]["state"]["phase"]["value"]["response"]
                .get("providerPromptEvaluation"),
            expected.as_ref()
        );
        assert_eq!(
            wire["receivedResponses"]["entries"][0].get("providerPromptEvaluation"),
            expected.as_ref()
        );
        assert_eq!(wire["receivedResponses"]["entries"][0]["attemptId"], "1");
        assert_eq!(wire["receivedResponses"]["entries"][0]["observedStep"], "3");
        assert_eq!(wire["receivedResponses"]["entries"][0]["tokenCount"], "18");
        s.pause("pause".into(), &id, &generation).unwrap();
        drive(&s, epoch);
        let verified = s.shared.store.verify(&id).unwrap();
        assert_eq!(verified.report.journal_count, 1);
        assert!(matches!(
            verified.checkpoint.state.phase,
            SustainedPhase::Prepared(_)
        ));
        let entry = s.lock().unwrap().active.as_ref().unwrap().catalog[0]
            .entry_id
            .clone();
        let journal = s
            .journal("journal".into(), &id, &generation, &entry)
            .unwrap();
        assert_eq!(
            journal.journal.get("providerPromptEvaluation"),
            expected.as_ref()
        );
        let stored = s.shared.store.read_journal(&id, &entry).unwrap();
        assert_eq!(stored.pending.response.provider_prompt_evaluation, metadata);
        let exports = d.path().join("exports");
        fs::create_dir(&exports).unwrap();
        let (revision, report) = s.export(&id, &generation, None, &exports, &[]).unwrap();
        let exported = exports.join(format!("{id}-{generation}-{revision}"));
        assert_eq!(
            sustained_store::verify_bundle(&exported)
                .unwrap()
                .manifest_sha256,
            report.manifest_sha256
        );
        let name = format!("journals/{entry}.json");
        let original = fs::read(s.shared.store.path(&id).unwrap().join(&name)).unwrap();
        assert_eq!(fs::read(exported.join(&name)).unwrap(), original);
        if metadata.is_none() {
            assert!(!String::from_utf8(original)
                .unwrap()
                .contains("providerPromptEvaluation"));
        }
        let restored = SustainedState::new(d.path().join("store"));
        let update = restored
            .resume("restore".into(), &id, &generation, &revision)
            .unwrap();
        let m = update.summary.unwrap();
        assert_eq!(m.phase, "paused");
        assert_eq!(
            restored
                .journal("restored".into(), &id, &m.generation, &entry)
                .unwrap()
                .journal
                .get("providerPromptEvaluation"),
            expected.as_ref()
        );
    }
}

#[test]
fn prompt_evaluation_incomplete_attempt_is_inspectable_but_never_a_saved_journal() {
    let mut response = answer();
    response.complete = false;
    response.stop_reason = Some("終".repeat(257));
    response.token_count = Some(i64::MAX);
    response.provider_prompt_evaluation = Some(ProviderPromptEvaluation::Reported {
        count: 9_007_199_254_740_993,
    });
    let (d, s, id, generation, _) = response_at_boundary(response);
    let detail = s.inspect("blocked".into(), &id).unwrap();
    assert_eq!(detail.report.journal_count, 0);
    assert!(matches!(
        s.shared.store.verify(&id).unwrap().checkpoint.state.phase,
        SustainedPhase::Blocked(_)
    ));
    let v = serde_json::to_value(detail).unwrap();
    assert_eq!(v["receivedResponses"]["total"], 1);
    assert_eq!(v["receivedResponses"]["entries"][0]["complete"], false);
    assert_eq!(
        v["receivedResponses"]["entries"][0]["stopReason"],
        "終".repeat(256)
    );
    assert_eq!(
        v["receivedResponses"]["entries"][0]["stopReasonTruncated"],
        true
    );
    assert_eq!(
        v["receivedResponses"]["entries"][0]["tokenCount"],
        i64::MAX.to_string()
    );
    assert_eq!(
        v["receivedResponses"]["entries"][0]["providerPromptEvaluation"],
        json!({"status":"reported","count":"9007199254740993"})
    );
    assert_eq!(
        s.journal_page("none".into(), &id, &generation, 0, 10)
            .unwrap()
            .total,
        0
    );
    let exports = d.path().join("exports");
    fs::create_dir(&exports).unwrap();
    let (_, report) = s.export(&id, &generation, None, &exports, &[]).unwrap();
    assert_eq!(report.journal_count, 0);
}

#[test]
fn prompt_evaluation_received_response_view_is_newest_fifty_and_reports_truncation() {
    let (_d, s, id, _) = setup(157, 3);
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    let detail = s.inspect("bounded".into(), &id).unwrap();
    let received = detail.received_responses;
    assert_eq!(received.total, 52);
    assert!(received.truncated);
    assert_eq!(received.entries.len(), 50);
    assert_eq!(received.entries.first().unwrap().attempt_id, "52");
    assert_eq!(received.entries.last().unwrap().attempt_id, "3");
}

fn reanchor_links(
    path: &std::path::Path,
    changed_journal: Option<(&str, &str)>,
    mutate_response: bool,
) {
    let manifest_path = path.join("manifest.json");
    let mut manifest: Value = serde_json::from_slice(&fs::read(&manifest_path).unwrap()).unwrap();
    let mut previous = Value::Null;
    let mut changed = false;
    for n in 1..=manifest["segmentCount"].as_u64().unwrap() {
        let name = path.join(format!("segments/segment-{n:08}.json"));
        let mut link: Value = serde_json::from_slice(&fs::read(&name).unwrap()).unwrap();
        link["previousSha256"] = previous.clone();
        if let Some((entry, hash)) = changed_journal {
            if link["journalSha256s"].get(entry).is_some() {
                link["journalSha256s"][entry] = hash.into();
            }
        }
        if mutate_response {
            for event in link["segment"]["events"].as_array_mut().unwrap() {
                if event["kind"]["type"] == "languageReceived" {
                    event["kind"]["data"]["response"]["providerPromptEvaluation"]["count"] =
                        json!(2);
                    changed = true;
                }
            }
        }
        let bytes = serde_json::to_vec(&link).unwrap();
        previous = crate::files::digest(&bytes).into();
        fs::write(name, bytes).unwrap();
    }
    assert!(!mutate_response || changed);
    manifest["lastSegmentSha256"] = previous;
    fs::write(manifest_path, serde_json::to_vec(&manifest).unwrap()).unwrap();
}

#[test]
fn prompt_evaluation_journal_and_event_mutations_fail_even_with_outer_hashes_reanchored() {
    for change_journal in [true, false] {
        let mut response = answer();
        response.provider_prompt_evaluation = Some(ProviderPromptEvaluation::Reported { count: 1 });
        let (_d, s, id, generation, epoch) = response_at_boundary(response);
        s.pause("pause".into(), &id, &generation).unwrap();
        drive(&s, epoch);
        let path = s.shared.store.path(&id).unwrap();
        let entry = s.lock().unwrap().active.as_ref().unwrap().catalog[0]
            .entry_id
            .clone();
        if change_journal {
            let file = path.join(format!("journals/{entry}.json"));
            let mut object: Value = serde_json::from_slice(&fs::read(&file).unwrap()).unwrap();
            object["pending"]["response"]["providerPromptEvaluation"]["count"] = json!(2);
            let bytes = serde_json::to_vec(&object).unwrap();
            let hash = crate::files::digest(&bytes);
            fs::write(file, bytes).unwrap();
            reanchor_links(&path, Some((&entry, &hash)), false);
        } else {
            reanchor_links(&path, None, true);
        }
        assert!(
            s.shared.store.verify(&id).is_err(),
            "independent metadata mutation accepted"
        );
    }
}
