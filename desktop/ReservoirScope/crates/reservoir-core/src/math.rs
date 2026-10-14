//! Fresh Rust translation of the bounded Essentials mechanisms. No ambient RNG,
//! threads, files, network or rendering. Float tolerances live in the verifier.
use crate::{ensure, CoreError, Result};
use nalgebra::{DMatrix, SymmetricEigen};
use serde::{Deserialize, Serialize};

pub const FIELD_SEED: u64 = 0x53454E534F5259;
pub const NOISE_SEED: u64 = 0x4E4F495345;

#[derive(Clone, Debug)]
pub struct SplitMix64 {
    pub state: u64,
}
impl SplitMix64 {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }
    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }
    pub fn unit(&mut self) -> f64 {
        ((self.next_u64() >> 11) as f64) * (1.0 / 9007199254740992.0)
    }
    pub fn signed(&mut self) -> f64 {
        2.0 * self.unit() - 1.0
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ReservoirModel {
    pub node_count: usize,
    pub input_count: usize,
    pub recurrent_weights: Vec<f64>,
    pub input_weights: Vec<f64>,
}
impl ReservoirModel {
    pub fn seeded(seed: u64) -> Self {
        let mut rng = SplitMix64::new(seed);
        let (n, m) = (32, 66);
        let mut input_weights = vec![0.0; n * (m + 1)];
        for row in 0..n {
            for column in 0..=m {
                let boost = if column < m {
                    if column >= 18 {
                        1.6
                    } else if column >= 16 {
                        1.2
                    } else {
                        1.0
                    }
                } else {
                    1.0
                };
                input_weights[row * (m + 1) + column] = rng.signed() * 0.5 * boost;
            }
        }
        let mut recurrent_weights = vec![0.0; n * n];
        for weight in &mut recurrent_weights {
            if rng.unit() < 0.1 {
                *weight = rng.signed();
            }
        }
        let maximum = recurrent_weights
            .chunks(n)
            .map(|row| row.iter().fold(0.0, |sum, x| sum + x.abs()))
            .fold(0.0, f64::max);
        if maximum > 0.0 {
            for weight in &mut recurrent_weights {
                *weight = *weight * 0.9 / maximum;
            }
        }
        Self {
            node_count: n,
            input_count: m,
            recurrent_weights,
            input_weights,
        }
    }
    pub fn validate(&self) -> Result<()> {
        ensure(
            (1..=4096).contains(&self.node_count) && (1..=4096).contains(&self.input_count),
            "Invalid model dimensions",
        )?;
        vector(
            &self.recurrent_weights,
            self.node_count * self.node_count,
            "recurrent weights",
        )?;
        vector(
            &self.input_weights,
            self.node_count * (self.input_count + 1),
            "input weights",
        )
    }
}

pub struct ReservoirEngine {
    pub model: ReservoirModel,
    pub leak: f64,
    pub state: Vec<f64>,
}
impl ReservoirEngine {
    pub fn new(model: ReservoirModel, leak: f64, state: Option<Vec<f64>>) -> Result<Self> {
        model.validate()?;
        ensure(
            leak.is_finite() && (0.0..=1.0).contains(&leak),
            "Invalid leak",
        )?;
        let state = state.unwrap_or_else(|| vec![0.0; model.node_count]);
        vector(&state, model.node_count, "initial state")?;
        ensure(
            state.iter().all(|x| x.abs() <= 1.0),
            "Initial state outside [-1,1]",
        )?;
        Ok(Self { model, leak, state })
    }
    pub fn step(&mut self, input: &[f64], noise: &[f64]) -> Result<Vec<f64>> {
        vector(input, self.model.input_count, "input")?;
        if !noise.is_empty() {
            vector(noise, self.model.node_count, "noise")?;
        }
        let (n, m) = (self.model.node_count, self.model.input_count);
        let mut next = vec![0.0; n];
        for (row, next_value) in next.iter_mut().enumerate() {
            let mut drive = self.model.input_weights[row * (m + 1) + m];
            for (column, x) in input.iter().enumerate() {
                drive += self.model.input_weights[row * (m + 1) + column] * x;
            }
            for column in 0..n {
                drive += self.model.recurrent_weights[row * n + column] * self.state[column];
            }
            let value = (1.0 - self.leak) * self.state[row]
                + self.leak * drive.tanh()
                + noise.get(row).copied().unwrap_or(0.0);
            ensure(value.is_finite(), "Nonfinite recurrence")?;
            *next_value = value.clamp(-1.0, 1.0);
        }
        self.state = next.clone();
        Ok(next)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SpectralMeasurement {
    pub dimension: usize,
    pub eigenvalues: Vec<f64>,
    /// Mode-major, one full vector per descending eigenvalue.
    pub eigenvectors: Vec<f64>,
    pub field_vector: Vec<f64>,
    pub covariance: Vec<f64>,
    pub entropy: f64,
    pub head_share: f64,
    pub shoulder_share: f64,
    pub tail_share: f64,
}

pub struct SensoryField {
    pub dimension: usize,
    pub input_count: usize,
    pub projection: Vec<f64>,
    pub covariance: Vec<f64>,
}
impl SensoryField {
    pub fn seeded(seed: u64) -> Self {
        let mut rng = SplitMix64::new(seed);
        Self::new(32, 66, (0..2112).map(|_| rng.signed()).collect(), None)
            .expect("fixed dimensions")
    }
    pub fn new(
        dimension: usize,
        input_count: usize,
        projection: Vec<f64>,
        covariance: Option<Vec<f64>>,
    ) -> Result<Self> {
        ensure(
            (1..=4096).contains(&dimension) && (1..=4096).contains(&input_count),
            "Invalid field dimensions",
        )?;
        vector(&projection, dimension * input_count, "projection")?;
        let covariance = covariance.unwrap_or_else(|| {
            let mut matrix = vec![0.0; dimension * dimension];
            for i in 0..dimension {
                matrix[i * dimension + i] = 1.0;
            }
            matrix
        });
        vector(&covariance, dimension * dimension, "covariance")?;
        for i in 0..dimension {
            for j in 0..i {
                ensure(
                    (covariance[i * dimension + j] - covariance[j * dimension + i]).abs() <= 1e-10,
                    "Covariance must be symmetric",
                )?;
            }
        }
        Ok(Self {
            dimension,
            input_count,
            projection,
            covariance,
        })
    }
    pub fn step(&mut self, input: &[f64], retention: f64) -> Result<SpectralMeasurement> {
        vector(input, self.input_count, "field input")?;
        ensure(
            retention.is_finite() && (0.0..=0.9999).contains(&retention),
            "Invalid retention",
        )?;
        let activated: Vec<f64> = input
            .iter()
            .enumerate()
            .map(|(i, x)| {
                let scale = if i < 8 {
                    0.75
                } else if i < 16 {
                    0.72
                } else if i < 18 {
                    1.12
                } else {
                    0.42
                };
                (x * scale * 0.58).tanh()
            })
            .collect();
        let n = self.dimension;
        let mut z = vec![0.0; n];
        for (row, z_row) in z.iter_mut().enumerate() {
            for (column, value) in activated.iter().enumerate() {
                *z_row += self.projection[row * self.input_count + column] * value;
            }
            *z_row /= (self.input_count as f64).sqrt();
        }
        let rms = (z.iter().fold(0.0, |sum, x| sum + x * x) / n as f64).sqrt();
        if rms > 1e-12 {
            for x in &mut z {
                *x /= rms;
            }
        } else {
            z.fill(0.0);
        }
        let mut next = self.covariance.clone();
        for row in 0..n {
            for column in 0..n {
                next[row * n + column] = retention * self.covariance[row * n + column]
                    + (1.0 - retention) * z[row] * z[column];
            }
        }
        let trace = (0..n).fold(0.0, |sum, i| sum + next[i * n + i]);
        if rms > 1e-12 && trace > 1e-12 {
            let scale = (n as f64 / trace).min(2.0);
            for x in &mut next {
                *x *= scale;
            }
        }
        let (eigenvalues, eigenvectors) = eigensystem(&next, n)?;
        let (entropy, head_share, shoulder_share, tail_share) = spectral_summary(&eigenvalues);
        self.covariance = next.clone();
        Ok(SpectralMeasurement {
            dimension: n,
            eigenvalues,
            eigenvectors,
            field_vector: z,
            covariance: next,
            entropy,
            head_share,
            shoulder_share,
            tail_share,
        })
    }
}

pub fn eigensystem(matrix: &[f64], dimension: usize) -> Result<(Vec<f64>, Vec<f64>)> {
    ensure(
        (1..=4096).contains(&dimension),
        "Invalid eigensystem dimension",
    )?;
    vector(matrix, dimension * dimension, "eigensystem matrix")?;
    // A bounded iteration budget makes corrupt/unconverged input a failure rather than a hang.
    let eigen = SymmetricEigen::try_new(
        DMatrix::from_row_slice(dimension, dimension, matrix),
        1e-14,
        100_000,
    )
    .ok_or_else(|| CoreError::Invalid("Symmetric eigensolver did not converge".into()))?;
    let mut order: Vec<usize> = (0..dimension).collect();
    order.sort_by(|a, b| eigen.eigenvalues[*b].total_cmp(&eigen.eigenvalues[*a]));
    let values = order
        .iter()
        .map(|i| eigen.eigenvalues[*i].max(0.0))
        .collect();
    let mut vectors = Vec::with_capacity(dimension * dimension);
    for column in order {
        let mut v: Vec<f64> = eigen.eigenvectors.column(column).iter().copied().collect();
        let largest = (0..dimension)
            .max_by(|a, b| v[*a].abs().total_cmp(&v[*b].abs()))
            .unwrap();
        if v[largest] < 0.0 {
            for x in &mut v {
                *x = -*x;
            }
        }
        vectors.extend(v);
    }
    Ok((values, vectors))
}

pub fn spectral_summary(eigenvalues: &[f64]) -> (f64, f64, f64, f64) {
    let values: Vec<f64> = eigenvalues
        .iter()
        .take(8)
        .map(|x| if x.is_finite() { x.max(0.0) } else { 0.0 })
        .collect();
    let total: f64 = values.iter().sum();
    if total <= 1e-12 {
        return (0.0, 0.0, 0.0, 0.0);
    }
    let shares: Vec<f64> = values.iter().map(|x| x / total).collect();
    let entropy = shares
        .iter()
        .fold(0.0, |sum, x| sum + if *x > 0.0 { -x * x.ln() } else { 0.0 });
    (
        if shares.len() > 1 {
            entropy / (shares.len() as f64).ln()
        } else {
            0.0
        },
        shares[0],
        shares.iter().skip(1).take(2).sum(),
        shares.iter().skip(3).sum(),
    )
}

#[derive(Default)]
pub struct ReducedFill {
    pub fill: f64,
}
impl ReducedFill {
    pub fn update(&mut self, values: &[f64], dt: f64) -> f64 {
        if !dt.is_finite() || dt < 0.0 || values.is_empty() || values.iter().any(|x| !x.is_finite())
        {
            return self.fill;
        }
        let mean = values.iter().fold(0.0, |sum, x| sum + x.max(0.0)) / values.len() as f64;
        let active = if mean > 1e-12 {
            values.iter().filter(|x| x.max(0.0) > 0.12 * mean).count()
        } else {
            0
        };
        let instant = if active > 0 {
            (active as f64 / values.len() as f64).max(0.04)
        } else {
            0.0
        };
        self.fill =
            (0.10 * instant + 0.90 * (1.0 - (0.006 * dt).min(0.15)) * self.fill).clamp(0.0, 1.0);
        self.fill
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ControlMeasurement {
    pub error: f64,
    pub integral: f64,
    pub requested_retention: f64,
    pub applied_retention: f64,
}
pub struct RetentionController {
    pub current_retention: f64,
    pub integral: f64,
}
impl RetentionController {
    pub fn new(initial_retention: f64) -> Result<Self> {
        ensure(
            initial_retention.is_finite() && (0.82..=0.995).contains(&initial_retention),
            "Invalid initial retention",
        )?;
        Ok(Self {
            current_retention: initial_retention,
            integral: 0.0,
        })
    }
    pub fn update(&mut self, fill_pct: f64) -> ControlMeasurement {
        if !fill_pct.is_finite() {
            return ControlMeasurement {
                error: 0.0,
                integral: self.integral,
                requested_retention: self.current_retention,
                applied_retention: self.current_retention,
            };
        }
        let error = fill_pct - 68.0;
        let e = (if error < 0.0 { -1.0 } else { 1.0 }) * (error.abs() - 4.0).max(0.0) / 20.0;
        let tentative = (0.85 * self.integral + e).clamp(-1.0, 1.0);
        let u = (0.55 * e + 0.04 * tentative).clamp(-0.12, 0.12);
        let requested = (0.955 - u).clamp(0.82, 0.995);
        if (requested <= 0.82 && e > 0.0) || (requested >= 0.995 && e < 0.0) {
            self.integral *= 0.85;
        } else {
            self.integral = tentative;
        }
        self.current_retention += (requested - self.current_retention).clamp(-0.01, 0.01);
        ControlMeasurement {
            error,
            integral: self.integral,
            requested_retention: requested,
            applied_retention: self.current_retention,
        }
    }
}

pub fn forcing(step: usize, dt: f64) -> Vec<f64> {
    let mut input = vec![0.0; 66];
    if (step - 1) % 30 >= 12 {
        return input;
    }
    let time = (step - 1) as f64 * dt;
    for (i, x) in input.iter_mut().enumerate().take(8) {
        *x = 0.45 + 0.35 * (time * (0.19 + i as f64 * 0.07) + i as f64).sin();
    }
    for (i, x) in input.iter_mut().enumerate().take(16).skip(8) {
        *x = 0.3 + 0.25 * (time * (0.31 + (i - 8) as f64 * 0.11) + i as f64 * 0.7).sin();
    }
    input
}

pub(crate) fn vector(values: &[f64], count: usize, label: &str) -> Result<()> {
    ensure(
        values.len() == count && values.iter().all(|x| x.is_finite()),
        &format!("Invalid {label} dimensions or nonfinite values"),
    )
}
pub(crate) fn near(a: f64, e: f64, label: &str) -> Result<()> {
    ensure(
        a.is_finite() && e.is_finite() && (a - e).abs() <= 2e-7 * e.abs().max(1.0),
        &format!("{label} does not replay ({a}, expected {e})"),
    )
}
pub(crate) fn near_vec(a: &[f64], e: &[f64], label: &str) -> Result<()> {
    ensure(a.len() == e.len(), &format!("{label} dimensions differ"))?;
    for (i, (a, e)) in a.iter().zip(e).enumerate() {
        near(*a, *e, &format!("{label}[{i}]"))?;
    }
    Ok(())
}
