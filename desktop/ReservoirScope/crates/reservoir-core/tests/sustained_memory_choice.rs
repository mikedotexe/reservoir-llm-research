//! 0.36.0: which earlier entry a turn returns. `latest` is byte for byte the earlier
//! mechanism; `state-aligned` lets the recurrent state choose among the applied entries by
//! their recorded effect at application; `random` is the seeded control. The prompt text
//! is the same under every policy. Also the watchdog warm-up of the difference channel.
//! 0.38.0: the recent-return window (`memory_recent_exclusion`) and the two-entry prompt
//! version, both off by default and byte for byte absent when off.
//! 0.39.0: the two-entry prompt version without a context line.
use reservoir_core::{math::SplitMix64, session::LanguageResponse, sustained::*};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::HashMap;

fn bytes<T: Serialize>(v: &T) -> Vec<u8> {
    serde_json::to_vec(v).unwrap()
}
fn text<T: Serialize>(v: &T) -> String {
    String::from_utf8(bytes(v)).unwrap()
}
fn hash(data: &[u8]) -> String {
    format!("{:x}", Sha256::digest(data))
}
fn spec(policy: SustainedMemoryPolicy) -> SustainedSpecification {
    SustainedSpecification {
        seed: 7,
        turn_every: 3,
        maximum_steps: 1000,
        maximum_turns: 400,
        sensory_noise_amplitude: DEFAULT_SENSORY_NOISE_AMPLITUDE,
        feedback_scale: DEFAULT_FEEDBACK_SCALE,
        memory_policy: policy,
        ..Default::default()
    }
}
fn checkpoint(s: &SustainedSession) -> SustainedCheckpoint {
    serde_json::from_slice(&bytes(&s.checkpoint())).unwrap()
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = hash(&bytes(&c.state));
}
fn segment(base: &SustainedCheckpoint, s: &SustainedSession) -> SustainedSegment {
    SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base.clone(),
        events: s.events().iter().cloned().collect(),
        final_checkpoint: checkpoint(s),
    }
}
fn acknowledge(s: &mut SustainedSession) {
    if let Some(last) = s.events().back().map(|e| e.id) {
        s.acknowledge_events(last).unwrap();
    }
}
fn cosine(a: &[f64], b: &[f64]) -> Option<f64> {
    if a.is_empty() || a.len() != b.len() {
        return None;
    }
    let dot: f64 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let na = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let nb = b.iter().map(|x| x * x).sum::<f64>().sqrt();
    (na > 0.0 && nb > 0.0).then(|| (dot / (na * nb)).clamp(-1.0, 1.0))
}
/// Distinct replies, so the surface codec gives each entry its own vector and effect.
fn reply(i: usize) -> LanguageResponse {
    let words = [
        "field", "turning", "quiet", "return", "listen", "shelf", "count", "pause", "again",
    ];
    let mut t = String::new();
    for k in 0..(4 + (i * 7) % 9) {
        t.push_str(words[(i + k * 3) % words.len()]);
        t.push_str(if k % 3 == 2 { ". " } else { " " });
    }
    t.push_str(&format!(
        "Entry {i} closes here{}",
        if i.is_multiple_of(2) { "." } else { "!" }
    ));
    LanguageResponse {
        text: t,
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(20),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
/// The worker's side: a journal store that answers every physical reread.
#[derive(Clone, Default)]
struct Store {
    saved: HashMap<String, SustainedJournal>,
    counter: usize,
    choices_on_journals: usize,
}
impl Store {
    fn settle(&mut self, s: &mut SustainedSession) {
        if let Some(m) = s.pending_memory().cloned() {
            let id = m.entry_id().unwrap().to_string();
            s.confirm_memory(&self.saved[&id]).unwrap();
        }
        if let Some(p) = s.pending_language().cloned() {
            s.start_language(p.attempt_id).unwrap();
            self.counter += 1;
            s.confirm_language(p.attempt_id, &reply(self.counter))
                .unwrap();
        }
        if let Some(j) = s.pending_journal().cloned() {
            if j.memory_choice.is_some() {
                self.choices_on_journals += 1;
            }
            let receipt = SustainedSaveReceipt {
                entry_id: j.entry.id.clone(),
                sha256: j.entry.sha256.clone(),
                relative_path: format!("journals/{}.json", j.entry.id),
            };
            s.confirm_saved(&receipt, &j.entry).unwrap();
            self.saved.insert(j.entry.id.clone(), j.entry.clone());
        }
        if let Some(p) = s.prepared_application() {
            let id = p.entry.attempt_id;
            s.authorize_application(id).unwrap();
        }
    }
    fn step(&mut self, s: &mut SustainedSession) -> SustainedFrame {
        self.settle(s);
        s.advance().unwrap()
    }
}

#[test]
fn latest_is_byte_for_byte_the_earlier_mechanism() {
    let spec = spec(SustainedMemoryPolicy::Latest);
    let json = text(&spec);
    assert!(
        !json.contains("memoryPolicy") && !json.contains("Warmup"),
        "{json}"
    );
    let decoded: SustainedSpecification = serde_json::from_slice(&bytes(&spec)).unwrap();
    assert_eq!(decoded.memory_policy, SustainedMemoryPolicy::Latest);
    assert_eq!(decoded.difference_watchdog_warmup, 0);
    assert!(!spec.needs_entry_effect());
    assert_eq!(
        text(&SustainedMemoryPolicy::StateAligned),
        "\"state-aligned\""
    );
    assert_eq!(text(&SustainedMemoryPolicy::Random), "\"random\"");
    assert_eq!(
        SustainedMemoryPolicy::StateAligned.as_str(),
        "state-aligned"
    );
    let base = checkpoint(&SustainedSession::new(spec.clone()).unwrap());
    let mut s = SustainedSession::new(spec).unwrap();
    let mut store = Store::default();
    let mut boundaries = 0;
    for _ in 0..40 {
        if let Some(m) = s.pending_memory() {
            boundaries += 1;
            assert!(m.entry.is_some() && m.choice.is_none());
            let t = text(m);
            assert!(t.contains("\"entry\":{") && !t.contains("choice"), "{t}");
        }
        store.step(&mut s);
    }
    assert!(boundaries >= 10);
    assert_eq!(store.choices_on_journals, 0);
    let all = format!(
        "{}{}",
        text(&s.checkpoint()),
        text(&s.events().iter().cloned().collect::<Vec<_>>())
    );
    for key in [
        "appliedEntries",
        "chosenMemory",
        "memoryChoice",
        "memoryPolicy",
        "\"choice\"",
        "entryEffect",
        "memoryRecentExclusion",
        "lastReturnedTurn",
        "excludedRecent",
        "latestShown",
    ] {
        assert!(!all.contains(key), "{key}");
    }
    segment(&base, &s).verify().unwrap();
}

#[test]
fn state_aligned_returns_the_entry_whose_effect_points_along_the_state() {
    let spec = spec(SustainedMemoryPolicy::StateAligned);
    assert!(spec.needs_entry_effect());
    assert!(text(&spec).contains("\"memoryPolicy\":\"state-aligned\""));
    let mut s = SustainedSession::new(spec.clone()).unwrap();
    let mut store = Store::default();
    let mut base = checkpoint(&s);
    let (mut boundaries, mut older, mut tampered) = (0, 0, false);
    for i in 0..60 {
        if i % 20 == 0 {
            acknowledge(&mut s);
            base = checkpoint(&s);
        }
        let c = checkpoint(&s);
        if let Some(m) = s.pending_memory().cloned() {
            boundaries += 1;
            assert!(m.entry.is_none());
            let choice = m.choice.clone().unwrap();
            assert_eq!(choice.policy, SustainedMemoryPolicy::StateAligned);
            let ledger = &c.state.applied_entries;
            assert_eq!(choice.candidates as usize, ledger.len());
            assert_eq!(
                ledger.last().unwrap().id,
                c.state.latest_memory.as_ref().unwrap().entry.id
            );
            assert!(c.state.chosen_memory.is_none());
            let state = &m.observation.state;
            let mut best = ledger.len() - 1;
            let mut best_score = f64::NEG_INFINITY;
            for (k, e) in ledger.iter().enumerate() {
                if let Some(x) = cosine(&e.effect, state) {
                    if x >= best_score {
                        best = k;
                        best_score = x;
                    }
                }
            }
            assert_eq!(choice.entry_id, ledger[best].id);
            assert_eq!(choice.sha256, ledger[best].sha256);
            assert_eq!(choice.applied_step, ledger[best].applied_step);
            assert_eq!(choice.age as usize, ledger.len() - 1 - best);
            assert_eq!(choice.score, cosine(&ledger[best].effect, state));
            assert_eq!(
                m.relative_path,
                format!("journals/{}.json", choice.entry_id)
            );
            assert_eq!(m.entry_id(), Some(choice.entry_id.as_str()));
            if choice.age > 0 {
                older += 1;
            }
            if let Some(other) = store.saved.values().find(|j| j.id != choice.entry_id) {
                // A wrong readback is refused and leaves the boundary unchanged.
                let before = s.checkpoint().sha256;
                assert!(s.confirm_memory(other).is_err());
                assert_eq!(s.checkpoint().sha256, before);
                if !tampered {
                    // A pending choice the state would not make fails validation.
                    let mut t = checkpoint(&s);
                    if let SustainedPhase::Memory(p) = &mut t.state.phase {
                        p.choice.as_mut().unwrap().age += 1;
                    }
                    rehash(&mut t);
                    assert!(t.validate().is_err());
                    let mut t = checkpoint(&s);
                    if let SustainedPhase::Memory(p) = &mut t.state.phase {
                        p.choice.as_mut().unwrap().entry_id = other.id.clone();
                        p.choice.as_mut().unwrap().sha256 = other.sha256.clone();
                        p.relative_path = format!("journals/{}.json", other.id);
                    }
                    rehash(&mut t);
                    assert!(t.validate().is_err());
                    let mut t = checkpoint(&s);
                    if let SustainedPhase::Memory(p) = &mut t.state.phase {
                        p.entry = Some(other.clone());
                        p.choice = None;
                    }
                    rehash(&mut t);
                    assert!(t.validate().is_err());
                    tampered = true;
                }
            }
            // The right readback becomes the prompt's memory, with the choice recorded.
            let chosen = store.saved[&choice.entry_id].clone();
            s.confirm_memory(&chosen).unwrap();
            let p = s.pending_language().unwrap().clone();
            assert_eq!(p.memory.as_ref().unwrap().entry.id, choice.entry_id);
            assert_eq!(p.memory.as_ref().unwrap().applied_step, choice.applied_step);
            assert_eq!(bytes(&p.memory_choice), bytes(&Some(choice.clone())));
            assert!(p.prompt.contains(&chosen.text));
            if let Some(other) = store.saved.values().find(|j| j.id != choice.entry_id) {
                assert!(!p.prompt.contains(&other.text));
            }
            let after = checkpoint(&s);
            assert_eq!(
                after.state.chosen_memory.as_ref().unwrap().entry.id,
                choice.entry_id
            );
            after.validate().unwrap();
        }
        store.step(&mut s);
    }
    assert!(boundaries >= 15, "{boundaries}");
    assert!(older >= 1, "the state never chose an older entry");
    assert!(tampered);
    assert_eq!(store.choices_on_journals, boundaries);
    checkpoint(&s).validate().unwrap();
    segment(&base, &s).verify().unwrap();

    // Restored continuations follow the uninterrupted run exactly, choices included.
    let mut straight = SustainedSession::new(spec.clone()).unwrap();
    let mut restored = SustainedSession::new(spec).unwrap();
    let (mut sa, mut sb) = (Store::default(), Store::default());
    for i in 0..45 {
        if i % 15 == 0 {
            acknowledge(&mut straight);
        }
        let a = sa.step(&mut straight);
        if i % 4 == 0 {
            restored = SustainedSession::restore(checkpoint(&restored)).unwrap();
        }
        let b = sb.step(&mut restored);
        assert_eq!(bytes(&a), bytes(&b), "step {}", i + 1);
    }
    assert_eq!(bytes(&straight.checkpoint()), bytes(&restored.checkpoint()));
}

#[test]
fn random_is_a_seeded_reproducible_control() {
    let spec = spec(SustainedMemoryPolicy::Random);
    let mut a = SustainedSession::new(spec.clone()).unwrap();
    let mut b = SustainedSession::new(spec.clone()).unwrap();
    let (mut sa, mut sb) = (Store::default(), Store::default());
    let mut ages = Vec::new();
    for i in 0..60 {
        if i % 20 == 0 {
            acknowledge(&mut a);
            acknowledge(&mut b);
        }
        let c = checkpoint(&a);
        if let Some(m) = a.pending_memory().cloned() {
            let choice = m.choice.unwrap();
            assert_eq!(choice.policy, SustainedMemoryPolicy::Random);
            assert!(choice.score.is_none());
            let n = c.state.applied_entries.len() as u64;
            let mut rng = SplitMix64::new(spec.seed ^ MEMORY_CHOICE_SEED ^ m.observed_step);
            let index = (rng.next_u64() % n) as usize;
            assert_eq!(choice.entry_id, c.state.applied_entries[index].id);
            assert_eq!(choice.age as usize, n as usize - 1 - index);
            ages.push(choice.age);
        }
        let fa = sa.step(&mut a);
        let fb = sb.step(&mut b);
        assert_eq!(bytes(&fa), bytes(&fb));
    }
    assert!(ages.len() >= 15);
    assert!(ages.iter().any(|&x| x > 0) && ages.contains(&0), "{ages:?}");
    assert_eq!(bytes(&a.checkpoint()), bytes(&b.checkpoint()));
    checkpoint(&a).validate().unwrap();
}

#[test]
fn the_ledger_is_bounded() {
    let spec = SustainedSpecification {
        turn_every: 1,
        ..spec(SustainedMemoryPolicy::StateAligned)
    };
    let mut s = SustainedSession::new(spec).unwrap();
    let mut store = Store::default();
    let mut first = None;
    for i in 0..(MEMORY_LEDGER_CAP + 10) {
        if i % 15 == 0 {
            acknowledge(&mut s);
        }
        store.step(&mut s);
        if first.is_none() {
            first = checkpoint(&s)
                .state
                .applied_entries
                .first()
                .map(|e| e.id.clone());
        }
    }
    let c = checkpoint(&s);
    assert_eq!(c.state.applied_entries.len(), MEMORY_LEDGER_CAP);
    assert!(first.is_some());
    assert_ne!(c.state.applied_entries.first().map(|e| e.id.clone()), first);
    assert_eq!(
        c.state.applied_entries.last().unwrap().id,
        c.state.latest_memory.as_ref().unwrap().entry.id
    );
    c.validate().unwrap();
    let mut t = checkpoint(&s);
    t.state.applied_entries.pop();
    rehash(&mut t);
    assert!(
        t.validate().is_err(),
        "a ledger not ending with the latest entry"
    );
    let mut t = checkpoint(&s);
    t.state.applied_entries.clear();
    rehash(&mut t);
    assert!(
        t.validate().is_err(),
        "a missing ledger under a choosing policy"
    );
}

#[test]
fn the_watchdog_warm_up_delays_the_fill_ring() {
    assert!(SustainedSpecification {
        difference_watchdog_warmup: MAX_STEPS + 1,
        ..Default::default()
    }
    .validate()
    .is_err());
    let spec = SustainedSpecification {
        difference_gain: 0.1,
        difference_watchdog_fill_std: 0.0,
        difference_watchdog_warmup: 100,
        turn_every: 30,
        ..spec(SustainedMemoryPolicy::Latest)
    };
    assert!(text(&spec).contains("\"differenceWatchdogWarmup\":100"));
    let mut s = SustainedSession::new(spec).unwrap();
    let mut store = Store::default();
    let mut frames = Vec::new();
    for i in 1..=200 {
        if i % 30 == 0 {
            acknowledge(&mut s);
        }
        frames.push(store.step(&mut s));
        if i == 50 {
            let c = checkpoint(&s);
            assert!(c.state.difference_fill_window.is_empty());
            c.validate().unwrap();
            let mut t = checkpoint(&s);
            t.state.difference_fill_window.push(50.0);
            rehash(&mut t);
            assert!(t.validate().is_err(), "a ring entry during the warm-up");
        }
        if i == 150 {
            assert_eq!(checkpoint(&s).state.difference_fill_window.len(), 50);
        }
    }
    let dropped = frames
        .iter()
        .find(|f| f.difference_gain_dropped.is_some())
        .unwrap();
    assert_eq!(dropped.step, 190);
    assert_eq!(
        dropped.difference_gain_dropped.as_ref().unwrap().reason,
        DIFFERENCE_DROP_FILL_STD
    );
    assert!(frames
        .iter()
        .filter(|f| f.step < 190)
        .all(|f| f.difference_gain_used == 0.1 && f.difference_input.len() == 48));
    checkpoint(&s).validate().unwrap();
}

#[test]
fn residual_and_random_older_choose_among_the_older_entries() {
    for policy in [
        SustainedMemoryPolicy::StateResidual,
        SustainedMemoryPolicy::RandomOlder,
    ] {
        let spec = spec(policy);
        assert!(text(&spec).contains(policy.as_str()));
        let mut s = SustainedSession::new(spec.clone()).unwrap();
        let mut store = Store::default();
        let mut base = checkpoint(&s);
        let (mut boundaries, mut single) = (0, 0);
        for i in 0..60 {
            if i % 20 == 0 {
                acknowledge(&mut s);
                base = checkpoint(&s);
            }
            let c = checkpoint(&s);
            if let Some(m) = s.pending_memory().cloned() {
                boundaries += 1;
                let choice = m.choice.clone().unwrap();
                assert_eq!(choice.policy, policy);
                let ledger = &c.state.applied_entries;
                let n = ledger.len();
                assert_eq!(choice.candidates as usize, n);
                if n == 1 {
                    single += 1;
                    assert_eq!(choice.age, 0);
                } else {
                    assert!(
                        choice.age >= 1,
                        "{policy:?} returned the latest with {n} candidates"
                    );
                    let expected = match policy {
                        SustainedMemoryPolicy::RandomOlder => {
                            let mut rng =
                                SplitMix64::new(spec.seed ^ MEMORY_CHOICE_SEED ^ m.observed_step);
                            (rng.next_u64() % (n as u64 - 1)) as usize
                        }
                        _ => {
                            let residual = project_out(&m.observation.state, &ledger[n - 1].effect);
                            let dot: f64 = residual
                                .iter()
                                .zip(&ledger[n - 1].effect)
                                .map(|(a, b)| a * b)
                                .sum();
                            assert!(dot.abs() < 1e-9, "the latest push is projected out");
                            let mut best = n - 2;
                            let mut best_score = f64::NEG_INFINITY;
                            for (k, e) in ledger.iter().enumerate().take(n - 1) {
                                if let Some(x) = cosine(&e.effect, &residual) {
                                    if x >= best_score {
                                        best = k;
                                        best_score = x;
                                    }
                                }
                            }
                            assert_eq!(choice.score, cosine(&ledger[best].effect, &residual));
                            best
                        }
                    };
                    assert_eq!(choice.entry_id, ledger[expected].id);
                    assert_eq!(choice.age as usize, n - 1 - expected);
                }
            }
            store.step(&mut s);
        }
        assert!(boundaries >= 15 && single == 1, "{boundaries} {single}");
        checkpoint(&s).validate().unwrap();
        segment(&base, &s).verify().unwrap();
    }
    assert_eq!(project_out(&[1.0, 2.0], &[0.0, 0.0]), vec![1.0, 2.0]);
    assert!(project_out(&[1.0, 1.0], &[1.0, 0.0])[0].abs() < 1e-12);
    assert_eq!(
        text(&SustainedMemoryPolicy::StateResidual),
        "\"state-residual\""
    );
    assert_eq!(
        text(&SustainedMemoryPolicy::RandomOlder),
        "\"random-older\""
    );
}

// 0.38.0: the recent-return window and the two-entry prompt version.

fn windowed(policy: SustainedMemoryPolicy, window: u64) -> SustainedSpecification {
    SustainedSpecification {
        memory_recent_exclusion: window,
        ..spec(policy)
    }
}
fn two_entry(policy: SustainedMemoryPolicy) -> SustainedSpecification {
    SustainedSpecification {
        prompt_version: SustainedPromptVersion::InertPlainContractTwoV1,
        ..spec(policy)
    }
}
fn two_entry_no_tag(policy: SustainedMemoryPolicy) -> SustainedSpecification {
    SustainedSpecification {
        prompt_version: SustainedPromptVersion::InertPlainContractTwoNoTagV1,
        ..spec(policy)
    }
}
/// The chooser's expected index under a window, recomputed from a checkpoint's ledger:
/// the older entries not returned within the window (all of them when that leaves none),
/// then the seeded draw or the residual alignment over them; and the excluded count.
fn expected_index(
    policy: SustainedMemoryPolicy,
    c: &SustainedCheckpoint,
    m: &SustainedPendingMemory,
    seed: u64,
) -> (usize, u64) {
    let ledger = &c.state.applied_entries;
    let n = ledger.len();
    let (t, k) = (
        c.state.turn_cursor,
        c.state.specification.memory_recent_exclusion,
    );
    let recent = |e: &SustainedAppliedEntry| {
        k > 0
            && e.last_returned_turn
                .is_some_and(|r| t.saturating_sub(r) <= k)
    };
    let excluded = ledger[..n - 1].iter().filter(|e| recent(e)).count() as u64;
    let mut kept: Vec<usize> = (0..n - 1).filter(|&i| !recent(&ledger[i])).collect();
    if kept.is_empty() {
        kept = (0..n - 1).collect();
    }
    let index = match policy {
        SustainedMemoryPolicy::RandomOlder => {
            let mut rng = SplitMix64::new(seed ^ MEMORY_CHOICE_SEED ^ m.observed_step);
            kept[(rng.next_u64() % kept.len() as u64) as usize]
        }
        _ => {
            let residual = project_out(&m.observation.state, &ledger[n - 1].effect);
            let mut best = *kept.last().unwrap();
            let mut best_score = f64::NEG_INFINITY;
            for &i in &kept {
                if let Some(x) = cosine(&ledger[i].effect, &residual) {
                    if x >= best_score {
                        best = i;
                        best_score = x;
                    }
                }
            }
            best
        }
    };
    (index, excluded)
}
/// `Store::settle` with every pending language and journal object's text collected.
fn settle_collect(store: &mut Store, s: &mut SustainedSession, sink: &mut String) {
    if let Some(m) = s.pending_memory().cloned() {
        sink.push_str(&text(&m));
        let id = m.entry_id().unwrap().to_string();
        s.confirm_memory(&store.saved[&id]).unwrap();
    }
    if let Some(p) = s.pending_language().cloned() {
        sink.push_str(&text(&p));
        s.start_language(p.attempt_id).unwrap();
        store.counter += 1;
        s.confirm_language(p.attempt_id, &reply(store.counter))
            .unwrap();
    }
    if let Some(j) = s.pending_journal().cloned() {
        sink.push_str(&text(&j));
        let receipt = SustainedSaveReceipt {
            entry_id: j.entry.id.clone(),
            sha256: j.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", j.entry.id),
        };
        s.confirm_saved(&receipt, &j.entry).unwrap();
        store.saved.insert(j.entry.id.clone(), j.entry.clone());
    }
    if let Some(p) = s.prepared_application() {
        let id = p.entry.attempt_id;
        s.authorize_application(id).unwrap();
    }
}
const V37_WITNESS: &[u8] =
    include_bytes!("fixtures/sustained-prompts/v37-state-residual-segment.json");

#[test]
fn recent_exclusion_is_absent_at_zero_and_needs_an_older_policy() {
    for policy in [
        SustainedMemoryPolicy::Latest,
        SustainedMemoryPolicy::StateAligned,
        SustainedMemoryPolicy::Random,
    ] {
        assert!(windowed(policy, 1).validate().is_err(), "{policy:?}");
        assert!(SustainedSession::new(windowed(policy, 1)).is_err());
    }
    for policy in [
        SustainedMemoryPolicy::StateResidual,
        SustainedMemoryPolicy::RandomOlder,
    ] {
        assert!(policy.chooses_older());
        assert!(windowed(policy, 1).validate().is_ok());
        assert!(windowed(policy, 256).validate().is_ok());
        assert!(windowed(policy, 257).validate().is_err());
        assert!(!text(&spec(policy)).contains("memoryRecentExclusion"));
        assert!(text(&windowed(policy, 3)).contains("\"memoryRecentExclusion\":3"));
        let decoded: SustainedSpecification =
            serde_json::from_slice(&bytes(&windowed(policy, 3))).unwrap();
        assert_eq!(decoded.memory_recent_exclusion, 3);
        // Without a window a run under an older policy writes none of the 0.38.0 keys.
        let base = checkpoint(&SustainedSession::new(spec(policy)).unwrap());
        let mut s = SustainedSession::new(spec(policy)).unwrap();
        let mut store = Store::default();
        let mut all = String::new();
        for _ in 0..30 {
            settle_collect(&mut store, &mut s, &mut all);
            s.advance().unwrap();
        }
        all.push_str(&text(&s.checkpoint()));
        all.push_str(&text(&s.events().iter().cloned().collect::<Vec<_>>()));
        assert!(all.contains("\"memoryChoice\":{"));
        for key in [
            "memoryRecentExclusion",
            "lastReturnedTurn",
            "excludedRecent",
            "latestShown",
        ] {
            assert!(!all.contains(key), "{policy:?}: {key}");
        }
        segment(&base, &s).verify().unwrap();
    }
    assert!(!SustainedMemoryPolicy::Latest.chooses_older());
    assert!(!SustainedMemoryPolicy::StateAligned.chooses_older());
    assert!(!SustainedMemoryPolicy::Random.chooses_older());

    // A state-residual segment recorded by the 0.37.0 binary, before the window and the
    // two-entry version existed, re-serialises byte for byte and validates under the new
    // code: its ledger carries no marks and its pending choice no exclusion count.
    assert_eq!(
        hash(V37_WITNESS),
        "2ea0deb306c6cf745e488387afdd75d71c6db7e44814c3ca8074cfb8a46c7faa"
    );
    let witness: SustainedSegment = serde_json::from_slice(V37_WITNESS).unwrap();
    assert_eq!(bytes(&witness), V37_WITNESS.to_vec());
    witness.initial_checkpoint.validate().unwrap();
    witness.final_checkpoint.validate().unwrap();
    let st = &witness.final_checkpoint.state;
    assert_eq!(st.step, 15);
    assert_eq!(st.specification.memory_recent_exclusion, 0);
    assert_eq!(
        st.specification.prompt_version,
        SustainedPromptVersion::InertPlainContractV1
    );
    assert_eq!(st.applied_entries.len(), 4);
    assert!(st
        .applied_entries
        .iter()
        .all(|e| e.last_returned_turn.is_none()));
    match &st.phase {
        SustainedPhase::Memory(p) => {
            let c = p.choice.as_ref().unwrap();
            assert_eq!(c.policy, SustainedMemoryPolicy::StateResidual);
            assert_eq!((c.age, c.candidates, c.excluded_recent), (3, 4, 0));
        }
        other => panic!("witness ends in {other:?}"),
    }
}

#[test]
#[cfg_attr(not(all(target_os = "macos", target_arch = "aarch64")), ignore)]
fn the_0_37_0_witness_segment_replays_exactly_on_the_recording_host() {
    let witness: SustainedSegment = serde_json::from_slice(V37_WITNESS).unwrap();
    witness.verify().unwrap();
}

#[test]
fn recent_exclusion_keeps_a_returned_entry_out_for_k_turns() {
    for policy in [
        SustainedMemoryPolicy::RandomOlder,
        SustainedMemoryPolicy::StateResidual,
    ] {
        let spec = windowed(policy, 2);
        let mut s = SustainedSession::new(spec.clone()).unwrap();
        let mut store = Store::default();
        let mut base = checkpoint(&s);
        let (mut boundaries, mut lapses, mut excluded_total, mut marked) = (0, 0, 0, 0);
        let mut expect_mark: Option<(String, u64)> = None;
        for i in 0..90 {
            if i % 20 == 0 {
                acknowledge(&mut s);
                base = checkpoint(&s);
            }
            let c = checkpoint(&s);
            if let Some((id, turn)) = expect_mark.take() {
                // The entry returned at the previous boundary was marked at the
                // application of the journal written with it in view, with that turn.
                let e = c.state.applied_entries.iter().find(|e| e.id == id).unwrap();
                assert_eq!(e.last_returned_turn, Some(turn), "{policy:?} at step {i}");
                marked += 1;
            }
            if let Some(m) = s.pending_memory().cloned() {
                boundaries += 1;
                let choice = m.choice.clone().unwrap();
                let ledger = &c.state.applied_entries;
                let n = ledger.len();
                assert_eq!(choice.candidates as usize, n);
                if n == 1 {
                    assert_eq!((choice.age, choice.excluded_recent), (0, 0));
                } else {
                    let (expected, excluded) = expected_index(policy, &c, &m, spec.seed);
                    assert_eq!(
                        choice.entry_id, ledger[expected].id,
                        "{policy:?} at step {i}"
                    );
                    assert_eq!(choice.age as usize, n - 1 - expected);
                    assert_eq!(choice.excluded_recent, excluded);
                    assert!(choice.excluded_recent < choice.candidates);
                    if excluded as usize == n - 1 {
                        lapses += 1;
                    } else if let Some(r) = ledger[expected].last_returned_turn {
                        assert!(c.state.turn_cursor - r > 2, "returned within the window");
                    }
                    excluded_total += excluded;
                }
                // Confirmation leaves the ledger untouched; the mark comes at application.
                let before = bytes(&c.state.applied_entries);
                let chosen = store.saved[&choice.entry_id].clone();
                s.confirm_memory(&chosen).unwrap();
                let after = checkpoint(&s);
                assert_eq!(bytes(&after.state.applied_entries), before);
                assert_eq!(
                    after.state.chosen_memory.as_ref().unwrap().entry.id,
                    choice.entry_id
                );
                after.validate().unwrap();
                expect_mark = Some((choice.entry_id.clone(), c.state.turn_cursor));
            }
            store.step(&mut s);
        }
        assert!(boundaries >= 25, "{boundaries}");
        assert_eq!(marked, boundaries);
        assert!(
            lapses >= 1 && excluded_total >= 1,
            "{policy:?}: {lapses} lapses, {excluded_total} excluded"
        );
        checkpoint(&s).validate().unwrap();
        segment(&base, &s).verify().unwrap();

        // Restored continuations follow the uninterrupted run exactly, marks included.
        let mut straight = SustainedSession::new(spec.clone()).unwrap();
        let mut restored = SustainedSession::new(spec.clone()).unwrap();
        let (mut sa, mut sb) = (Store::default(), Store::default());
        for i in 0..45 {
            if i % 15 == 0 {
                acknowledge(&mut straight);
            }
            let a = sa.step(&mut straight);
            if i % 4 == 0 {
                restored = SustainedSession::restore(checkpoint(&restored)).unwrap();
            }
            let b = sb.step(&mut restored);
            assert_eq!(bytes(&a), bytes(&b), "step {}", i + 1);
        }
        assert_eq!(bytes(&straight.checkpoint()), bytes(&restored.checkpoint()));
        assert!(text(&straight.checkpoint()).contains("\"lastReturnedTurn\":"));
    }
}

#[test]
fn recent_exclusion_retries_reproduce_the_choice() {
    for policy in [
        SustainedMemoryPolicy::RandomOlder,
        SustainedMemoryPolicy::StateResidual,
    ] {
        let mut s = SustainedSession::new(windowed(policy, 2)).unwrap();
        let mut store = Store::default();
        let mut exercised = false;
        for i in 0..90 {
            if i % 20 == 0 {
                acknowledge(&mut s);
            }
            if let (Some(m), false) = (s.pending_memory().cloned(), exercised) {
                let choice = m.choice.clone().unwrap();
                if choice.excluded_recent >= 1 {
                    // A failed read: the retry recomputes the same choice.
                    s.fail_memory("read failed").unwrap();
                    assert!(s.blocked().is_some());
                    checkpoint(&s).validate().unwrap();
                    s.retry_language().unwrap();
                    let again = s.pending_memory().unwrap().clone();
                    assert_eq!(bytes(&again.choice), bytes(&m.choice));
                    // A failed attempt after confirmation: the retry rereads and the
                    // recomputed choice is the same, exclusion count included.
                    s.confirm_memory(&store.saved[&choice.entry_id]).unwrap();
                    let p = s.pending_language().unwrap().clone();
                    s.start_language(p.attempt_id).unwrap();
                    s.fail_language(p.attempt_id, "provider down").unwrap();
                    checkpoint(&s).validate().unwrap();
                    s.retry_language().unwrap();
                    let third = s.pending_memory().unwrap().clone();
                    assert_eq!(bytes(&third.choice), bytes(&m.choice));
                    assert!(checkpoint(&s).state.chosen_memory.is_none());
                    exercised = true;
                }
            }
            store.step(&mut s);
        }
        assert!(exercised, "{policy:?}: no boundary with an exclusion");
        checkpoint(&s).validate().unwrap();
    }
}

#[test]
fn recent_exclusion_tampering_fails() {
    // A mark without a window.
    let mut s = SustainedSession::new(spec(SustainedMemoryPolicy::RandomOlder)).unwrap();
    let mut store = Store::default();
    for _ in 0..12 {
        store.step(&mut s);
    }
    let mut t = checkpoint(&s);
    assert!(!t.state.applied_entries.is_empty());
    t.state.applied_entries[0].last_returned_turn = Some(1);
    rehash(&mut t);
    assert!(t.validate().is_err(), "a mark without a window");
    // Under a window, at a boundary where it kept out at least one entry and left at
    // least two: a mark out of range, a wrong exclusion count, and a mark on the chosen
    // entry (which would change the choice) all fail.
    for policy in [
        SustainedMemoryPolicy::RandomOlder,
        SustainedMemoryPolicy::StateResidual,
    ] {
        let mut s = SustainedSession::new(windowed(policy, 2)).unwrap();
        let mut store = Store::default();
        let mut tampered = false;
        for i in 0..90 {
            if i % 20 == 0 {
                acknowledge(&mut s);
            }
            if let (Some(m), false) = (s.pending_memory().cloned(), tampered) {
                let c = checkpoint(&s);
                let choice = m.choice.clone().unwrap();
                let kept = (choice.candidates - 1).saturating_sub(choice.excluded_recent);
                if choice.excluded_recent >= 1 && kept >= 2 {
                    let marked = c
                        .state
                        .applied_entries
                        .iter()
                        .position(|e| e.last_returned_turn.is_some())
                        .unwrap();
                    let mut t = checkpoint(&s);
                    t.state.applied_entries[marked].last_returned_turn = Some(0);
                    rehash(&mut t);
                    assert!(t.validate().is_err(), "a mark at turn 0");
                    let mut t = checkpoint(&s);
                    t.state.applied_entries[marked].last_returned_turn =
                        Some(t.state.turn_cursor + 1);
                    rehash(&mut t);
                    assert!(t.validate().is_err(), "a mark in the future");
                    let mut t = checkpoint(&s);
                    if let SustainedPhase::Memory(p) = &mut t.state.phase {
                        p.choice.as_mut().unwrap().excluded_recent += 1;
                    }
                    rehash(&mut t);
                    assert!(t.validate().is_err(), "a wrong exclusion count");
                    let mut t = checkpoint(&s);
                    let chosen = t
                        .state
                        .applied_entries
                        .iter()
                        .position(|e| e.id == choice.entry_id)
                        .unwrap();
                    t.state.applied_entries[chosen].last_returned_turn =
                        Some(t.state.turn_cursor - 1);
                    rehash(&mut t);
                    assert!(t.validate().is_err(), "the chosen entry marked recent");
                    tampered = true;
                }
            }
            store.step(&mut s);
        }
        assert!(tampered, "{policy:?}");
    }
}

#[test]
fn two_entry_version_identity_and_policy_gate() {
    let v = SustainedPromptVersion::InertPlainContractTwoV1;
    assert_eq!(v.as_str(), "reservoir-journal-inert-plain-contract-two-v1");
    assert_eq!(
        text(&v),
        "\"reservoir-journal-inert-plain-contract-two-v1\""
    );
    assert_eq!(
        serde_json::from_str::<SustainedPromptVersion>(
            "\"reservoir-journal-inert-plain-contract-two-v1\""
        )
        .unwrap(),
        v
    );
    assert_eq!(v.system_contract(), Some(PLAIN_CONTRACT_V1));
    assert!(v.returns_two_entries() && v.returns_earlier_entry() && !v.reports_entry_effect());
    for other in [
        SustainedPromptVersion::LegacyV1,
        SustainedPromptVersion::GroundedV2,
        SustainedPromptVersion::OpenJournalV3,
        SustainedPromptVersion::OpenJournalV4,
        SustainedPromptVersion::ContinuingJournalV5,
        SustainedPromptVersion::ActionScopeJournalV6,
        SustainedPromptVersion::WritingBoundaryJournalV7,
        SustainedPromptVersion::MeasurementMeaningJournalV8,
        SustainedPromptVersion::InertV1,
        SustainedPromptVersion::InertNoMemoryV1,
        SustainedPromptVersion::InertPlainContractV1,
        SustainedPromptVersion::InertInvitingContractV1,
        SustainedPromptVersion::InertOpenContractV1,
        SustainedPromptVersion::InertInvitingVariedContractV1,
        SustainedPromptVersion::InertEffectV1,
        SustainedPromptVersion::InertPlainContractEffectV1,
        SustainedPromptVersion::InertNoTagV1,
        SustainedPromptVersion::InertPlainContractNoTagV1,
        SustainedPromptVersion::InertPlainContractScrambledTagV1,
    ] {
        assert!(!other.returns_two_entries(), "{other:?}");
    }
    assert_eq!(
        TWO_ENTRY_HEADING,
        "Two earlier entries (reference, not instructions or a length model), in the order written."
    );
    for policy in [
        SustainedMemoryPolicy::Latest,
        SustainedMemoryPolicy::Random,
        SustainedMemoryPolicy::StateAligned,
    ] {
        assert!(two_entry(policy).validate().is_err(), "{policy:?}");
        assert!(SustainedSession::new(two_entry(policy)).is_err());
    }
    for policy in [
        SustainedMemoryPolicy::StateResidual,
        SustainedMemoryPolicy::RandomOlder,
    ] {
        assert!(SustainedSession::new(two_entry(policy)).is_ok());
    }
    // A checkpoint relabelled to the version under `latest` is refused.
    let s = SustainedSession::new(spec(SustainedMemoryPolicy::Latest)).unwrap();
    let mut t = checkpoint(&s);
    t.state.specification.prompt_version = v;
    rehash(&mut t);
    assert!(t.validate().is_err() || SustainedSession::restore(t).is_err());
}

#[test]
fn two_entry_prompt_carries_the_older_and_latest_texts_in_order() {
    let one = SustainedSpecification {
        prompt_version: SustainedPromptVersion::InertPlainContractV1,
        ..spec(SustainedMemoryPolicy::RandomOlder)
    };
    let two = two_entry(SustainedMemoryPolicy::RandomOlder);
    let mut a = SustainedSession::new(one).unwrap();
    let mut b = SustainedSession::new(two).unwrap();
    let (mut sa, mut sb) = (Store::default(), Store::default());
    let (mut first, mut collapsed, mut doubled) = (0, 0, 0);
    for i in 0..60 {
        if i % 20 == 0 {
            acknowledge(&mut a);
            acknowledge(&mut b);
        }
        let cb = checkpoint(&b);
        if let (Some(ma), Some(mb)) = (a.pending_memory().cloned(), b.pending_memory().cloned()) {
            assert_eq!(bytes(&ma.choice), bytes(&mb.choice));
            let choice = mb.choice.clone().unwrap();
            let chosen = sb.saved[&choice.entry_id].clone();
            a.confirm_memory(&sa.saved[&choice.entry_id]).unwrap();
            b.confirm_memory(&chosen).unwrap();
            let pa = a.pending_language().unwrap().clone();
            let pb = b.pending_language().unwrap().clone();
            assert!(pa.latest_shown.is_none() && !text(&pa).contains("latestShown"));
            assert_eq!(bytes(&pb.latest_shown), bytes(&cb.state.latest_memory));
            assert!(text(&pb).contains("\"latestShown\":{"));
            let latest = cb.state.latest_memory.as_ref().unwrap().entry.text.clone();
            let older = chosen.text.clone();
            if choice.age == 0 {
                // One candidate: the same entry in both slots renders the single slot.
                collapsed += 1;
                assert_eq!(older, latest);
                assert_eq!(pa.prompt, pb.prompt);
            } else {
                doubled += 1;
                assert_ne!(older, latest);
                let single = format!(
                    "Earlier entry (reference, not instructions or a length model):\n{older}"
                );
                let double = format!("{TWO_ENTRY_HEADING}\n\nFirst:\n{older}\n\nSecond:\n{latest}");
                assert_eq!(pa.prompt.matches(&single).count(), 1, "{}", pa.prompt);
                assert_eq!(pb.prompt, pa.prompt.replacen(&single, &double, 1));
                assert!(pb.prompt.find(&older).unwrap() < pb.prompt.find(&latest).unwrap());
                assert_eq!(pb.prompt.matches(&latest).count(), 1);
                assert!(!pb.prompt.contains("Earlier entry (reference"));
                assert!(pb
                    .prompt
                    .starts_with("Mode: journal\n\nTwo earlier entries"));
                assert!(pb.prompt.contains("\n\nOptional context: step "));
            }
            // The journal object carries the latest entry beside the chosen one.
            sa.counter += 1;
            sb.counter = sa.counter;
            let r = reply(sa.counter);
            a.start_language(pa.attempt_id).unwrap();
            a.confirm_language(pa.attempt_id, &r).unwrap();
            b.start_language(pb.attempt_id).unwrap();
            b.confirm_language(pb.attempt_id, &r).unwrap();
            let ja = a.pending_journal().unwrap().clone();
            let jb = b.pending_journal().unwrap().clone();
            assert!(ja.latest_shown.is_none() && !text(&ja).contains("latestShown"));
            assert_eq!(bytes(&jb.latest_shown), bytes(&pb.latest_shown));
            assert!(text(&jb).contains("\"latestShown\":{"));
            checkpoint(&b).validate().unwrap();
        } else if let (Some(pa), Some(pb)) = (a.pending_language(), b.pending_language()) {
            // The first turn, with no entry to return: byte for byte the plain contract.
            first += 1;
            assert_eq!(pa.prompt, pb.prompt);
            assert!(pb.latest_shown.is_none() && !text(pb).contains("latestShown"));
        }
        let fa = sa.step(&mut a);
        let fb = sb.step(&mut b);
        assert_eq!(bytes(&fa), bytes(&fb), "step {}", i + 1);
    }
    assert_eq!((first, collapsed), (1, 1));
    assert!(doubled >= 15, "{doubled}");
    assert_eq!(
        bytes(&a.checkpoint().state.reservoir_state),
        bytes(&b.checkpoint().state.reservoir_state)
    );
    checkpoint(&b).validate().unwrap();
}

#[test]
fn two_entry_latest_shown_tampering_fails_validation() {
    let mut s = SustainedSession::new(two_entry(SustainedMemoryPolicy::RandomOlder)).unwrap();
    let mut store = Store::default();
    let mut done = false;
    for i in 0..60 {
        if i % 20 == 0 {
            acknowledge(&mut s);
        }
        if let (Some(m), false) = (s.pending_memory().cloned(), done) {
            let choice = m.choice.clone().unwrap();
            if choice.age >= 1 && choice.candidates >= 3 {
                let latest = checkpoint(&s).state.latest_memory.clone();
                // A blocked read (attempt 0) with a latest entry injected.
                s.fail_memory("read failed").unwrap();
                checkpoint(&s).validate().unwrap();
                let mut t = checkpoint(&s);
                if let SustainedPhase::Blocked(b) = &mut t.state.phase {
                    b.pending.latest_shown = latest.clone();
                }
                rehash(&mut t);
                assert!(
                    t.validate().is_err(),
                    "a blocked read carrying a latest entry"
                );
                s.retry_language().unwrap();
                s.confirm_memory(&store.saved[&choice.entry_id]).unwrap();
                checkpoint(&s).validate().unwrap();
                // The language phase: removed, swapped, or the prompt edited.
                let mut t = checkpoint(&s);
                if let SustainedPhase::Language(p) = &mut t.state.phase {
                    p.latest_shown = None;
                }
                rehash(&mut t);
                assert!(t.validate().is_err(), "the latest entry removed");
                let latest_id = latest.as_ref().unwrap().entry.id.clone();
                let other = store
                    .saved
                    .values()
                    .find(|j| j.id != choice.entry_id && j.id != latest_id)
                    .unwrap()
                    .clone();
                let mut t = checkpoint(&s);
                if let SustainedPhase::Language(p) = &mut t.state.phase {
                    let l = p.latest_shown.as_mut().unwrap();
                    l.relative_path = format!("journals/{}.json", other.id);
                    l.applied_step = other.observed_step + 1;
                    l.entry = other;
                }
                rehash(&mut t);
                assert!(t.validate().is_err(), "the latest entry swapped");
                let mut t = checkpoint(&s);
                if let SustainedPhase::Language(p) = &mut t.state.phase {
                    p.prompt.push('x');
                }
                rehash(&mut t);
                assert!(t.validate().is_err(), "the prompt edited");
                // The journal phase: removed.
                let p = s.pending_language().unwrap().clone();
                s.start_language(p.attempt_id).unwrap();
                store.counter += 1;
                s.confirm_language(p.attempt_id, &reply(store.counter))
                    .unwrap();
                checkpoint(&s).validate().unwrap();
                let mut t = checkpoint(&s);
                if let SustainedPhase::Journal(j) = &mut t.state.phase {
                    j.latest_shown = None;
                }
                rehash(&mut t);
                assert!(t.validate().is_err(), "a journal without the latest entry");
                done = true;
            }
        }
        store.step(&mut s);
    }
    assert!(done);
    // A one-entry version carrying a latest entry.
    let mut s = SustainedSession::new(SustainedSpecification {
        prompt_version: SustainedPromptVersion::InertPlainContractV1,
        ..spec(SustainedMemoryPolicy::RandomOlder)
    })
    .unwrap();
    let mut store = Store::default();
    let mut injected = false;
    for _ in 0..30 {
        if let (Some(m), false) = (s.pending_memory().cloned(), injected) {
            s.confirm_memory(&store.saved[m.entry_id().unwrap()])
                .unwrap();
            let mut t = checkpoint(&s);
            let latest = t.state.latest_memory.clone();
            if let SustainedPhase::Language(p) = &mut t.state.phase {
                p.latest_shown = latest;
            }
            rehash(&mut t);
            assert!(
                t.validate().is_err(),
                "a one-entry version carrying a latest entry"
            );
            injected = true;
        }
        store.step(&mut s);
    }
    assert!(injected);
}

#[test]
fn two_entry_replay_and_restore_reproduce() {
    let spec = SustainedSpecification {
        memory_recent_exclusion: 1,
        ..two_entry(SustainedMemoryPolicy::StateResidual)
    };
    let mut s = SustainedSession::new(spec.clone()).unwrap();
    let mut store = Store::default();
    let mut base = checkpoint(&s);
    let mut all = String::new();
    let (mut failed_language, mut failed_memory) = (false, false);
    for i in 0..60 {
        if i % 30 == 0 {
            acknowledge(&mut s);
            base = checkpoint(&s);
        }
        if let Some(m) = s.pending_memory().cloned() {
            if !failed_language && i > 30 {
                s.confirm_memory(&store.saved[m.entry_id().unwrap()])
                    .unwrap();
                let p = s.pending_language().unwrap().clone();
                s.start_language(p.attempt_id).unwrap();
                s.fail_language(p.attempt_id, "provider down").unwrap();
                s.retry_language().unwrap();
                failed_language = true;
            } else if !failed_memory && i > 40 {
                s.fail_memory("read failed").unwrap();
                s.retry_language().unwrap();
                failed_memory = true;
            }
        }
        settle_collect(&mut store, &mut s, &mut all);
        s.advance().unwrap();
    }
    assert!(failed_language && failed_memory);
    checkpoint(&s).validate().unwrap();
    assert!(all.contains("\"latestShown\":{") && all.contains("\"excludedRecent\":"));
    let seg = segment(&base, &s);
    assert!(text(&seg).contains("\"lastReturnedTurn\":"));
    seg.verify().unwrap();
    let mut straight = SustainedSession::new(spec.clone()).unwrap();
    let mut restored = SustainedSession::new(spec).unwrap();
    let (mut sa, mut sb) = (Store::default(), Store::default());
    for i in 0..45 {
        if i % 15 == 0 {
            acknowledge(&mut straight);
        }
        let a = sa.step(&mut straight);
        if i % 4 == 0 {
            restored = SustainedSession::restore(checkpoint(&restored)).unwrap();
        }
        let b = sb.step(&mut restored);
        assert_eq!(bytes(&a), bytes(&b), "step {}", i + 1);
    }
    assert_eq!(bytes(&straight.checkpoint()), bytes(&restored.checkpoint()));
}

// 0.39.0: the two-entry slot without a context line.

#[test]
fn two_entry_no_tag_version_identity_and_policy_gate() {
    let v = SustainedPromptVersion::InertPlainContractTwoNoTagV1;
    assert_eq!(
        v.as_str(),
        "reservoir-journal-inert-plain-contract-two-no-tag-v1"
    );
    assert_eq!(
        text(&v),
        "\"reservoir-journal-inert-plain-contract-two-no-tag-v1\""
    );
    assert_eq!(
        serde_json::from_str::<SustainedPromptVersion>(
            "\"reservoir-journal-inert-plain-contract-two-no-tag-v1\""
        )
        .unwrap(),
        v
    );
    assert_eq!(v.system_contract(), Some(PLAIN_CONTRACT_V1));
    assert!(v.returns_two_entries() && v.returns_earlier_entry() && !v.reports_entry_effect());
    assert!(SustainedPromptVersion::InertPlainContractTwoV1.returns_two_entries());
    assert!(!SustainedPromptVersion::InertPlainContractNoTagV1.returns_two_entries());
    for policy in [
        SustainedMemoryPolicy::Latest,
        SustainedMemoryPolicy::Random,
        SustainedMemoryPolicy::StateAligned,
    ] {
        assert!(two_entry_no_tag(policy).validate().is_err(), "{policy:?}");
        assert!(SustainedSession::new(two_entry_no_tag(policy)).is_err());
    }
    for policy in [
        SustainedMemoryPolicy::StateResidual,
        SustainedMemoryPolicy::RandomOlder,
    ] {
        assert!(SustainedSession::new(two_entry_no_tag(policy)).is_ok());
    }
    let s = SustainedSession::new(spec(SustainedMemoryPolicy::Latest)).unwrap();
    let mut t = checkpoint(&s);
    t.state.specification.prompt_version = v;
    rehash(&mut t);
    assert!(t.validate().is_err() || SustainedSession::restore(t).is_err());
}

#[test]
fn two_entry_no_tag_prompt_is_the_two_entry_prompt_minus_its_context_line() {
    const CLOSE: &str = "No continuity label, delta, evidence citation, stance line, or explanation is required for this writing.";
    let single = SustainedSpecification {
        prompt_version: SustainedPromptVersion::InertPlainContractNoTagV1,
        ..spec(SustainedMemoryPolicy::RandomOlder)
    };
    let mut a = SustainedSession::new(two_entry(SustainedMemoryPolicy::RandomOlder)).unwrap();
    let mut b =
        SustainedSession::new(two_entry_no_tag(SustainedMemoryPolicy::RandomOlder)).unwrap();
    let mut c = SustainedSession::new(single).unwrap();
    let (mut sa, mut sb, mut sc) = (Store::default(), Store::default(), Store::default());
    let (mut first, mut collapsed, mut doubled) = (0, 0, 0);
    let mut base = checkpoint(&b);
    for i in 0..60 {
        if i % 20 == 0 {
            acknowledge(&mut a);
            acknowledge(&mut b);
            acknowledge(&mut c);
            base = checkpoint(&b);
        }
        let cb = checkpoint(&b);
        if let (Some(ma), Some(mb), Some(mc)) = (
            a.pending_memory().cloned(),
            b.pending_memory().cloned(),
            c.pending_memory().cloned(),
        ) {
            // The same seeded draw under all three versions.
            assert_eq!(bytes(&ma.choice), bytes(&mb.choice));
            assert_eq!(bytes(&mb.choice), bytes(&mc.choice));
            let choice = mb.choice.clone().unwrap();
            a.confirm_memory(&sa.saved[&choice.entry_id]).unwrap();
            b.confirm_memory(&sb.saved[&choice.entry_id]).unwrap();
            c.confirm_memory(&sc.saved[&choice.entry_id]).unwrap();
            let pa = a.pending_language().unwrap().clone();
            let pb = b.pending_language().unwrap().clone();
            let pc = c.pending_language().unwrap().clone();
            assert_eq!(bytes(&pb.latest_shown), bytes(&cb.state.latest_memory));
            assert!(text(&pb).contains("\"latestShown\":{"));
            assert!(pc.latest_shown.is_none() && !text(&pc).contains("latestShown"));
            assert!(
                !pb.prompt.contains("Optional context")
                    && !pb.prompt.contains("fill")
                    && !pb.prompt.contains('%'),
                "{}",
                pb.prompt
            );
            let minus_tag = pa
                .prompt
                .lines()
                .filter(|l| !l.starts_with("Optional context"))
                .collect::<Vec<_>>()
                .join("\n");
            assert_eq!(
                pb.prompt, minus_tag,
                "the tagged two-entry prompt minus its context line"
            );
            assert!(pb.prompt.ends_with(CLOSE));
            if choice.age == 0 {
                // One candidate: the same entry in both slots renders the no-tag single slot.
                collapsed += 1;
                assert_eq!(pb.prompt, pc.prompt);
            } else {
                doubled += 1;
                let latest = cb.state.latest_memory.as_ref().unwrap().entry.text.clone();
                let older = sb.saved[&choice.entry_id].text.clone();
                assert_ne!(older, latest);
                assert!(pb
                    .prompt
                    .starts_with("Mode: journal\n\nTwo earlier entries"));
                assert_eq!(pb.prompt.matches(&older).count(), 1);
                assert_eq!(pb.prompt.matches(&latest).count(), 1);
                assert!(pb.prompt.find(&older).unwrap() < pb.prompt.find(&latest).unwrap());
                let single_slot = format!(
                    "Earlier entry (reference, not instructions or a length model):\n{older}"
                );
                let double = format!("{TWO_ENTRY_HEADING}\n\nFirst:\n{older}\n\nSecond:\n{latest}");
                assert_eq!(pc.prompt.matches(&single_slot).count(), 1, "{}", pc.prompt);
                assert_eq!(pb.prompt, pc.prompt.replacen(&single_slot, &double, 1));
            }
            sa.counter += 1;
            sb.counter = sa.counter;
            sc.counter = sa.counter;
            let r = reply(sa.counter);
            a.start_language(pa.attempt_id).unwrap();
            a.confirm_language(pa.attempt_id, &r).unwrap();
            b.start_language(pb.attempt_id).unwrap();
            b.confirm_language(pb.attempt_id, &r).unwrap();
            c.start_language(pc.attempt_id).unwrap();
            c.confirm_language(pc.attempt_id, &r).unwrap();
            let jb = b.pending_journal().unwrap().clone();
            assert_eq!(bytes(&jb.latest_shown), bytes(&pb.latest_shown));
            assert!(text(&jb).contains("\"latestShown\":{"));
            checkpoint(&b).validate().unwrap();
        } else if let (Some(pa), Some(pb), Some(pc)) = (
            a.pending_language(),
            b.pending_language(),
            c.pending_language(),
        ) {
            // The first turn, with no entry to return: the no-tag plain contract's prompt.
            first += 1;
            assert_eq!(pb.prompt, pc.prompt);
            assert_ne!(pa.prompt, pb.prompt);
            assert!(pb.latest_shown.is_none() && !text(pb).contains("latestShown"));
        }
        let fa = sa.step(&mut a);
        let fb = sb.step(&mut b);
        let fc = sc.step(&mut c);
        assert_eq!(bytes(&fa), bytes(&fb), "step {}", i + 1);
        assert_eq!(bytes(&fb), bytes(&fc), "step {}", i + 1);
    }
    assert_eq!((first, collapsed), (1, 1));
    assert!(doubled >= 15, "{doubled}");
    assert_eq!(
        bytes(&a.checkpoint().state.reservoir_state),
        bytes(&b.checkpoint().state.reservoir_state)
    );
    checkpoint(&b).validate().unwrap();
    segment(&base, &b).verify().unwrap();
}
