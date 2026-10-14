//! Bounded Unicode port of the retained Swift codec. Unqualified scalars or
//! multi-scalar graphemes return Unsupported; original UTF-8 remains unchanged.
use crate::{math::SpectralMeasurement, CoreError, Result};
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;
use unicode_segmentation::UnicodeSegmentation;
#[path = "codec_unicode_data.rs"]
mod unicode_data;

const LETTER: u8 = 1;
const NUMBER: u8 = 2;
const UPPERCASE: u8 = 4;
const WHITESPACE: u8 = 8;
const PUNCTUATION: u8 = 16;
const FOUNDATION_WHITESPACE: u8 = 32;
const FOUNDATION_NEWLINE: u8 = 64;
const FOUNDATION_TRIM: u8 = 128;

fn unsupported() -> CoreError {
    CoreError::Unsupported("Text codec scalar or grapheme is outside the retained Swift Unicode qualification; original UTF-8 bytes are retained".into())
}
fn scalar_flags(c: char) -> Option<u8> {
    let point = c as u32;
    let index = unicode_data::PROPERTIES.partition_point(|row| row.1 < point);
    unicode_data::PROPERTIES
        .get(index)
        .filter(|row| row.0 <= point)
        .map(|row| row.2)
}
fn scalar_has(c: char, flag: u8) -> bool {
    scalar_flags(c).is_some_and(|bits| bits & flag != 0)
}
fn flags(grapheme: &str) -> Result<u8> {
    // Swift Character equality and property lookup are canonically equivalent.
    let normalized: String = grapheme.nfc().collect();
    let mut chars = normalized.chars();
    let first = chars.next().ok_or_else(unsupported)?;
    if chars.next().is_none() {
        if grapheme.chars().any(|c| scalar_flags(c).is_none()) {
            return Err(unsupported());
        }
        return scalar_flags(first).ok_or_else(unsupported);
    }
    unicode_data::CLUSTERS
        .iter()
        .find(|(s, _)| s.nfc().eq(normalized.chars()))
        .map(|row| row.1)
        .ok_or_else(unsupported)
}
fn qualified_characters(text: &str) -> Result<Vec<(&str, u8)>> {
    text.graphemes(true)
        .map(|g| flags(g).map(|f| (g, f)))
        .collect()
}
/// Shared with the action envelope parser: native Foundation scalar trimming,
/// after the same bounded Unicode qualification used by the numerical codec.
pub fn has_non_whitespace(text: &str) -> Result<bool> {
    qualified_characters(text)?;
    Ok(text.chars().any(|c| !scalar_has(c, FOUNDATION_TRIM)))
}
fn lowercase(text: &str) -> String {
    let mut result = String::with_capacity(text.len());
    for c in text.chars() {
        match unicode_data::LOWERCASE.binary_search_by_key(&c, |row| row.0) {
            Ok(index) => result.push_str(unicode_data::LOWERCASE[index].1),
            Err(_) => result.push(c),
        }
    }
    result
}

// Native ellipsis matching does not split a final period carrying a combining
// mark. Paragraph separators separately use raw LF substring matching, including
// the final LF of CRLF (both behaviors have retained native vectors).
fn literal_components<'a>(text: &'a str, separator: &str) -> Vec<&'a str> {
    let mut boundaries = text
        .grapheme_indices(true)
        .map(|(i, _)| i)
        .collect::<BTreeSet<_>>();
    boundaries.insert(text.len());
    let mut from = 0;
    let mut parts = Vec::new();
    for (start, _) in text.match_indices(separator) {
        let end = start + separator.len();
        if start >= from && boundaries.contains(&start) && boundaries.contains(&end) {
            parts.push(&text[from..start]);
            from = end;
        }
    }
    parts.push(&text[from..]);
    parts
}

