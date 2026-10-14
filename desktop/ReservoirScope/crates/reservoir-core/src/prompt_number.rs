//! Native prompt numbers use Foundation's locale-aware `%.8f`, whose decimal
//! rounding differs from ordinary binary printf/Rust precision at decimal ties.
//! The retained Swift oracle qualifies shortest-decimal, ties-to-even behavior
//! on bounded prompt values, neighboring ties, signed zero and tiny/large probes.

pub(crate) fn fixed8(value: f64) -> String {
    debug_assert!(value.is_finite(), "prompt observations must be finite");
    // Rust Display supplies a shortest round-tripping decimal, in fixed form.
    // Round its decimal digits directly; multiplying the binary value by 1e8
    // would reintroduce exactly the ambiguity this contract needs to preserve.
    let decimal = value.abs().to_string();
    let (whole, fraction) = decimal.split_once('.').unwrap_or((&decimal, ""));
    let mut digits = whole.as_bytes().to_vec();
    digits.extend(fraction.bytes().take(8));
    digits.resize(whole.len() + 8, b'0');
    let remainder = fraction.as_bytes().get(8..).unwrap_or_default();
    let round_up = remainder.first().is_some_and(|digit| {
        *digit > b'5'
            || (*digit == b'5'
                && (remainder[1..].iter().any(|d| *d != b'0')
                    || (digits.last().unwrap() - b'0') % 2 == 1))
    });
    if round_up {
        let mut carry = true;
        for digit in digits.iter_mut().rev() {
            if *digit == b'9' {
                *digit = b'0';
            } else {
                *digit += 1;
                carry = false;
                break;
            }
        }
        if carry {
            digits.insert(0, b'1');
        }
    }
    digits.insert(digits.len() - 8, b'.');
    if value.is_sign_negative() {
        digits.insert(0, b'-');
    }
    String::from_utf8(digits).expect("finite decimal formatting contains ASCII digits")
}

#[cfg(test)]
mod tests {
    use super::fixed8;
    #[test]
    fn matches_retained_swift_locale_aware_oracle() {
        let fixture: serde_json::Value = serde_json::from_str(include_str!(
            "../tests/fixtures/swift-prompt-fixed8-v1.json"
        ))
        .unwrap();
        let rows = fixture["vectors"].as_array().unwrap();
        assert_eq!(rows.len(), 1173);
        for row in rows {
            let bits = u64::from_str_radix(row["bits"].as_str().unwrap(), 16).unwrap();
            assert_eq!(
                fixed8(f64::from_bits(bits)),
                row["expected"],
                "bits {bits:016x}"
            );
        }
    }
}
