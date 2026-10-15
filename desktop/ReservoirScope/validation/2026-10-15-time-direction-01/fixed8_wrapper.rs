//! Validation-only stdin/stdout adapter. No model, network or application code.
//! Each line is `value HEXBITS` or `difference HEXBITS HEXBITS`.
//! Output: result bits, existing fixed8, signed fixed8 (tab separated).
#[path = "../../crates/reservoir-core/src/prompt_number.rs"]
mod prompt_number;

use std::io::{self, BufRead};

fn number(s: &str) -> Result<f64, String> {
    if s.len() != 16 || !s.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("Expected exactly 16 hexadecimal binary64 digits".into());
    }
    let value = f64::from_bits(u64::from_str_radix(s, 16).map_err(|e| e.to_string())?);
    if !value.is_finite() {
        return Err("Non-finite input".into());
    }
    Ok(value)
}

fn run() -> Result<(), String> {
    for line in io::stdin().lock().lines() {
        let line = line.map_err(|e| e.to_string())?;
        let fields: Vec<_> = line.split_whitespace().collect();
        let value = match fields.as_slice() {
            ["value", a] => number(a)?,
            ["difference", a, b] => number(a)? - number(b)?,
            _ => return Err("Expected value or difference with exact operand count".into()),
        };
        if !value.is_finite() {
            return Err("Non-finite result".into());
        }
        let formatted = prompt_number::fixed8(value);
        let signed = if formatted.starts_with('-') {
            formatted.clone()
        } else {
            format!("+{formatted}")
        };
        println!("{:016x}\t{formatted}\t{signed}", value.to_bits());
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