pub fn encode(text: &str) -> Result<Vec<f64>> {
    let characters = qualified_characters(text)?;
    let mut f = vec![0.0_f64; 48];
    if !text.chars().any(|c| !scalar_has(c, FOUNDATION_TRIM)) {
        return Ok(f);
    }
    let count = characters.len().max(1) as f64;
    let lower = lowercase(text);
    let lower_characters = qualified_characters(&lower)?;
    let mut words = Vec::<String>::new();
    let mut word = String::new();
    for (g, properties) in lower_characters {
        if properties & (LETTER | NUMBER) != 0 || g == "'" {
            word.push_str(g);
        } else if !word.is_empty() {
            words.push(std::mem::take(&mut word));
        }
    }
    if !word.is_empty() {
        words.push(word);
    }
    let word_count = words.len().max(1) as f64;
    let mut sentences = Vec::<Vec<(&str, u8)>>::new();
    let mut sentence = Vec::new();
    for &(g, properties) in &characters {
        if [".", "!", "?"].contains(&g) {
            if !sentence.is_empty() {
                sentences.push(std::mem::take(&mut sentence));
            }
        } else {
            sentence.push((g, properties));
        }
    }
    if !sentence.is_empty() {
        sentences.push(sentence);
    }
    let sentence_count = sentences.len().max(1) as f64;
    let lengths: Vec<f64> = sentences
        .iter()
        .map(|s| {
            s.split(|(_, flags)| flags & WHITESPACE != 0)
                .filter(|part| !part.is_empty())
                .count() as f64
        })
        .collect();
    let mean_length = lengths.iter().sum::<f64>() / sentence_count;
    let variance = lengths
        .iter()
        .map(|x| (x - mean_length).powi(2))
        .sum::<f64>()
        / sentence_count;
    let mut frequencies = BTreeMap::<String, usize>::new();
    for (c, _) in &characters {
        *frequencies.entry(c.nfc().collect()).or_default() += 1;
    }
    let entropy = frequencies.values().fold(0.0, |sum, frequency| {
        let p = *frequency as f64 / count;
        sum - p * p.log2()
    });
    let density = |flag: u8| {
        characters
            .iter()
            .filter(|(_, bits)| bits & flag != 0)
            .count() as f64
            / count
    };
    let occurrences = |c: &str| characters.iter().filter(|(g, _)| *g == c).count() as f64;
    let marks = |set: &[&str], gain: f64| {
        (gain
            * words
                .iter()
                .filter(|word| set.contains(&word.as_str()))
                .count() as f64
            / word_count)
            .tanh()
    };
    f[0] = entropy.tanh();
    f[1] = (1.2
        * characters
            .iter()
            .filter(|(_, bits)| bits & PUNCTUATION != 0)
            .count() as f64
        / word_count)
        .tanh();
    f[2] = (2.0 * density(UPPERCASE)).tanh();
    f[3] = (3.0 * density(NUMBER)).tanh();
    f[4] = ((words
        .iter()
        .map(|s| s.graphemes(true).count() as f64)
        .sum::<f64>()
        / word_count
        - 4.5)
        / 2.0)
        .tanh();
    let scalars: Vec<f64> = text.chars().map(|c| c as u32 as f64).collect();
    if scalars.len() > 1 {
        let movement: f64 = scalars
            .windows(2)
            .map(|pair| (pair[0] - pair[1]).abs())
            .sum();
        f[5] = (movement / (scalars.len() - 1) as f64 / 30.0).tanh();
    }
    f[6] = (2.0 * (density(WHITESPACE) - 0.15)).tanh();
    f[7] = (5.0
        * characters
            .iter()
            .filter(|(_, bits)| bits & (LETTER | NUMBER | WHITESPACE | PUNCTUATION) == 0)
            .count() as f64
        / count)
        .tanh();
    f[8] = (2.0
        * (words
            .iter()
            .map(|word| word.nfc().collect::<String>())
            .collect::<BTreeSet<_>>()
            .len() as f64
            / word_count
            - 0.5))
        .tanh();
    f[9] = marks(
        &[
            "perhaps",
            "maybe",
            "might",
            "could",
            "seems",
            "possibly",
            "uncertain",
        ],
        3.0,
    );
    f[10] = marks(
        &["certain", "clearly", "definitely", "always", "must", "know"],
        1.8,
    );
    f[11] = marks(
        &[
            "not", "no", "never", "neither", "without", "cannot", "don't",
        ],
        1.2,
    );
    f[12] = marks(&["i", "me", "my", "mine", "myself", "we", "our", "us"], 2.0);
    f[13] = marks(&["you", "your", "yours", "yourself"], 3.0);
    f[14] = marks(
        &[
            "move", "change", "make", "build", "try", "act", "explore", "choose",
        ],
        2.0,
    );
    f[15] = marks(
        &[
            "and",
            "but",
            "or",
            "because",
            "while",
            "although",
            "therefore",
        ],
        3.0,
    );
    f[16] = ((word_count / sentence_count - 12.0) / 8.0).tanh();
    f[17] = (variance.sqrt() / 8.0).tanh();
    f[18] = (2.0 * occurrences("?") / sentence_count).tanh();
    f[19] = (2.0 * occurrences("!") / sentence_count).tanh();
    f[20] =
        (literal_components(text, "...").len().saturating_sub(1) as f64 / sentence_count).tanh();
    let lists = text
        .split(|c| scalar_has(c, FOUNDATION_NEWLINE))
        .filter(|s| {
            let s = s.trim_matches(|c| scalar_has(c, FOUNDATION_WHITESPACE));
            let mut g = s.graphemes(true);
            matches!(g.next(), Some("-" | "*" | "•")) && g.next() == Some(" ")
        })
        .count();
    f[21] = (lists as f64 / sentence_count).tanh();
    f[22] = ((occurrences("\"") + occurrences("“") + occurrences("”")) / sentence_count).tanh();
    f[23] = (text
        .split("\n\n")
        .filter(|s| !s.is_empty())
        .count()
        .saturating_sub(1) as f64
        / 3.0)
        .tanh();
    f[24] = marks(
        &[
            "warm", "care", "love", "gentle", "kind", "together", "thank", "safe",
        ],
        3.0,
    );
    f[25] = marks(
        &[
            "tense",
            "pressure",
            "fear",
            "strain",
            "tight",
            "worry",
            "pain",
            "difficult",
        ],
        3.0,
    );
    f[26] = marks(
        &[
            "wonder", "curious", "question", "explore", "discover", "why", "how",
        ],
        2.0,
    );
    f[27] = marks(
        &[
            "reflect",
            "notice",
            "consider",
            "understand",
            "remember",
            "think",
            "observe",
        ],
        3.0,
    );
    f[28] = marks(
        &[
            "before", "after", "now", "then", "later", "again", "still", "time",
        ],
        3.0,
    );
    f[29] = marks(
        &[
            "small", "large", "deep", "wide", "little", "much", "more", "less",
        ],
        3.0,
    );
    f[30] = (count.ln() / 7.0).tanh();
    f[31] = (f.iter().take(31).fold(0.0, |sum, x| sum + x * x) / 31.0).sqrt();
    for value in f.iter_mut().take(32) {
        *value = (*value * 2.0).clamp(-5.0, 5.0);
    }
    Ok(f)
}

