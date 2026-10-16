//! Bounded readers for frozen Observatory evidence. These validate retained
//! structure and hash bindings; they do not regenerate the historical engine.
use crate::{ensure, CoreError, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub const MAX_JSON_BYTES: usize = 2 * 1024 * 1024;
pub const MAX_STATE_ROWS: usize = 1024;
pub const STATE_DIMENSIONS: usize = 128;
pub const MAX_STATE_BYTES: usize = MAX_STATE_ROWS * STATE_DIMENSIONS * 4;

pub fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn decode<T: for<'de> Deserialize<'de>>(bytes: &[u8], maximum: usize) -> Result<T> {
    ensure(
        !bytes.is_empty() && bytes.len() <= maximum,
        "Evidence byte length is empty or exceeds its explicit bound.",
    )?;
    serde_json::from_slice(bytes).map_err(|e| CoreError::Invalid(format!("Evidence JSON: {e}")))
}

#[derive(Clone, Debug, Deserialize)]
pub struct HistoricalEvidence {
    pub schema_version: u64,
    pub kind: String,
    pub subject: Option<HistoricalSubject>,
    pub capture: Option<HistoricalCapture>,
    pub bands: ReferenceBands,
    pub definitions: Option<BTreeMap<String, String>>,
    pub controller: HistoricalController,
    pub samples: Vec<HistoricalSample>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct HistoricalSubject {
    pub being: Option<String>,
    pub note: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct HistoricalCapture {
    pub captured_at_utc: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct HistoricalController {
    pub historical_status: Option<String>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all(serialize = "camelCase"))]
pub struct ReferenceBands {
    pub shelf_min_pct: f64,
    pub shelf_entry_pct: Option<f64>,
    pub target_pct: f64,
    pub shelf_max_pct: f64,
    pub elevated_release_pct: Option<f64>,
    pub strong_rail_pct: f64,
    pub force_rail_pct: f64,
    pub status: Option<String>,
    pub note: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct HistoricalSample {
    pub t_utc: String,
    pub t_s: f64,
    pub session_id: i64,
    pub fill_pct: f64,
    pub fill_rate_pct_per_s: Option<f64>,
    pub cascade: Vec<f64>,
    pub esn_cov_lambda1: Option<f64>,
    pub geom_radius: Option<f64>,
    pub geom_rel: Option<f64>,
    pub esn_leak: Option<f64>,
    pub esn_lambda: Option<f64>,
    pub source_ids: Option<Vec<Option<i64>>>,
}
impl HistoricalEvidence {
    pub fn from_bytes(bytes: &[u8]) -> Result<Self> {
        let evidence: Self = decode(bytes, MAX_JSON_BYTES)?;
        evidence.validate()?;
        Ok(evidence)
    }
    pub fn validate(&self) -> Result<()> {
        if self.schema_version != 1 || self.kind != "reservoir_3d_evidence" {
            return Err(CoreError::Unsupported(
                "Unsupported historical evidence schema.".into(),
            ));
        }
        ensure(
            !self.samples.is_empty(),
            "Historical replay has no samples.",
        )?;
        let mut previous = None;
        for sample in &self.samples {
            ensure(
                sample.t_s.is_finite()
                    && sample.fill_pct.is_finite()
                    && (0.0..=100.0).contains(&sample.fill_pct)
                    && valid_timestamp(&sample.t_utc)
                    && sample.cascade.len() == 3
                    && sample.cascade.iter().all(|v| v.is_finite()),
                "Historical sample has invalid time, fill, or spectral slots.",
            )?;
            ensure(
                previous.is_none_or(|t| sample.t_s > t),
                "Historical elapsed times must increase strictly.",
            )?;
            ensure(
                [
                    sample.fill_rate_pct_per_s,
                    sample.esn_cov_lambda1,
                    sample.geom_radius,
                    sample.geom_rel,
                    sample.esn_leak,
                    sample.esn_lambda,
                ]
                .iter()
                .flatten()
                .all(|v| v.is_finite()),
                "Optional historical measurements must be finite or absent.",
            )?;
            previous = Some(sample.t_s);
        }
        let b = &self.bands;
        let values = [
            b.shelf_min_pct,
            b.target_pct,
            b.shelf_max_pct,
            b.strong_rail_pct,
            b.force_rail_pct,
        ];
        ensure(
            values
                .iter()
                .all(|v| v.is_finite() && (0.0..=100.0).contains(v))
                && values.windows(2).all(|v| v[0] <= v[1]),
            "Reference bands must be finite, ordered and within 0–100%.",
        )?;
        ensure(
            [b.shelf_entry_pct, b.elevated_release_pct]
                .iter()
                .flatten()
                .all(|v| v.is_finite() && (0.0..=100.0).contains(v)),
            "Optional reference bands must be finite and within 0–100%.",
        )?;
        Ok(())
    }
    /// Playback holds the last retained observation. Scrubbing may select the
    /// nearest, with earlier rows winning ties; positions clamp to endpoints.
    pub fn seek(&self, position: f64, nearest: bool) -> Result<usize> {
        ensure(position.is_finite(), "Seek position must be finite.")?;
        let upper = self.samples.partition_point(|s| s.t_s <= position);
        if upper == 0 {
            return Ok(0);
        }
        let lower = upper - 1;
        if nearest
            && upper < self.samples.len()
            && self.samples[upper].t_s - position < position - self.samples[lower].t_s
        {
            Ok(upper)
        } else {
            Ok(lower)
        }
    }
    pub fn break_before(&self, index: usize) -> bool {
        index > 0
            && self
                .samples
                .get(index)
                .zip(self.samples.get(index - 1))
                .is_some_and(|(s, p)| s.session_id != p.session_id)
    }
    pub fn interval_seconds(&self, index: usize) -> Option<f64> {
        index
            .checked_sub(1)
            .and_then(|p| self.samples.get(index).zip(self.samples.get(p)))
            .map(|(s, p)| s.t_s - p.t_s)
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct StateReplayManifest {
    pub schema: String,
    pub dtype: String,
    pub layout: String,
    pub binary_file: String,
    pub rows: usize,
    pub dimensions: usize,
    pub byte_count: usize,
    pub source_sha256: String,
    pub geometry_sha256: String,
    pub captured_at_utc: Option<String>,
    pub row_order: String,
    pub per_row_timestamps_available: bool,
    pub paired_fill_available: bool,
    pub node_layout_id: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct StateGeometry {
    pub schema: String,
    pub source: GeometrySource,
    pub timing: GeometryTiming,
    pub missing_fields: Option<Vec<String>>,
    pub pca: PrincipalComponents,
    pub samples: Vec<GeometrySample>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometrySource {
    pub captured_at_utc: Option<String>,
    pub files: BTreeMap<String, GeometryFile>,
    pub consistency: Option<SourceConsistency>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometryFile {
    pub sha256: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct SourceConsistency {
    pub limitation: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometryTiming {
    pub row_order: Option<String>,
    pub row_unit: Option<String>,
    pub per_row_timestamps_available: Option<bool>,
    pub cadence_notes: Option<String>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct PrincipalComponents {
    pub rows: usize,
    pub dimensions: usize,
    pub mean: Vec<f64>,
    pub eigenvalues: Vec<f64>,
    pub components: Vec<Vec<f64>>,
    pub explained_variance_ratio: Vec<f64>,
    pub retained_fraction: f64,
    pub omitted_fraction: f64,
    pub total_sample_variance: f64,
    pub covariance_denominator: usize,
    pub normalization: GeometryNormalization,
    pub fit_scope: Option<String>,
    pub frozen: Option<bool>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometryNormalization {
    pub reference_radius: f64,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometrySample {
    pub index: usize,
    pub pc: Vec<f64>,
    pub state_rms: f64,
    pub centered_rms: f64,
    pub projected_rms: f64,
    pub reconstruction_rmse: f64,
    pub centered_norm: f64,
    pub projected_norm: f64,
    pub residual_norm: f64,
}
#[derive(Clone, Debug)]
pub struct StateReplay {
    pub manifest: StateReplayManifest,
    pub geometry: StateGeometry,
    raw: Vec<u8>,
}

/// Exact coordinate fields, not a mesh or a spatial interpretation. Display
/// scales are fixed: activations -1..1, magnitude 0..1, all deviations -2..2.
/// Values outside those scales remain unchanged; counts describe display limits.
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StateFields {
    pub magnitude: Vec<f64>,
    pub deviation: Vec<f64>,
    pub magnitude_out_of_range_count: usize,
    pub deviation_out_of_range_count: usize,
    pub scores: Vec<f64>,
    pub centered_energy: f64,
    pub selections: Vec<StateFieldSelection>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StateFieldSelection {
    pub selected_modes: Vec<usize>,
    /// The centered selected-mode contribution, without adding the mean.
    pub reconstruction: Vec<f64>,
    pub residual: Vec<f64>,
    pub reconstructed_energy: f64,
    pub residual_energy: f64,
    pub reconstruction_out_of_range_count: usize,
    pub residual_out_of_range_count: usize,
}

fn validate_reference(mean: &[f64], components: &[Vec<f64>], dimensions: usize) -> Result<()> {
    ensure(
        mean.len() == dimensions && mean.iter().all(|v| v.is_finite())
            && (1..=3).contains(&components.len())
            && components.iter().all(|c| c.len() == dimensions && c.iter().all(|v| v.is_finite())),
        "State fields require a finite coordinate-compatible mean and one to three frozen components.",
    )?;
    for (a, component) in components.iter().enumerate() {
        for (b, other) in components.iter().enumerate().take(a + 1) {
            let dot = component
                .iter()
                .zip(other)
                .fold(0.0, |sum, (x, y)| sum + x * y);
            ensure(
                (dot - if a == b { 1.0 } else { 0.0 }).abs() <= 1e-5,
                "State field components must be orthonormal within the native 1e-5 bound.",
            )?;
        }
    }
    Ok(())
}

/// Native StateSurfaceMath.field arithmetic: subtract the mean, take ordered
/// Double dot products, sum selected components, then subtract that contribution.
/// This does not refit PCA, normalize rows or infer any clock, fill or layout.
pub fn derive_state_fields(
    activations: &[f64],
    mean: &[f64],
    components: &[Vec<f64>],
    selections: &[Vec<usize>],
) -> Result<StateFields> {
    ensure(
        (1..=STATE_DIMENSIONS).contains(&activations.len())
            && activations
                .iter()
                .all(|v| v.is_finite() && (*v as f32).is_finite()),
        "State fields require one to 128 finite Float32-representable activations.",
    )?;
    ensure(
        selections.len() <= 8,
        "At most eight subsets of the three frozen modes may be requested.",
    )?;
    validate_reference(mean, components, activations.len())?;
    let magnitude: Vec<f64> = activations.iter().map(|v| v.abs()).collect();
    let deviation: Vec<f64> = activations.iter().zip(mean).map(|(x, m)| x - m).collect();
    let scores: Vec<f64> = components
        .iter()
        .map(|c| {
            c.iter()
                .zip(&deviation)
                .fold(0.0, |sum, (loading, value)| sum + loading * value)
        })
        .collect();
    let energy = |values: &[f64]| values.iter().fold(0.0, |sum, v| sum + v * v);
    let out_of_range =
        |values: &[f64]| values.iter().filter(|v| !(-2.0..=2.0).contains(*v)).count();
    let centered_energy = energy(&deviation);
    ensure(
        deviation.iter().chain(&scores).all(|v| v.is_finite()) && centered_energy.is_finite(),
        "State field subtraction or scores are nonfinite.",
    )?;
    let selections = selections
        .iter()
        .map(|requested| {
            let mut selected_modes = requested.clone();
            selected_modes.sort_unstable();
            selected_modes.dedup();
            ensure(
                selected_modes.iter().all(|i| *i < components.len()),
                "Selected state modes are outside the frozen components.",
            )?;
            let reconstruction: Vec<f64> = (0..activations.len())
                .map(|node| {
                    selected_modes.iter().fold(0.0, |sum, mode| {
                        sum + scores[*mode] * components[*mode][node]
                    })
                })
                .collect();
            let residual: Vec<f64> = deviation
                .iter()
                .zip(&reconstruction)
                .map(|(x, projected)| x - projected)
                .collect();
            let reconstructed_energy = energy(&reconstruction);
            let residual_energy = energy(&residual);
            ensure(
                reconstruction
                    .iter()
                    .chain(&residual)
                    .all(|v| v.is_finite() && (*v as f32).is_finite())
                    && reconstructed_energy.is_finite()
                    && residual_energy.is_finite(),
                "State field reconstruction or residual is not representable.",
            )?;
            Ok(StateFieldSelection {
                selected_modes,
                reconstructed_energy,
                residual_energy,
                reconstruction_out_of_range_count: out_of_range(&reconstruction),
                residual_out_of_range_count: out_of_range(&residual),
                reconstruction,
                residual,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    ensure(
        deviation.iter().all(|v| (*v as f32).is_finite()),
        "State deviation is not Float32-representable.",
    )?;
    Ok(StateFields {
        magnitude_out_of_range_count: magnitude
            .iter()
            .filter(|v| !(0.0..=1.0).contains(*v))
            .count(),
        deviation_out_of_range_count: out_of_range(&deviation),
        magnitude,
        deviation,
        scores,
        centered_energy,
        selections,
    })
}

impl StateReplay {
    pub fn from_bytes(manifest_bytes: &[u8], raw: Vec<u8>, geometry_bytes: &[u8]) -> Result<Self> {
        let m: StateReplayManifest = decode(manifest_bytes, 16 * 1024)?;
        let g: StateGeometry = decode(geometry_bytes, MAX_JSON_BYTES)?;
        if m.schema != "reservoir.state_replay.v1" || g.schema != "reservoir.state_geometry.v1" {
            return Err(CoreError::Unsupported(
                "Unsupported retained state or geometry schema.".into(),
            ));
        }
        ensure(m.dtype == "<f4" && m.layout == "row_major" && m.binary_file == "state-replay.bin"
            && (2..=MAX_STATE_ROWS).contains(&m.rows) && m.dimensions == STATE_DIMENSIONS
            && m.rows == g.pca.rows && m.dimensions == g.pca.dimensions && m.row_order == "oldest_to_newest"
            && !m.per_row_timestamps_available && !m.paired_fill_available && m.node_layout_id.is_none()
            && g.timing.row_order.as_deref() == Some(m.row_order.as_str()) && g.timing.per_row_timestamps_available == Some(false),
            "Expected bounded 128-coordinate ordinal state capture, with no invented time, paired fill or node-layout identity.")?;
        ensure(
            g.samples.len() == m.rows
                && g.pca.mean.len() == m.dimensions
                && g.pca.components.len() == 3
                && g.pca
                    .components
                    .iter()
                    .all(|c| c.len() == m.dimensions && c.iter().all(|v| v.is_finite()))
                && g.pca.eigenvalues.len() == m.dimensions
                && g.pca.explained_variance_ratio.len() == m.dimensions
                && g.pca
                    .mean
                    .iter()
                    .chain(&g.pca.eigenvalues)
                    .chain(&g.pca.explained_variance_ratio)
                    .all(|v| v.is_finite())
                && g.pca.retained_fraction.is_finite()
                && (0.0..=1.0).contains(&g.pca.retained_fraction)
                && g.pca.normalization.reference_radius.is_finite()
                && g.pca.normalization.reference_radius > 0.0,
            "Frozen PCA dimensions or numeric metadata are invalid.",
        )?;
        validate_reference(&g.pca.mean, &g.pca.components, m.dimensions)?;
        let pca = &g.pca;
        let total: f64 = pca.eigenvalues.iter().sum();
        let variance_sum: f64 = pca.explained_variance_ratio.iter().sum();
        let retained_sum: f64 = pca.explained_variance_ratio.iter().take(3).sum();
        ensure(
            pca.covariance_denominator == m.rows - 1
                && pca.eigenvalues.iter().all(|v| *v >= 0.0)
                && pca.eigenvalues.windows(2).all(|w| w[0] >= w[1])
                && pca
                    .explained_variance_ratio
                    .iter()
                    .all(|v| (0.0..=1.0).contains(v))
                && pca.total_sample_variance.is_finite()
                && pca.total_sample_variance > 0.0
                && (total - pca.total_sample_variance).abs() <= 1e-10 * total.max(1.0)
                && (variance_sum - 1.0).abs() <= 1e-10
                && (retained_sum - pca.retained_fraction).abs() <= 1e-10
                && pca.omitted_fraction.is_finite()
                && (0.0..=1.0).contains(&pca.omitted_fraction)
                && (pca.omitted_fraction + pca.retained_fraction - 1.0).abs() <= 1e-10
                && pca
                    .eigenvalues
                    .iter()
                    .zip(&pca.explained_variance_ratio)
                    .all(|(value, ratio)| {
                        (value / pca.total_sample_variance - ratio).abs() <= 1e-10
                    }),
            "Frozen sample-covariance spectrum, variance shares or denominator are inconsistent.",
        )?;
        for (index, s) in g.samples.iter().enumerate() {
            ensure(
                s.index == index
                    && s.pc.len() == 3
                    && s.pc.iter().all(|v| v.is_finite())
                    && [
                        s.state_rms,
                        s.centered_rms,
                        s.projected_rms,
                        s.reconstruction_rmse,
                        s.centered_norm,
                        s.projected_norm,
                        s.residual_norm,
                    ]
                    .iter()
                    .all(|v| v.is_finite() && *v >= 0.0),
                "Geometry row index, coordinates or distances are invalid.",
            )?;
        }
        ensure(
            digest(geometry_bytes) == m.geometry_sha256
                && g.source
                    .files
                    .get("states")
                    .and_then(|f| f.sha256.as_deref())
                    == Some(m.source_sha256.as_str())
                && m.captured_at_utc == g.source.captured_at_utc,
            "State replay does not bind this exact geometry and source identity.",
        )?;
        ensure(
            raw.len() == m.rows * m.dimensions * 4
                && raw.len() == m.byte_count
                && raw.len() <= MAX_STATE_BYTES
                && digest(&raw) == m.source_sha256,
            "State replay byte count or SHA-256 differs from manifest.",
        )?;
        ensure(
            raw.chunks_exact(4).all(|b| {
                let v = f32::from_le_bytes(b.try_into().unwrap());
                v.is_finite() && (-1.0..=1.0).contains(&v)
            }),
            "Retained activations must be finite and within −1…1.",
        )?;
        Ok(Self {
            manifest: m,
            geometry: g,
            raw,
        })
    }
    pub fn activations(&self, index: usize) -> Result<Vec<f64>> {
        ensure(
            index < self.manifest.rows,
            "State frame is outside retained coverage.",
        )?;
        Ok(
            self.raw[index * STATE_DIMENSIONS * 4..(index + 1) * STATE_DIMENSIONS * 4]
                .chunks_exact(4)
                .map(|b| f64::from(f32::from_le_bytes(b.try_into().unwrap())))
                .collect(),
        )
    }
    pub fn fields(&self, index: usize) -> Result<StateFields> {
        derive_state_fields(
            &self.activations(index)?,
            &self.geometry.pca.mean,
            &self.geometry.pca.components,
            &[vec![0], vec![1], vec![2], vec![0, 1, 2]],
        )
    }
    pub fn node(&self, index: usize, coordinate: usize) -> Result<f64> {
        ensure(
            index < self.manifest.rows && coordinate < STATE_DIMENSIONS,
            "State row or coordinate is outside retained coverage.",
        )?;
        let offset = (index * STATE_DIMENSIONS + coordinate) * 4;
        Ok(f64::from(f32::from_le_bytes(
            self.raw[offset..offset + 4].try_into().unwrap(),
        )))
    }
    pub fn seek(&self, position: f64, nearest: bool) -> Result<usize> {
        ensure(position.is_finite(), "Seek position must be finite.")?;
        let position = position.clamp(0.0, (self.manifest.rows - 1) as f64);
        // Earlier row wins an exact midpoint, matching history scrubbing.
        Ok(if nearest && position.fract() > 0.5 {
            position.ceil()
        } else {
            position.floor()
        } as usize)
    }
}

// Retained RFC3339-shaped timestamps are displayed verbatim. No wall-clock
// conversion is used to align evidence. Calendar validation prevents bogus dates.
fn valid_timestamp(s: &str) -> bool {
    let b = s.as_bytes();
    if b.len() < 20
        || b[4] != b'-'
        || b[7] != b'-'
        || b[10] != b'T'
        || b[13] != b':'
        || b[16] != b':'
    {
        return false;
    }
    let number = |start: usize, end: usize| -> Option<u32> {
        let p = b.get(start..end)?;
        if !p.iter().all(u8::is_ascii_digit) {
            return None;
        }
        std::str::from_utf8(p).ok()?.parse().ok()
    };
    let (Some(y), Some(m), Some(d), Some(h), Some(min), Some(sec)) = (
        number(0, 4),
        number(5, 7),
        number(8, 10),
        number(11, 13),
        number(14, 16),
        number(17, 19),
    ) else {
        return false;
    };
    if !(1..=12).contains(&m) || h > 23 || min > 59 || sec > 59 {
        return false;
    }
    let days = [
        31,
        if y % 4 == 0 && (y % 100 != 0 || y % 400 == 0) {
            29
        } else {
            28
        },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ][m as usize - 1];
    if d == 0 || d > days {
        return false;
    }
    let mut end = 19;
    if b.get(end) == Some(&b'.') {
        end += 1;
        let start = end;
        while b.get(end).is_some_and(u8::is_ascii_digit) {
            end += 1;
        }
        if end == start {
            return false;
        }
    }
    match b.get(end) {
        Some(b'Z') => end + 1 == b.len(),
        Some(b'+' | b'-') => {
            b.len() == end + 6
                && b[end + 3] == b':'
                && number(end + 1, end + 3).is_some_and(|v| v <= 23)
                && number(end + 4, end + 6).is_some_and(|v| v <= 59)
        }
        _ => false,
    }
}
