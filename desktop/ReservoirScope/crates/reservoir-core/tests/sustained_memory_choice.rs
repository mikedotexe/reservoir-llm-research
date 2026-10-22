//! 0.36.0: which earlier entry a turn returns. `latest` is byte for byte the earlier
//! mechanism; `state-aligned` lets the recurrent state choose among the applied entries by
//! their recorded effect at application; `random` is the seeded control. The prompt text
//! is the same under every policy. Also the watchdog warm-up of the difference channel.
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
