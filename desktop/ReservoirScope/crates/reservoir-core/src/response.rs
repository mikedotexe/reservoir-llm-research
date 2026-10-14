//! Bounded retained response readers. Native immediate action boundaries and the
//! separate simulated-parent fixture have different meanings and never share a clock.
use crate::{ensure, CoreError, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;
use unicode_segmentation::UnicodeSegmentation;

pub const NATIVE_MAX_BYTES: usize = 8 * 1024 * 1024;
pub const MAX_RECEIPTS: usize = 1024;
pub const SIMULATION_MAX_BYTES: usize = 1_048_576;
pub const SIMULATION_SHA256: &str =
    "fe97623dcccb4b089ce4e0a1b5cc99ec902793efed8fbfcf1041ce8c865e9100";
pub const NATIVE_SUBJECT: &str = "Minime native ESN rehearsal";
pub const NATIVE_SCOPE: &str = "isolated research copy; no running being";
pub const NATIVE_CLOCK: &str =
    "successful native step ids; supplied rehearsal clock is not measured wall time";
fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn is_hash(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn bounded_text(s: &str, max: usize) -> bool {
    !s.is_empty() && s.graphemes(true).count() <= max
}
fn raw(bytes: &[u8], limit: usize) -> Result<serde_json::Value> {
    ensure(
        !bytes.is_empty() && bytes.len() <= limit,
        "Response JSON is empty or exceeds its explicit byte bound.",
    )?;
    serde_json::from_slice(bytes).map_err(|e| CoreError::Invalid(format!("Response JSON: {e}")))
}
fn exact_keys(value: &serde_json::Value, keys: &[&str]) -> bool {
    value
        .as_object()
        .is_some_and(|v| v.len() == keys.len() && keys.iter().all(|k| v.contains_key(*k)))
}
fn decode<T: for<'de> Deserialize<'de>>(bytes: &[u8]) -> Result<T> {
    serde_json::from_slice(bytes)
        .map_err(|e| CoreError::Invalid(format!("Response structure: {e}")))
}

// Swift JSONDecoder accepts mathematically integral decimal/exponent tokens.
// RawValue preserves the token so wide UInt64 values never pass through f64.
fn exact_integer(token: &str) -> std::result::Result<i128, String> {
    let (negative, unsigned) = token
        .strip_prefix('-')
        .map_or((false, token), |s| (true, s));
    let (mantissa, exponent) =
        unsigned
            .split_once(['e', 'E'])
            .map_or(Ok((unsigned, 0_i64)), |(m, e)| {
                e.parse::<i64>()
                    .map(|n| (m, n))
                    .map_err(|_| "Integer exponent is out of range.".to_string())
            })?;
    let (whole, fraction) = mantissa.split_once('.').unwrap_or((mantissa, ""));
    if whole.is_empty()
        || !whole
            .bytes()
            .chain(fraction.bytes())
            .all(|b| b.is_ascii_digit())
    {
        return Err("Expected an exact JSON integer.".into());
    }
    let digits = format!("{whole}{fraction}");
    let digits = digits.trim_start_matches('0');
    if digits.is_empty() {
        return Ok(0);
    }
    let scale = exponent
        .checked_sub(fraction.len() as i64)
        .ok_or("Integer exponent is out of range.")?;
    let mut digits = digits.to_string();
    if scale < 0 {
        let removed = scale
            .checked_neg()
            .and_then(|v| usize::try_from(v).ok())
            .ok_or("Integer scale is out of range.")?;
        if removed > digits.len() || !digits[digits.len() - removed..].bytes().all(|b| b == b'0') {
            return Err("Integer token has a fractional value.".into());
        }
        digits.truncate(digits.len() - removed);
    } else {
        if scale > 20 || digits.len() + scale as usize > 20 {
            return Err("Integer exceeds native UInt64 bounds.".into());
        }
        digits.extend(std::iter::repeat_n('0', scale as usize));
    }
    if digits.len() > 20 {
        return Err("Integer exceeds native bounds.".into());
    }
    let value = digits
        .parse::<i128>()
        .map_err(|_| "Invalid integer token.".to_string())?;
    Ok(if negative { -value } else { value })
}
trait NativeInteger: TryFrom<i128> {
    fn accepts_float(value: f64) -> bool;
}
impl NativeInteger for u64 {
    fn accepts_float(value: f64) -> bool {
        (0.0..18_446_744_073_709_551_616.0).contains(&value)
    }
}
impl NativeInteger for i64 {
    fn accepts_float(value: f64) -> bool {
        (-9_223_372_036_854_775_808.0..9_223_372_036_854_775_808.0).contains(&value)
    }
}
impl NativeInteger for u32 {
    fn accepts_float(value: f64) -> bool {
        (0.0..=4_294_967_295.0).contains(&value)
    }
}
fn check_float_token<T: NativeInteger>(token: &str) -> std::result::Result<(), String> {
    // Foundation first checks representability for decimal/exponent tokens.
    // Near UInt64/Int64 endpoints a rounded f64 may be outside that range even
    // when the exact decimal integer fits. Plain integer tokens take another path.
    if token.contains(['.', 'e', 'E']) {
        let value = token
            .parse::<f64>()
            .map_err(|_| "Native floating integer token is invalid.".to_string())?;
        if !value.is_finite() || !T::accepts_float(value) {
            return Err("Floating integer token is not representable in its native type.".into());
        }
    }
    Ok(())
}
fn native_integer<'de, D, T>(d: D) -> std::result::Result<T, D::Error>
where
    D: serde::Deserializer<'de>,
    T: NativeInteger,
{
    let raw = Box::<serde_json::value::RawValue>::deserialize(d)?;
    check_float_token::<T>(raw.get()).map_err(serde::de::Error::custom)?;
    let value = exact_integer(raw.get()).map_err(serde::de::Error::custom)?;
    T::try_from(value)
        .map_err(|_| serde::de::Error::custom("Integer exceeds its declared native bounds."))
}
fn optional_integer<'de, D, T>(d: D) -> std::result::Result<Option<T>, D::Error>
where
    D: serde::Deserializer<'de>,
    T: NativeInteger,
{
    let raw = Option::<Box<serde_json::value::RawValue>>::deserialize(d)?;
    raw.map(|raw| {
        check_float_token::<T>(raw.get()).map_err(serde::de::Error::custom)?;
        let value = exact_integer(raw.get()).map_err(serde::de::Error::custom)?;
        T::try_from(value)
            .map_err(|_| serde::de::Error::custom("Integer exceeds its declared native bounds."))
    })
    .transpose()
}
fn native_u64<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<u64, D::Error> {
    native_integer(d)
}
fn native_usize<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<usize, D::Error> {
    let value: i64 = native_integer(d)?;
    usize::try_from(value).map_err(|_| serde::de::Error::custom("Native count is negative."))
}
fn optional_u64<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<u64>, D::Error> {
    optional_integer(d)
}
fn optional_i64<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<i64>, D::Error> {
    optional_integer(d)
}
fn optional_u32<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<u32>, D::Error> {
    optional_integer(d)
}
fn optional_usize<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<usize>, D::Error> {
    let value: Option<i64> = optional_integer(d)?;
    value
        .map(|v| {
            usize::try_from(v).map_err(|_| serde::de::Error::custom("Native count is negative."))
        })
        .transpose()
}
fn parse_f32<E: serde::de::Error>(
    raw: &serde_json::value::RawValue,
) -> std::result::Result<f32, E> {
    let value = raw
        .get()
        .parse::<f32>()
        .map_err(|_| E::custom("Expected a native Float32 number."))?;
    if value.is_finite() {
        Ok(value)
    } else {
        Err(E::custom(
            "Number cannot be represented as a finite native Float32.",
        ))
    }
}
fn finite_vec<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<Vec<f32>, D::Error> {
    Vec::<Box<serde_json::value::RawValue>>::deserialize(d)?
        .iter()
        .map(|raw| parse_f32(raw))
        .collect()
}
fn optional_finite_vec<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<Vec<f32>>, D::Error> {
    Option::<Vec<Box<serde_json::value::RawValue>>>::deserialize(d)?
        .map(|values| values.iter().map(|raw| parse_f32(raw)).collect())
        .transpose()
}
fn optional_finite<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<f32>, D::Error> {
    Option::<Box<serde_json::value::RawValue>>::deserialize(d)?
        .map(|raw| parse_f32(&raw))
        .transpose()
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NativeIdentity {
    pub engine_session_id: String,
    pub model_id: String,
    pub node_layout_id: String,
    #[serde(deserialize_with = "native_usize")]
    pub node_count: usize,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NativeReceipt {
    #[serde(deserialize_with = "native_u64")]
    pub schema_version: u64,
    pub command_id: String,
    pub intent_id: String,
    pub identity: NativeIdentity,
    pub pattern_id: String,
    pub pattern_sha256: String,
    #[serde(deserialize_with = "finite_vec")]
    pub direction: Vec<f32>,
    pub status: String,
    #[serde(deserialize_with = "native_u64")]
    pub observed_at_unix_ms: u64,
    #[serde(default, deserialize_with = "optional_u64")]
    pub successful_step_id: Option<u64>,
    #[serde(default, deserialize_with = "optional_i64")]
    pub pulse_index: Option<i64>,
    #[serde(default, deserialize_with = "optional_u32")]
    pub success_offset: Option<u32>,
    #[serde(default, deserialize_with = "optional_finite")]
    pub requested_amount: Option<f32>,
    #[serde(default, deserialize_with = "optional_finite_vec")]
    pub before: Option<Vec<f32>>,
    #[serde(default, deserialize_with = "optional_finite_vec")]
    pub after: Option<Vec<f32>>,
    #[serde(default, deserialize_with = "optional_finite_vec")]
    pub delta: Option<Vec<f32>>,
    #[serde(default, deserialize_with = "optional_finite")]
    pub attenuation: Option<f32>,
    pub actual_l2: Option<f64>,
    #[serde(default, deserialize_with = "optional_finite")]
    pub max_abs_delta: Option<f32>,
    pub clipped: bool,
    #[serde(default, deserialize_with = "optional_u64")]
    pub boundary_wait_us: Option<u64>,
    #[serde(default, deserialize_with = "optional_finite")]
    pub effective_leak: Option<f32>,
    #[serde(default, deserialize_with = "optional_finite_vec")]
    pub realized_noise: Option<Vec<f32>>,
    pub reason: Option<String>,
}
// Swift String and Dictionary key equality use canonical equivalence. Keep
// original text for display/export; normalize comparison keys only.
fn canonical(value: &str) -> String {
    value.nfc().collect()
}
fn text_equal(a: &str, b: &str) -> bool {
    a.nfc().eq(b.nfc())
}
fn optional_text_equal(a: Option<&str>, b: Option<&str>) -> bool {
    match (a, b) {
        (None, None) => true,
        (Some(a), Some(b)) => text_equal(a, b),
        _ => false,
    }
}
fn canonical_hashes(map: &BTreeMap<String, String>) -> BTreeMap<String, &str> {
    map.iter()
        .map(|(k, v)| (canonical(k), v.as_str()))
        .collect()
}
impl PartialEq for NativeIdentity {
    fn eq(&self, other: &Self) -> bool {
        self.node_count == other.node_count
            && text_equal(&self.engine_session_id, &other.engine_session_id)
            && text_equal(&self.model_id, &other.model_id)
            && text_equal(&self.node_layout_id, &other.node_layout_id)
    }
}
impl Eq for NativeIdentity {}
impl PartialEq for NativeReceipt {
    fn eq(&self, other: &Self) -> bool {
        self.schema_version == other.schema_version
            && text_equal(&self.command_id, &other.command_id)
            && text_equal(&self.intent_id, &other.intent_id)
            && self.identity == other.identity
            && text_equal(&self.pattern_id, &other.pattern_id)
            && text_equal(&self.pattern_sha256, &other.pattern_sha256)
            && self.direction == other.direction
            && text_equal(&self.status, &other.status)
            && self.observed_at_unix_ms == other.observed_at_unix_ms
            && self.successful_step_id == other.successful_step_id
            && self.pulse_index == other.pulse_index
            && self.success_offset == other.success_offset
            && self.requested_amount == other.requested_amount
            && self.before == other.before
            && self.after == other.after
            && self.delta == other.delta
            && self.attenuation == other.attenuation
            && self.actual_l2 == other.actual_l2
            && self.max_abs_delta == other.max_abs_delta
            && self.clipped == other.clipped
            && self.boundary_wait_us == other.boundary_wait_us
            && self.effective_leak == other.effective_leak
            && self.realized_noise == other.realized_noise
            && optional_text_equal(self.reason.as_deref(), other.reason.as_deref())
    }
}
impl NativeReceipt {
    pub fn has_state(&self) -> bool {
        matches!(self.status.as_str(), "applied" | "no_op")
    }
    pub fn is_boundary(&self) -> bool {
        self.has_state() || self.status == "headroom_rejected"
    }
    pub fn frame_id(&self) -> String {
        format!(
            "{}:{}:{}",
            self.command_id,
            self.successful_step_id.unwrap_or(0),
            self.pulse_index.unwrap_or(-1)
        )
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct NativePayload {
    schema: String,
    subject: String,
    scope: String,
    source_hashes: BTreeMap<String, String>,
    clock: String,
    fill: (),
    reference_basis: (),
    receipts: Vec<NativeReceipt>,
}
#[derive(Clone, Debug)]
pub struct NativeResponse {
    pub source_hashes: BTreeMap<String, String>,
    pub receipts: Vec<NativeReceipt>,
    pub frame_indices: Vec<usize>,
    pub boundary_indices: Vec<usize>,
    pub file_sha256: String,
}
impl NativeResponse {
    pub fn decode(bytes: &[u8]) -> Result<Self> {
        let value = raw(bytes, NATIVE_MAX_BYTES)?;
        ensure(
            exact_keys(
                &value,
                &[
                    "schema",
                    "subject",
                    "scope",
                    "source_hashes",
                    "fill",
                    "reference_basis",
                    "clock",
                    "receipts",
                ],
            ) && value["fill"].is_null()
                && value["reference_basis"].is_null(),
            "Native receipts cannot claim fill, a reference basis, or unsupported wrapper fields.",
        )?;
        let p: NativePayload = decode(bytes)?;
        let _ = (p.fill, p.reference_basis);
        ensure(p.schema=="research.native_action_response.v1"&&p.subject==NATIVE_SUBJECT&&p.scope==NATIVE_SCOPE&&p.clock==NATIVE_CLOCK,
            "Expected isolated native rehearsal receipts with successful-step identities; live evidence is a separate contract.")?;
        ensure(
            !p.source_hashes.is_empty()
                && p.source_hashes.len() <= 32
                && p.source_hashes
                    .iter()
                    .all(|(k, v)| bounded_text(k, 128) && is_hash(v)),
            "Native source hashes are absent or malformed.",
        )?;
        ensure(
            !p.receipts.is_empty() && p.receipts.len() <= MAX_RECEIPTS,
            "Native bundles require 1–1024 receipts.",
        )?;
        let statuses = [
            "accepted",
            "applied",
            "no_op",
            "completed",
            "headroom_rejected",
            "expired",
            "cancelled",
            "superseded",
            "suspended",
            "identity_mismatch",
            "step_failed",
        ];
        ensure(
            canonical_hashes(&p.source_hashes).len() == p.source_hashes.len(),
            "Canonically duplicate source-hash keys are ambiguous and unsupported.",
        )?;
        let mut frame_indices = vec![];
        let mut boundary_indices = vec![];
        let mut ids = BTreeSet::new();
        let mut previous: Option<&NativeReceipt> = None;
        for (index, r) in p.receipts.iter().enumerate() {
            ensure(
                r.schema_version == 1 && statuses.contains(&r.status.as_str()),
                "Unsupported native receipt version or status.",
            )?;
            ensure(
                [
                    &r.command_id,
                    &r.intent_id,
                    &r.pattern_id,
                    &r.identity.engine_session_id,
                    &r.identity.model_id,
                    &r.identity.node_layout_id,
                ]
                .iter()
                .all(|s| bounded_text(s, 512))
                    && r.identity.node_count == 128
                    && is_hash(&r.pattern_sha256),
                "Native receipt action, model or coordinate identity is invalid.",
            )?;
            ensure(
                r.direction.len() == 128 && r.direction.iter().all(|v| v.is_finite()),
                "Native receipt direction is invalid.",
            )?;
            if r.is_boundary() {
                let (
                    Some(before),
                    Some(after),
                    Some(delta),
                    Some(step),
                    Some(pulse),
                    Some(amount),
                    Some(attenuation),
                    Some(l2),
                    Some(maximum),
                    Some(leak),
                    Some(noise),
                    Some(_),
                    Some(_),
                ) = (
                    &r.before,
                    &r.after,
                    &r.delta,
                    r.successful_step_id,
                    r.pulse_index,
                    r.requested_amount,
                    r.attenuation,
                    r.actual_l2,
                    r.max_abs_delta,
                    r.effective_leak,
                    &r.realized_noise,
                    r.success_offset,
                    r.boundary_wait_us,
                )
                else {
                    return Err(CoreError::Invalid("Applied boundaries require exact step, state, noise, leak and application measurements.".into()));
                };
                ensure(
                    step > 0
                        && pulse >= 0
                        && [before, after, delta, noise]
                            .iter()
                            .all(|v| v.len() == 128 && v.iter().all(|x| x.is_finite())),
                    "Native boundary dimensions or step identity are invalid.",
                )?;
                ensure(
                    before.iter().chain(after).all(|v| v.abs() <= 1.0)
                        && amount.is_finite()
                        && attenuation.is_finite()
                        && (0.0..=1.0).contains(&attenuation)
                        && leak.is_finite()
                        && (0.0..=1.0).contains(&leak)
                        && l2.is_finite()
                        && l2 >= 0.0
                        && maximum.is_finite(),
                    "Native controls and state must be finite and within declared bounds.",
                )?;
                ensure(after.iter().zip(before).zip(delta).all(|((&a,&b),&d)|(a-b).to_bits()==d.to_bits()),"Action delta must equal Float32 applied minus ordinary state, including signed bits.")?;
                let expected_l2 = delta
                    .iter()
                    .fold(0.0, |sum, &v| sum + f64::from(v) * f64::from(v))
                    .sqrt();
                let expected_max = delta.iter().map(|v| v.abs()).fold(0.0_f32, f32::max);
                ensure(
                    (expected_l2 - l2).abs() <= 1e-12 * expected_l2.max(1.0)
                        && maximum == expected_max,
                    "Native action measurements disagree with the full 128-coordinate delta.",
                )?;
                ensure(
                    !matches!(r.status.as_str(), "no_op" | "headroom_rejected")
                        || delta.iter().all(|v| *v == 0.0),
                    "No-op or headroom rejection cannot contain a state change.",
                )?;
                ensure(
                    r.status != "headroom_rejected"
                        || (attenuation == 0.0 && l2 == 0.0 && maximum == 0.0 && !r.clipped),
                    "Headroom rejection must report zero applied amount.",
                )?;
                ensure(
                    ids.insert(canonical(&r.frame_id())),
                    "Native action boundary is duplicated.",
                )?;
                if let Some(prev) = previous {
                    ensure(
                        r.identity == prev.identity && step > prev.successful_step_id.unwrap(),
                        "A native bundle cannot splice identities or reverse successful steps.",
                    )?;
                }
                previous = Some(r);
                boundary_indices.push(index);
                if r.has_state() {
                    frame_indices.push(index);
                }
            } else {
                ensure(
                    r.before.is_none() && r.after.is_none() && r.delta.is_none(),
                    "Admission, terminal and failed events cannot present an applied state.",
                )?;
            }
        }
        Ok(Self {
            source_hashes: p.source_hashes,
            receipts: p.receipts,
            frame_indices,
            boundary_indices,
            file_sha256: hash(bytes),
        })
    }
    pub fn identity(&self) -> Option<&NativeIdentity> {
        self.boundary_indices
            .first()
            .map(|&i| &self.receipts[i].identity)
            .or_else(|| self.receipts.first().map(|r| &r.identity))
    }
    pub fn delta_scale(&self) -> f64 {
        self.frame_indices
            .iter()
            .flat_map(|&i| self.receipts[i].delta.as_ref().into_iter().flatten())
            .map(|&v| f64::from(v).abs())
            .fold(1e-9, f64::max)
    }
    pub fn validate_replacement(&self, previous: &Self) -> Result<()> {
        if self.identity() != previous.identity() {
            return Ok(());
        }
        ensure(
            canonical_hashes(&self.source_hashes) == canonical_hashes(&previous.source_hashes),
            "Source code identity changed within the same native session.",
        )?;
        let old: BTreeMap<_, _> = previous
            .boundary_indices
            .iter()
            .map(|&i| {
                let r = &previous.receipts[i];
                (canonical(&r.frame_id()), r)
            })
            .collect();
        for &i in &self.boundary_indices {
            let r = &self.receipts[i];
            if let Some(prior) = old.get(&canonical(&r.frame_id())) {
                ensure(
                    *prior == r,
                    "An already observed native boundary changed in the same source identity.",
                )?;
            }
        }
        if let Some(&i) = previous.boundary_indices.last() {
            let step = self
                .boundary_indices
                .last()
                .and_then(|&i| self.receipts[i].successful_step_id)
                .unwrap_or(0);
            ensure(
                step >= previous.receipts[i].successful_step_id.unwrap(),
                "Native source moved backwards; retain the previous bundle.",
            )?;
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct SimulationSummary {
    pub requested_signed_l2: f64,
    pub actual_initial_l2: f64,
    pub peak_gain_over_initial: f64,
    #[serde(default, deserialize_with = "optional_usize")]
    pub return_boundary: Option<usize>,
    pub return_status: String,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SimulationFrame {
    #[serde(deserialize_with = "native_usize")]
    pub sample_index: usize,
    #[serde(deserialize_with = "native_usize")]
    pub original_boundary_step: usize,
    pub control: Vec<f64>,
    pub intervention: Vec<f64>,
    pub delta: Vec<f64>,
    pub separation_l2: f64,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SimulationResponse {
    pub schema: String,
    pub subject: String,
    pub scope: String,
    pub run_id: String,
    pub selection: String,
    #[serde(deserialize_with = "native_usize")]
    pub node_count: usize,
    pub node_layout: String,
    pub model_hashes: BTreeMap<String, String>,
    pub clock: String,
    pub controls: String,
    pub display_rules: Vec<String>,
    pub result_summary: SimulationSummary,
    pub source_results_sha256: String,
    pub fill: (),
    pub reference_basis: (),
    pub frames: Vec<SimulationFrame>,
}
impl SimulationResponse {
    pub fn decode(bytes: &[u8]) -> Result<Self> {
        Self::decode_with_hash(bytes, SIMULATION_SHA256)
    }
    /// Explicit expected identity is useful for synthetic rejection fixtures.
    /// The desktop reader always uses the compiled retained fixture identity.
    pub fn decode_with_hash(bytes: &[u8], expected_sha256: &str) -> Result<Self> {
        let value = raw(bytes, SIMULATION_MAX_BYTES)?;
        ensure(
            hash(bytes) == expected_sha256,
            "Simulation does not match its retained byte identity.",
        )?;
        ensure(exact_keys(&value,&["schema","subject","scope","run_id","selection","node_count","node_layout","model_hashes","reference_basis","fill","clock","controls","display_rules","result_summary","source_results_sha256","frames"])
            &&value["fill"].is_null()&&value["reference_basis"].is_null(),"Simulation cannot claim fill, reference basis, measured seconds or unsupported wrapper fields.")?;
        let frames = value["frames"]
            .as_array()
            .ok_or_else(|| CoreError::Invalid("Simulation frames must be an array.".into()))?;
        ensure(
            frames.len() == 65
                && frames.iter().all(|v| {
                    exact_keys(
                        v,
                        &[
                            "sample_index",
                            "original_boundary_step",
                            "control",
                            "intervention",
                            "delta",
                            "separation_l2",
                        ],
                    )
                }),
            "Simulation requires exactly 65 complete frames without unsupported fields.",
        )?;
        let r: Self = decode(bytes)?;
        r.validate()?;
        Ok(r)
    }
    pub fn fixed_delta_scale(&self) -> f64 {
        self.result_summary.requested_signed_l2.abs()
    }
    pub fn return_threshold(&self) -> f64 {
        self.result_summary.actual_initial_l2 * 0.1
    }
    fn validate(&self) -> Result<()> {
        ensure(
            self.schema == "research.state_response_preview.v1"
                && self.node_count == 128
                && self.frames.len() == 65,
            "Simulation schema or dimensions are unsupported.",
        )?;
        ensure(self.subject=="esn-divide simulated parent; not live Minime"&&self.clock=="simulation boundary indices only; no measured seconds"
            &&self.scope=="harness parent; fixed recorded controls and additive transition residual; no cloned adaptive controller, no native checkpoint parity claim"
            &&self.node_layout=="captured esn-divide parent index order; not established compatible with native Minime node identity"
            &&self.controls=="Identical recorded inputs, leak, bridge and transition residual; no adaptive controller replica", "Simulation provenance cannot be relabeled as live or native evidence.")?;
        ensure(
            self.run_id == "s0:coordinate_0:dose+0.001"
                && !self.selection.is_empty()
                && !self.display_rules.is_empty(),
            "Simulation fixture identity is unsupported.",
        )?;
        ensure(
            is_hash(&self.source_results_sha256)
                && self.model_hashes.len() == 2
                && ["model/parent/wres", "model/parent/win"]
                    .iter()
                    .all(|k| self.model_hashes.contains_key(*k))
                && self.model_hashes.values().all(|s| is_hash(s)),
            "Simulation source/model hashes are absent or malformed.",
        )?;
        let s = &self.result_summary;
        ensure(
            [
                s.requested_signed_l2,
                s.actual_initial_l2,
                s.peak_gain_over_initial,
            ]
            .iter()
            .all(|v| v.is_finite())
                && self.fixed_delta_scale() == 0.001
                && s.actual_initial_l2 > 0.0,
            "Simulation displacement scale is invalid.",
        )?;
        for (index, f) in self.frames.iter().enumerate() {
            ensure(
                f.sample_index == index && f.original_boundary_step == 200 + index,
                "Simulation boundary order is missing, duplicated or changed.",
            )?;
            ensure(
                f.control.len() == 128 && f.intervention.len() == 128 && f.delta.len() == 128,
                "Simulation coordinates have invalid dimensions.",
            )?;
            ensure(
                f.control
                    .iter()
                    .chain(&f.intervention)
                    .all(|v| v.is_finite() && v.abs() <= 1.0)
                    && f.delta.iter().all(|v| v.is_finite())
                    && f.separation_l2.is_finite()
                    && f.separation_l2 >= 0.0,
                "Simulation coordinates must be finite and bounded.",
            )?;
            ensure(
                f.delta
                    .iter()
                    .zip(f.intervention.iter().zip(&f.control))
                    .all(|(&d, (&a, &b))| (d - (a - b)).abs() <= 1e-14),
                "Simulation delta differs from its paired state difference.",
            )?;
            let distance = f.delta.iter().fold(0.0, |sum, v| sum + v * v).sqrt();
            ensure(
                (distance - f.separation_l2).abs() <= 1e-12,
                "Simulation distance differs from its full vector.",
            )?;
        }
        let first = &self.frames[0];
        ensure(
            (first.delta[0] - s.requested_signed_l2).abs() <= 1e-14
                && first.delta[1..].iter().all(|v| v.abs() <= 1e-14)
                && (first.separation_l2 - s.actual_initial_l2).abs() <= 1e-12,
            "Boundary zero must contain the declared coordinate-zero displacement.",
        )?;
        let peak = self
            .frames
            .iter()
            .map(|f| f.separation_l2)
            .fold(0.0, f64::max)
            / s.actual_initial_l2;
        ensure(
            (peak - s.peak_gain_over_initial).abs() <= 1e-10,
            "Simulation peak summary disagrees with the full path.",
        )?;
        let first_return = (1..=self.frames.len() - 8).find(|&start| {
            self.frames[start..start + 8]
                .iter()
                .all(|f| f.separation_l2 <= self.return_threshold())
        });
        ensure(
            first_return == s.return_boundary
                && s.return_status
                    == if first_return.is_some() {
                        "observed"
                    } else {
                        "not_returned_within_64_steps"
                    },
            "Simulation return summary disagrees with threshold and eight-boundary dwell.",
        )?;
        Ok(())
    }
}
