//! One fair, nonblocking admission queue for local writing and embedding calls.
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, VecDeque},
    sync::{Arc, Mutex},
    time::Instant,
};

#[derive(Default)]
struct Endpoint {
    active: usize,
    waiting: VecDeque<(String, Instant)>,
}
struct Inner {
    limit: usize,
    endpoints: BTreeMap<String, Endpoint>,
    waited_ms: BTreeMap<String, u64>,
}
#[derive(Clone)]
pub struct ProviderScheduler(Arc<Mutex<Inner>>);
impl Default for ProviderScheduler {
    fn default() -> Self {
        Self(Arc::new(Mutex::new(Inner {
            limit: 1,
            endpoints: BTreeMap::new(),
            waited_ms: BTreeMap::new(),
        })))
    }
}
fn key(endpoint: &str) -> String {
    endpoint
        .trim_end_matches('/')
        .replace("localhost", "127.0.0.1")
        .replace("[::1]", "127.0.0.1")
}
pub struct Permit {
    pub queued_millis: u64,
    scheduler: ProviderScheduler,
    endpoint: String,
}
impl Drop for Permit {
    fn drop(&mut self) {
        if let Ok(mut g) = self.scheduler.0.lock() {
            if let Some(e) = g.endpoints.get_mut(&self.endpoint) {
                e.active = e.active.saturating_sub(1);
            }
        }
    }
}
impl ProviderScheduler {
    pub fn try_acquire(&self, endpoint: &str, owner: &str) -> Option<Permit> {
        let endpoint = key(endpoint);
        let mut g = self.0.lock().ok()?;
        let limit = g.limit;
        let e = g.endpoints.entry(endpoint.clone()).or_default();
        if !e.waiting.iter().any(|(id, _)| id == owner) {
            e.waiting.push_back((owner.into(), Instant::now()));
        }
        if e.active >= limit || e.waiting.front().is_none_or(|(id, _)| id != owner) {
            return None;
        }
        let (_, at) = e.waiting.pop_front()?;
        e.active += 1;
        let queued_millis = at.elapsed().as_millis() as u64;
        *g.waited_ms.entry(owner.into()).or_default() += queued_millis;
        Some(Permit {
            queued_millis,
            scheduler: self.clone(),
            endpoint,
        })
    }
    pub fn cancel(&self, owner: &str) {
        if let Ok(mut g) = self.0.lock() {
            for e in g.endpoints.values_mut() {
                e.waiting.retain(|(id, _)| id != owner);
            }
        }
    }
    pub fn set_limit(&self, limit: usize) -> Result<(), &'static str> {
        if !(1..=16).contains(&limit) {
            return Err("Model concurrency must be 1–16");
        }
        self.0.lock().map_err(|_| "Scheduler unavailable")?.limit = limit;
        Ok(())
    }
    pub fn snapshot(&self) -> Value {
        let g = self.0.lock().unwrap_or_else(|e| e.into_inner());
        json!({"maxConcurrentRequests":g.limit,"queueTimeCountsAsActive":true,"endpoints":g.endpoints.iter().map(|(endpoint,e)|json!({"endpoint":endpoint,"active":e.active,"waiting":e.waiting.iter().map(|(id,at)|json!({"runId":id,"queuedMillis":at.elapsed().as_millis() as u64})).collect::<Vec<_>>()})).collect::<Vec<_>>(),"waitedMillis":g.waited_ms})
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fair_cancellable_and_endpoint_normalized() {
        let s = ProviderScheduler::default();
        let a = s.try_acquire("http://localhost:1234", "a").unwrap();
        assert!(s.try_acquire("http://127.0.0.1:1234/", "b").is_none());
        assert!(s.try_acquire("http://127.0.0.1:1234", "c").is_none());
        s.cancel("b");
        drop(a);
        assert!(s.try_acquire("http://127.0.0.1:1234", "a").is_none());
        let c = s.try_acquire("http://127.0.0.1:1234", "c").unwrap();
        drop(c);
        assert!(s.try_acquire("http://127.0.0.1:1234", "a").is_some());
    }
}