pub fn feedback(features: &[f64], measurement: &SpectralMeasurement) -> Vec<f64> {
    if features.len() != 48 || features.iter().any(|x| !x.is_finite()) {
        return features.to_vec();
    }
    let mut result = features.to_vec();
    let concentration = ((measurement.head_share - 0.55) / 0.45).clamp(0.0, 1.0);
    let low_entropy = ((0.45 - measurement.entropy) / 0.45).clamp(0.0, 1.0);
    let damping = (0.6 * concentration + 0.4 * low_entropy).clamp(0.0, 1.0);
    let lift = (0.45 * (measurement.shoulder_share / 0.35).min(1.0)
        + 0.35 * (measurement.tail_share / 0.30).min(1.0)
        + 0.20 * ((measurement.entropy - 0.55) / 0.45).clamp(0.0, 1.0))
    .clamp(0.0, 1.0);
    result[26] *= 1.0 - 0.18 * damping;
    result[27] *= 1.0 - 0.14 * damping;
    result[31] *= 1.0 - 0.12 * damping;
    result[17] += 0.18 * lift;
    result[26] += 0.22 * lift;
    result[27] += 0.18 * lift;
    result[31] += 0.16 * lift;
    for value in result.iter_mut().take(32) {
        *value = value.clamp(-5.0, 5.0);
    }
    result[32..].fill(0.0);
    result
}
