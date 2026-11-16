use super::*;
use reservoir_core::sustained::*;
use std::path::Path;

fn peer_config(group: &str, participant: &str, peers: &[&str]) -> SustainedConfig {
    SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        control_feedback: Some(SustainedControlFeedback::DiagnosticV1),
        peer_reading: Some(SustainedPeerConfig {
            version: SustainedPeerVersion::LatestAppliedV1,
            group: group.into(),
            participant: participant.into(),
            peers: peers.iter().map(|s| s.to_string()).collect(),
        }),
        ..config(40, 3)
    }
}
fn create(
    base: &Path,
    app: &str,
    config: SustainedConfig,
) -> (SustainedState, String, String, u64) {
    let s = SustainedState::new(
        base.join(format!("research.reservoir.scope.{app}"))
            .join("sustained-v1"),
    );
    let m = s.create("create".into(), config).unwrap().summary.unwrap();
    let epoch = arm(&s);
    (s, m.session_id, m.generation, epoch)
}
fn next(s: &SustainedState, epoch: u64) -> Box<SustainedPendingLanguage> {
    for _ in 0..100 {
        match s.worker_boundary(epoch).unwrap() {
            Work::Provider(p, _, _permit) => return p,
            Work::Continue(_) => {}
            _ => panic!("expected writing boundary"),
        }
    }
    panic!("writing boundary not reached")
}
fn settle_and_apply(s: &SustainedState, epoch: u64, p: &SustainedPendingLanguage, text: &str) {
    s.settle(
        epoch,
        p.attempt_id,
        Ok(LanguageResponse {
            text: text.into(),
            ..answer()
        }),
        None,
        1,
    )
    .unwrap();
    for _ in 0..10 {
        if s.lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .committed
            .state
            .step
            > p.observed_step
        {
            return;
        }
        assert!(matches!(
            s.worker_boundary(epoch).unwrap(),
            Work::Continue(_)
        ));
    }
    panic!("application not committed")
}
#[test]
fn peer_snapshot_precedes_dispatch_and_replays_without_the_source() {
    let d = tempfile::tempdir().unwrap();
    let (g, gid, gg, ge) = create(
        d.path(),
        "peer-reader",
        peer_config("cohort", "gemma", &["glm", "mistral"]),
    );
    let (l, lid, _, le) = create(
        d.path(),
        "peer-source",
        peer_config("cohort", "glm", &["gemma"]),
    );
    let p = next(&l, le);
    settle_and_apply(&l, le, &p, "OLDER PEER WRITING\nNEXT: NONE");
    let path = l.shared.store.root.join(&lid).join("manifest.json");
    let before = fs::read(&path).unwrap();
    let request = next(&g, ge);
    assert!(!request.prompt.contains("OLDER PEER WRITING"));
    assert_eq!(fs::read(&path).unwrap(), before);
    let p = next(&l, le);
    settle_and_apply(&l, le, &p, "NEWER PEER WRITING\nNEXT: NONE");
    settle_and_apply(
        &g,
        ge,
        &request,
        "I will read the preceding peers.\nNEXT: READ_PEERS",
    );
    let later = next(&g, ge);
    assert!(later.prompt.contains("OLDER PEER WRITING"));
    assert!(!later.prompt.contains("NEWER PEER WRITING"));
    let state = g.get("view".into(), None).unwrap().summary.unwrap();
    let read = state.actions.unwrap().peer_read.unwrap();
    assert_eq!(
        read.snapshot.peers[0]
            .entry
            .as_ref()
            .unwrap()
            .manifest_sha256,
        crate::files::digest(&before)
    );
    assert!(read.snapshot.peers[1].entry.is_none());
    // Retain a settled final boundary, then take the source away entirely.
    settle_and_apply(&g, ge, &later, "I can retain that distinction.\nNEXT: NONE");
    drop(l);
    fs::rename(
        d.path().join("research.reservoir.scope.peer-source"),
        d.path().join("retired-source"),
    )
    .unwrap();
    assert!(g.shared.store.verify(&gid).is_ok());
    let exports = d.path().join("exports");
    fs::create_dir(&exports).unwrap();
    assert_eq!(
        g.export(&gid, &gg, None, &exports, &[])
            .unwrap()
            .1
            .journal_count,
        2
    );
    let result = next(&g, ge);
    assert!(result.prompt.contains("OLDER PEER WRITING"));
    let snapshot = g
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .captured
        .unwrap();
    assert!(snapshot.peers.iter().all(|p| p.entry.is_none()));
}
#[test]
fn ambiguous_foreign_unapplied_and_nonreciprocal_sources_are_unavailable() {
    let d = tempfile::tempdir().unwrap();
    let (g, _, _, ge) = create(d.path(), "reader", peer_config("cohort", "gemma", &["glm"]));
    let (_foreign, _, _, _) = create(
        d.path(),
        "foreign",
        peer_config("another-cohort", "glm", &["gemma"]),
    );
    let p = next(&g, ge);
    assert!(g
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .captured
        .unwrap()
        .peers[0]
        .entry
        .is_none());
    settle_and_apply(&g, ge, &p, "None yet.\nNEXT: READ_PEERS");
    let (a, _, _, ae) = create(
        d.path(),
        "source-a",
        peer_config("cohort", "glm", &["gemma"]),
    );
    let ap = next(&a, ae);
    a.settle(
        ae,
        ap.attempt_id,
        Ok(LanguageResponse {
            text: "UNAPPLIED\nNEXT: NONE".into(),
            ..answer()
        }),
        None,
        1,
    )
    .unwrap();
    let p = next(&g, ge);
    assert!(g
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .captured
        .unwrap()
        .peers[0]
        .entry
        .is_none());
    settle_and_apply(&g, ge, &p, "None applied.\nNEXT: READ_PEERS");
    // A second exact participant is a conflict, even if one candidate is older.
    let (_b, _, _, _) = create(
        d.path(),
        "source-b",
        peer_config("cohort", "glm", &["other"]),
    );
    next(&g, ge);
    let snapshot = g
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .captured
        .unwrap();
    assert!(snapshot.peers[0]
        .unavailable
        .as_ref()
        .unwrap()
        .contains("Multiple sessions"));
}
#[test]
fn damaged_peer_checkpoint_and_linked_store_never_supply_text() {
    let d = tempfile::tempdir().unwrap();
    let (g, _, _, ge) = create(d.path(), "reader", peer_config("cohort", "gemma", &["glm"]));
    let (l, lid, _, le) = create(d.path(), "source", peer_config("cohort", "glm", &["gemma"]));
    let p = next(&l, le);
    settle_and_apply(&l, le, &p, "Source.\nNEXT: NONE");
    let manifest: Manifest = serde_json::from_slice(
        &fs::read(l.shared.store.root.join(&lid).join("manifest.json")).unwrap(),
    )
    .unwrap();
    let cp_path = l
        .shared
        .store
        .root
        .join(&lid)
        .join("checkpoints")
        .join(format!("{}.json", manifest.checkpoint_sha256));
    let cp_bytes = fs::read(&cp_path).unwrap();
    fs::write(
        l.shared
            .store
            .root
            .join(&lid)
            .join("checkpoints")
            .join(format!("{}.json", manifest.checkpoint_sha256)),
        b"damaged",
    )
    .unwrap();
    next(&g, ge);
    let snapshot = g
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .captured
        .unwrap();
    assert!(snapshot.peers[0].entry.is_none());
    #[cfg(unix)]
    {
        fs::write(&cp_path, &cp_bytes).unwrap();
        let retired = d.path().join("retired-source");
        fs::rename(d.path().join("research.reservoir.scope.source"), &retired).unwrap();
        let link = d.path().join("research.reservoir.scope.link");
        std::os::unix::fs::symlink(&retired, link).unwrap();
        // Discovery must ignore linked app roots; it never traverses an arbitrary linked target.
        let s = g.lock().unwrap();
        let a = s.active.as_ref().unwrap();
        let c = super::super::peers::capture(
            &g.shared.store,
            &a.manifest,
            a.engine.pending_language().unwrap(),
        );
        assert!(c.peers[0].entry.is_none());
    }
}
