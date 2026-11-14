//! Offline representation diagnostics, never a provider call or production codec change.
//! Input: frozen corpus JSON, optionally carrying retained local embeddings.
//! Output includes vectors but no prose. Wider projections are comparison instruments.
use reservoir_core::{codec, math::SplitMix64};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, error::Error, fs};

fn projected_width(embedding: &[f64], seed: u64, width: usize) -> Vec<f64> {
    let norm = embedding.iter().map(|x| x * x).sum::<f64>().sqrt();
    let unit: Vec<_> = embedding.iter().map(|x| x / norm).collect();
    let mut rng = SplitMix64::new(seed);
    let mut out = vec![0.0; width];
    let scale = 1.0 / (unit.len() as f64).sqrt();
    for slot in &mut out {
        let mut acc = 0.0;
        for pair in unit.chunks(2) {
            let radius = (-2.0 * rng.unit().max(1e-300).ln()).sqrt();
            let angle = 2.0 * std::f64::consts::PI * rng.unit();
            acc += radius * angle.cos() * pair[0];
            if pair.len() == 2 {
                acc += radius * angle.sin() * pair[1];
            }
        }
        *slot = acc * scale;
    }
    // Hold total input energy fixed, rather than adding energy with dimension.
    let norm = out.iter().map(|x| x * x).sum::<f64>().sqrt();
    let gain = codec::EMBEDDING_TARGET_RMS * 32.0_f64.sqrt() / norm;
    for value in &mut out {
        *value = (*value * gain).clamp(-5.0, 5.0);
    }
    out
}

fn lexical_control(text: &str) -> Vec<f64> {
    let lower = text.to_lowercase();
    let words: Vec<_> = lower
        .split(|c: char| !c.is_alphanumeric() && c != '\'')
        .filter(|x| !x.is_empty())
        .collect();
    let mut out = vec![0.0; 32];
    let mut add = |feature: &str, weight: f64| {
        let hash = Sha256::digest(feature.as_bytes());
        let index = u64::from_le_bytes(hash[..8].try_into().unwrap()) as usize % 32;
        out[index] += weight * if hash[8] & 1 == 0 { 1.0 } else { -1.0 };
    };
    for word in &words {
        add(&format!("word:{word}"), 1.0);
    }
    for pair in words.windows(2) {
        add(&format!("pair:{} {}", pair[0], pair[1]), 0.5);
    }
    let norm = out.iter().map(|x| x * x).sum::<f64>().sqrt();
    if norm > 0.0 {
        for x in &mut out {
            *x *= codec::EMBEDDING_TARGET_RMS * 32.0_f64.sqrt() / norm;
        }
    }
    out
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 3 {
        return Err("Usage: codec_distinction CORPUS.json OUTPUT.json (offline only)".into());
    }
    let bytes = fs::read(&args[1])?;
    let corpus: Value = serde_json::from_slice(&bytes)?;
    let seeds: Vec<u64> = serde_json::from_value(corpus["projectionSeeds"].clone())?;
    let items = corpus["items"].as_array().ok_or("items must be an array")?;
    let mut rows = Vec::new();
    for item in items {
        let text = item["text"].as_str().ok_or("missing text")?;
        let mut vectors = BTreeMap::<String, Vec<f64>>::new();
        let features = codec::encode(text)?;
        if let Some(retained) = item.get("retainedSurface") {
            let retained: Vec<f64> = serde_json::from_value(retained.clone())?;
            if features != retained {
                return Err(format!("Surface encoding changed for {}", item["id"]).into());
            }
        }
        vectors.insert("surface".into(), features);
        vectors.insert("lexical-hash32-control".into(), lexical_control(text));
        if let Some(retained) = item.get("retainedFeedback") {
            vectors.insert(
                "retained-surface-feedback".into(),
                serde_json::from_value(retained.clone())?,
            );
        }
        if let Some(embedding) = item.get("embedding") {
            let embedding: Vec<f64> = serde_json::from_value(embedding.clone())?;
            if embedding.is_empty() || embedding.iter().any(|x| !x.is_finite()) {
                return Err("Invalid embedding".into());
            }
            vectors.insert("embedding-raw".into(), embedding.clone());
            for &seed in &seeds {
                let actual = codec::project_embedding(&embedding, seed)?;
                let check = projected_width(&embedding, seed, 32);
                if actual[..32]
                    .iter()
                    .zip(&check)
                    .any(|(a, b)| (a - b).abs() > 1e-12)
                {
                    return Err("Diagnostic 32 projection differs from production".into());
                }
                vectors.insert(format!("embedding32-seed{seed}"), actual);
                for width in [48, 64, 128] {
                    vectors.insert(
                        format!("diagnostic{width}-seed{seed}"),
                        projected_width(&embedding, seed, width),
                    );
                }
            }
        }
        rows.push(json!({"id":item["id"],"cohort":item["cohort"],"group":item.get("group"),"role":item.get("role"),"source":item.get("source"),"textSha256":format!("{:x}",Sha256::digest(text.as_bytes())),"utf8Bytes":text.len(),"unicodeScalars":text.chars().count(),"vectors":vectors}));
    }
    let output = json!({"format":"codec-distinction-v1","corpusSha256":format!("{:x}",Sha256::digest(&bytes)),"projectionSeeds":seeds,"targetL2":codec::EMBEDDING_TARGET_RMS*32.0_f64.sqrt(),"productionUsedDimensions":32,"productionLayoutDimensions":48,"rows":rows});
    fs::write(&args[2], serde_json::to_string_pretty(&output)? + "\n")?;
    println!(
        "Encoded {} frozen texts without a provider call.",
        items.len()
    );
    Ok(())
}
