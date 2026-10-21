use super::*;
use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    sync::{mpsc, Arc},
    thread,
};

fn configuration(endpoint: String) -> LanguageConfiguration {
    serde_json::from_value(json!({"backend":"ollama","endpoint":endpoint,"model":"owned-fixture:exact","contextTokens":4096,"responseFormat":"json"})).unwrap()
}
fn accept_request(stream: &mut TcpStream) -> String {
    stream
        .set_read_timeout(Some(Duration::from_secs(3)))
        .unwrap();
    let mut bytes = Vec::new();
    let mut buf = [0; 4096];
    loop {
        let n = stream.read(&mut buf).unwrap();
        assert!(n > 0, "request ended early");
        bytes.extend_from_slice(&buf[..n]);
        if let Some(p) = bytes.windows(4).position(|w| w == b"\r\n\r\n") {
            let headers = String::from_utf8_lossy(&bytes[..p]);
            let length = headers
                .lines()
                .find_map(|line| {
                    line.to_ascii_lowercase()
                        .strip_prefix("content-length: ")
                        .and_then(|s| s.parse::<usize>().ok())
                })
                .unwrap_or(0);
            if bytes.len() >= p + 4 + length {
                return String::from_utf8(bytes).unwrap();
            }
        }
        assert!(bytes.len() < 2 * MAXIMUM_BYTES);
    }
}
fn server(
    handler: impl FnOnce(&mut TcpStream, String) + Send + 'static,
) -> (String, thread::JoinHandle<()>) {
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    let address = listener.local_addr().unwrap();
    let handle = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let request = accept_request(&mut stream);
        handler(&mut stream, request);
    });
    (format!("http://{address}"), handle)
}
fn respond(stream: &mut TcpStream, status: u16, body: &[u8]) {
    let header=format!("HTTP/1.1 {status} Fixture\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",body.len());
    stream.write_all(header.as_bytes()).unwrap();
    let _ = stream.write_all(body);
}
fn envelope() -> serde_json::Value {
    json!({"done":true,"message":{"content":"{\"action\":\"WAIT\"}"},"model":"owned-fixture:exact","done_reason":"stop","eval_count":18})
}

#[test]
fn operational_endpoint_boundary_is_loopback_only() {
    for address in [
        "http://127.0.0.1:11434",
        "http://localhost:1/",
        "http://[::1]:65535",
    ] {
        assert!(
            validate_configuration(&configuration(address.into())).is_ok(),
            "{address}"
        );
    }
    for address in [
        "https://localhost:11434",
        "http://example.org:11434",
        "http://localhost:0",
        "http://localhost:65536",
        "http://localhost:-1",
        "http://localhost:80/path",
        "http://localhost:80//",
        "http://localhost:80/?x=1",
        "http://user@localhost:80",
        "http://localhost:80/#x",
        "http://127.1:80",
        "http://2130706433:80",
    ] {
        assert!(
            validate_configuration(&configuration(address.into())).is_err(),
            "{address}"
        );
    }
}
#[test]
fn inventory_uses_only_explicit_get_and_exact_identity() {
    let (url, worker) = server(|stream, request| {
        assert!(request.starts_with("GET /api/tags HTTP/1.1\r\n"));
        assert!(!request.to_lowercase().contains("authorization:"));
        respond(stream,200,br#"{"models":[{"name":"owned-fixture:exact","model":"owned-fixture:exact","digest":"fixture-digest"}]}"#);
    });
    let found = inventory(&configuration(url), &AtomicBool::new(false)).unwrap();
    assert_eq!(found.name, "owned-fixture:exact");
    assert_eq!(found.digest.as_deref(), Some("fixture-digest"));
    worker.join().unwrap();
}
#[test]
fn inventory_rejects_missing_ambiguous_or_malformed_identities() {
    for (bytes, category) in [
        (r#"{"models":[{"name":"other"}]}"#, "missing-model"),
        (
            r#"{"models":[{"name":"x"},{"name":"x"}]}"#,
            "duplicate-model",
        ),
        (r#"{"models":[{"name":"x","model":"other"}]}"#, "inventory"),
        (r#"{"models":[{}]}"#, "inventory"),
        ("broken", "inventory"),
        (r#"{"models":[{"name":"e\u0301"}]}"#, "missing-model"),
    ] {
        assert_eq!(
            decode_inventory(
                bytes.as_bytes(),
                if bytes.contains("0301") { "é" } else { "x" }
            )
            .unwrap_err()
            .category,
            category
        );
    }
}
#[test]
fn generation_posts_native_bounded_options_and_retains_response() {
    let (url, worker) = server(|stream, request| {
        assert!(request.starts_with("POST /api/chat HTTP/1.1\r\n"));
        let body: serde_json::Value =
            serde_json::from_str(request.split_once("\r\n\r\n").unwrap().1).unwrap();
        assert_eq!(
            body,
            json!({"model":"owned-fixture:exact","stream":false,"messages":[{"role":"user","content":"Retained observation prompt"}],"options":{"num_predict":256,"temperature":0,"num_ctx":4096},"format":"json"})
        );
        respond(stream, 200, &serde_json::to_vec(&envelope()).unwrap());
    });
    let r = generate(
        &configuration(url),
        "Retained observation prompt",
        &AtomicBool::new(false),
    )
    .unwrap();
    assert!(r.complete);
    assert_eq!(r.text, r#"{"action":"WAIT"}"#);
    assert_eq!(r.token_count, Some(18));
    assert_eq!(r.stop_reason.as_deref(), Some("stop"));
    worker.join().unwrap();
}
#[test]
fn prose_requests_do_not_silently_add_json_or_context() {
    let mut config = configuration("http://localhost:1234".into());
    config.context_tokens = None;
    config.response_format = None;
    let body = generation_body(&config, "p", 256, Sampling::GREEDY);
    assert!(body.get("format").is_none());
    assert!(body["options"].get("num_ctx").is_none());
    assert_eq!(body["options"]["num_predict"], 256);
}
#[test]
fn incomplete_envelopes_remain_incomplete_without_losing_raw_text() {
    for (key, value) in [
        ("done", json!(false)),
        ("done_reason", json!("length")),
        ("eval_count", json!(-1)),
        ("eval_count", json!(257)),
    ] {
        let mut r = envelope();
        r[key] = value;
        let decoded =
            decode_generation(&serde_json::to_vec(&r).unwrap(), "owned-fixture:exact", 256)
                .unwrap();
        assert!(!decoded.complete);
        assert_eq!(decoded.text, r#"{"action":"WAIT"}"#);
    }
    let mut r = envelope();
    r.as_object_mut().unwrap().remove("model");
    r.as_object_mut().unwrap().remove("eval_count");
    assert!(
        decode_generation(&serde_json::to_vec(&r).unwrap(), "owned-fixture:exact", 256)
            .unwrap()
            .complete
    );
}
#[test]
fn malformed_envelopes_and_provider_substitution_fail() {
    assert_eq!(
        decode_generation(b"{}", "x", 256).unwrap_err().category,
        "response-json"
    );
    assert_eq!(
        decode_generation(&serde_json::to_vec(&envelope()).unwrap(), "other", 256)
            .unwrap_err()
            .category,
        "model-identity"
    );
}

fn response_with_prompt_evaluation(raw: &str) -> Vec<u8> {
    format!(r#"{{"done":true,"message":{{"content":"A complete retained journal."}},"model":"owned-fixture:exact","done_reason":"stop","eval_count":18,"prompt_eval_count":{raw}}}"#).into_bytes()
}

#[test]
fn optional_prompt_evaluation_preserves_integer_tokens_without_float_rounding() {
    use ProviderPromptEvaluation::{Reported, Unusable};
    use ProviderPromptEvaluationIssue as Issue;
    for (raw, expected) in [
        ("null", None),
        ("0", Some(Reported { count: 0 })),
        ("8193", Some(Reported { count: 8193 })),
        (
            "9007199254740993",
            Some(Reported {
                count: 9_007_199_254_740_993,
            }),
        ),
        ("18446744073709551615", Some(Reported { count: u64::MAX })),
        (
            "18446744073709551616",
            Some(Unusable {
                reason: Issue::OutOfRange,
            }),
        ),
        (
            "9999999999999999999999999999999999999999999",
            Some(Unusable {
                reason: Issue::OutOfRange,
            }),
        ),
        (
            "-1",
            Some(Unusable {
                reason: Issue::Negative,
            }),
        ),
        (
            "-0",
            Some(Unusable {
                reason: Issue::Negative,
            }),
        ),
        (
            "1.0",
            Some(Unusable {
                reason: Issue::NonInteger,
            }),
        ),
        (
            "9007199254740993.0",
            Some(Unusable {
                reason: Issue::NonInteger,
            }),
        ),
        (
            "1e999",
            Some(Unusable {
                reason: Issue::NonInteger,
            }),
        ),
        (
            "1e-999",
            Some(Unusable {
                reason: Issue::NonInteger,
            }),
        ),
        (
            r#""123""#,
            Some(Unusable {
                reason: Issue::WrongType,
            }),
        ),
        (
            "true",
            Some(Unusable {
                reason: Issue::WrongType,
            }),
        ),
        (
            "[]",
            Some(Unusable {
                reason: Issue::WrongType,
            }),
        ),
        (
            r#"{"n":1e999}"#,
            Some(Unusable {
                reason: Issue::WrongType,
            }),
        ),
    ] {
        let response = decode_generation(
            &response_with_prompt_evaluation(raw),
            "owned-fixture:exact",
            256,
        )
        .unwrap();
        assert_eq!(response.provider_prompt_evaluation, expected, "{raw}");
        assert!(
            response.complete,
            "optional metadata gated completion: {raw}"
        );
        assert_eq!(response.token_count, Some(18));
        assert_eq!(response.text, "A complete retained journal.");
    }
    let absent = decode_generation(
        &serde_json::to_vec(&envelope()).unwrap(),
        "owned-fixture:exact",
        256,
    )
    .unwrap();
    assert!(absent.provider_prompt_evaluation.is_none());
    assert!(serde_json::to_value(absent)
        .unwrap()
        .get("providerPromptEvaluation")
        .is_none());
}

#[test]
fn prompt_evaluation_duplicate_metadata_is_unusable_without_rejecting_complete_reply() {
    for fields in [
        r#""prompt_eval_count":1,"prompt_eval_count":2"#,
        r#""prompt_eval_count":null,"prompt_eval_count":null"#,
    ] {
        let bytes = format!(
            r#"{{"done":true,"message":{{"content":"Kept"}},"done_reason":"stop",{fields}}}"#
        );
        let r = decode_generation(bytes.as_bytes(), "owned-fixture:exact", 256).unwrap();
        assert!(r.complete);
        assert_eq!(
            r.provider_prompt_evaluation,
            Some(ProviderPromptEvaluation::Unusable {
                reason: ProviderPromptEvaluationIssue::DuplicateField
            })
        );
    }
}

#[test]
fn prompt_evaluation_malformed_json_and_existing_response_gates_remain_unchanged() {
    for raw in ["NaN", "01", "", "[1,]", "{broken}"] {
        assert_eq!(
            decode_generation(
                &response_with_prompt_evaluation(raw),
                "owned-fixture:exact",
                256
            )
            .unwrap_err()
            .category,
            "response-json"
        );
    }
    for raw in ["123", r#""malformed""#] {
        for (old, new) in [
            (r#""done":true"#, r#""done":false"#),
            (r#""done_reason":"stop""#, r#""done_reason":"length""#),
            (r#""eval_count":18"#, r#""eval_count":257"#),
        ] {
            let bytes = String::from_utf8(response_with_prompt_evaluation(raw))
                .unwrap()
                .replace(old, new);
            assert!(
                !decode_generation(bytes.as_bytes(), "owned-fixture:exact", 256)
                    .unwrap()
                    .complete
            );
        }
        assert_eq!(
            decode_generation(&response_with_prompt_evaluation(raw), "different", 256)
                .unwrap_err()
                .category,
            "model-identity"
        );
    }
}

#[test]
fn owned_http_prompt_evaluation_cases_preserve_evidence_and_completion_independently() {
    for (raw, complete) in [
        ("9007199254740993", true),
        ("null", true),
        (r#""unusable""#, true),
        ("18446744073709551616", true),
        ("321", false),
    ] {
        let mut body = response_with_prompt_evaluation(raw);
        if !complete {
            body = String::from_utf8(body)
                .unwrap()
                .replace(r#""done_reason":"stop""#, r#""done_reason":"length""#)
                .into_bytes();
        }
        let (url, worker) = server(move |stream, request| {
            assert!(request.starts_with("POST /api/chat HTTP/1.1\r\n"));
            respond(stream, 200, &body);
        });
        let response = generate_sustained(
            &configuration(url),
            "Explicit isolated fixture prompt",
            &AtomicBool::new(false),
            1024,
            180,
            Sampling::GREEDY,
        )
        .unwrap();
        worker.join().unwrap();
        assert_eq!(response.complete, complete);
        assert_eq!(
            response.provider_prompt_evaluation,
            prompt_evaluation_token(raw)
        );
    }
}
#[test]
fn redirects_are_not_followed_and_status_failures_are_retained() {
    let trap = TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    trap.set_nonblocking(true).unwrap();
    let address = trap.local_addr().unwrap();
    let (url, worker) = server(move |stream, _| {
        stream.write_all(format!("HTTP/1.1 302 Redirect\r\nLocation: http://{address}/api/tags\r\nContent-Length: 0\r\nConnection: close\r\n\r\n").as_bytes()).unwrap();
    });
    assert_eq!(
        inventory(&configuration(url), &AtomicBool::new(false))
            .unwrap_err()
            .category,
        "http-status"
    );
    worker.join().unwrap();
    assert_eq!(
        trap.accept().unwrap_err().kind(),
        std::io::ErrorKind::WouldBlock
    );
    let (url, worker) = server(|stream, _| respond(stream, 503, b"unavailable"));
    assert_eq!(
        inventory(&configuration(url), &AtomicBool::new(false))
            .unwrap_err()
            .category,
        "http-status"
    );
    worker.join().unwrap();
}
#[test]
fn declared_and_chunked_response_sizes_are_bounded() {
    let (url, worker) = server(|stream, _| {
        stream
            .write_all(
                format!(
                    "HTTP/1.1 200 OK\r\nContent-Length: {}\r\n\r\n",
                    MAXIMUM_BYTES + 1
                )
                .as_bytes(),
            )
            .unwrap();
    });
    assert_eq!(
        inventory(&configuration(url), &AtomicBool::new(false))
            .unwrap_err()
            .category,
        "response-size"
    );
    worker.join().unwrap();
    let (url, worker) = server(|stream, _| {
        stream
            .write_all(
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n",
            )
            .unwrap();
        let payload = vec![b' '; MAXIMUM_BYTES + 1];
        let _ = stream.write_all(format!("{:x}\r\n", payload.len()).as_bytes());
        let _ = stream.write_all(&payload);
        let _ = stream.write_all(b"\r\n0\r\n\r\n");
    });
    assert_eq!(
        inventory(&configuration(url), &AtomicBool::new(false))
            .unwrap_err()
            .category,
        "response-size"
    );
    worker.join().unwrap();
}
#[test]
fn exact_one_mib_is_accepted_before_decoding() {
    let mut body = br#"{"models":[{"name":"owned-fixture:exact"}]}"#.to_vec();
    body.resize(MAXIMUM_BYTES, b' ');
    let (url, worker) = server(move |stream, _| respond(stream, 200, &body));
    assert!(inventory(&configuration(url), &AtomicBool::new(false)).is_ok());
    worker.join().unwrap();
}
#[test]
fn stalled_headers_and_body_obey_total_deadline() {
    for headers in [false, true] {
        let (url, worker) = server(move |stream, _| {
            if headers {
                stream
                    .write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{")
                    .unwrap();
            }
            thread::sleep(Duration::from_millis(180));
        });
        assert_eq!(
            inventory_with_timeout(
                &configuration(url),
                &AtomicBool::new(false),
                Duration::from_millis(80)
            )
            .unwrap_err()
            .category,
            "timeout"
        );
        worker.join().unwrap();
    }
}
#[test]
fn cancellation_drops_inflight_request_and_late_reply_cannot_win() {
    let (seen_tx, seen_rx) = mpsc::channel();
    let (release_tx, release_rx) = mpsc::channel();
    let (url, worker) = server(move |stream, _| {
        seen_tx.send(()).unwrap();
        release_rx.recv_timeout(Duration::from_secs(3)).unwrap();
        let _ = stream.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\n{\"models\":[]}");
    });
    let cancelled = Arc::new(AtomicBool::new(false));
    let flag = cancelled.clone();
    let task = thread::spawn(move || inventory(&configuration(url), &flag));
    seen_rx.recv_timeout(Duration::from_secs(3)).unwrap();
    cancelled.store(true, Ordering::Release);
    let started = Instant::now();
    assert_eq!(task.join().unwrap().unwrap_err().category, "cancelled");
    assert!(started.elapsed() < Duration::from_secs(1));
    release_tx.send(()).unwrap();
    worker.join().unwrap();
}
#[test]
fn pre_cancelled_or_oversized_prompt_makes_no_connection() {
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    listener.set_nonblocking(true).unwrap();
    let config = configuration(format!("http://{}", listener.local_addr().unwrap()));
    assert_eq!(
        inventory(&config, &AtomicBool::new(true))
            .unwrap_err()
            .category,
        "cancelled"
    );
    assert_eq!(
        generate(
            &config,
            &"x".repeat(MAXIMUM_BYTES + 1),
            &AtomicBool::new(false)
        )
        .unwrap_err()
        .category,
        "prompt-size"
    );
    assert_eq!(
        listener.accept().unwrap_err().kind(),
        std::io::ErrorKind::WouldBlock
    );
}

#[test]
fn a_ready_decode_cannot_finish_after_the_total_deadline() {
    let result = bounded(&AtomicBool::new(false), Duration::from_millis(5), async {
        thread::sleep(Duration::from_millis(15));
        Ok(())
    });
    assert_eq!(result.unwrap_err().category, "timeout");
    assert_eq!(INVENTORY_TIMEOUT, Duration::from_secs(5));
    assert_eq!(GENERATION_TIMEOUT, Duration::from_secs(60));
}

#[test]
fn sustained_generation_posts_selected_budget_and_accepts_long_complete_prose() {
    let prose = "An unhurried passage can continue without a prescribed shape.\n\n".repeat(40);
    let expected = prose.clone();
    let (url, worker) = server(move |stream, request| {
        let body: serde_json::Value =
            serde_json::from_str(request.split_once("\r\n\r\n").unwrap().1).unwrap();
        assert_eq!(
            body,
            json!({"model":"owned-fixture:exact","stream":false,"messages":[{"role":"user","content":"Exact open journal prompt"}],"options":{"num_predict":1024,"temperature":0,"num_ctx":8192}})
        );
        let mut value = envelope();
        value["message"]["content"] = json!(prose);
        value["eval_count"] = json!(900);
        respond(stream, 200, &serde_json::to_vec(&value).unwrap());
    });
    let mut config = configuration(url);
    config.context_tokens = Some(8192);
    config.response_format = None;
    let response = generate_sustained(
        &config,
        "Exact open journal prompt",
        &AtomicBool::new(false),
        1024,
        180,
        Sampling::GREEDY,
    )
    .unwrap();
    assert!(response.complete);
    assert_eq!(response.text, expected);
    assert_eq!(response.token_count, Some(900));
    worker.join().unwrap();
}

#[test]
fn sustained_reported_tokens_are_not_clamped_and_cutoff_is_independent_of_budget() {
    for (tokens, stop, complete) in [
        (2048, "stop", true),
        (2049, "stop", false),
        (1024, "length", false),
    ] {
        let mut value = envelope();
        value["eval_count"] = json!(tokens);
        value["done_reason"] = json!(stop);
        let response = decode_generation(
            &serde_json::to_vec(&value).unwrap(),
            "owned-fixture:exact",
            2048,
        )
        .unwrap();
        assert_eq!(response.complete, complete);
        assert_eq!(response.token_count, Some(tokens));
    }
}

#[test]
fn sustained_invalid_budget_or_cancellation_never_connects() {
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    listener.set_nonblocking(true).unwrap();
    let mut config = configuration(format!("http://{}", listener.local_addr().unwrap()));
    for (tokens, deadline) in [(255, 180), (2049, 180), (1024, 59), (1024, 181)] {
        assert_eq!(
            generate_sustained(
                &config,
                "p",
                &AtomicBool::new(false),
                tokens,
                deadline,
                Sampling::GREEDY
            )
            .unwrap_err()
            .category,
            "configuration"
        );
    }
    config.context_tokens = Some(1024);
    assert_eq!(
        generate_sustained(
            &config,
            "p",
            &AtomicBool::new(false),
            1024,
            180,
            Sampling::GREEDY
        )
        .unwrap_err()
        .category,
        "configuration"
    );
    config.context_tokens = Some(8192);
    assert_eq!(
        generate_sustained(
            &config,
            "p",
            &AtomicBool::new(true),
            2048,
            180,
            Sampling::GREEDY
        )
        .unwrap_err()
        .category,
        "cancelled"
    );
    assert_eq!(
        listener.accept().unwrap_err().kind(),
        std::io::ErrorKind::WouldBlock
    );
}

#[test]
fn sustained_inflight_cancellation_and_total_deadline_remain_bounded() {
    let (seen_tx, seen_rx) = mpsc::channel();
    let (release_tx, release_rx) = mpsc::channel();
    let (url, worker) = server(move |stream, _| {
        seen_tx.send(()).unwrap();
        release_rx.recv_timeout(Duration::from_secs(3)).unwrap();
        let _ = stream.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}");
    });
    let flag = Arc::new(AtomicBool::new(false));
    let sent = flag.clone();
    let task = thread::spawn(move || {
        generate_sustained(&configuration(url), "p", &sent, 2048, 180, Sampling::GREEDY)
    });
    seen_rx.recv_timeout(Duration::from_secs(3)).unwrap();
    flag.store(true, Ordering::Release);
    assert_eq!(task.join().unwrap().unwrap_err().category, "cancelled");
    release_tx.send(()).unwrap();
    worker.join().unwrap();
    for partial_body in [false, true] {
        let (url, worker) = server(move |stream, _| {
            if partial_body {
                stream
                    .write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{")
                    .unwrap();
            }
            thread::sleep(Duration::from_millis(160));
        });
        assert_eq!(
            generate_with_limits(
                &configuration(url),
                "p",
                &AtomicBool::new(false),
                Duration::from_millis(60),
                1024,
                Sampling::GREEDY
            )
            .unwrap_err()
            .category,
            "timeout"
        );
        worker.join().unwrap();
    }
}

#[test]
fn sustained_route_keeps_one_mib_response_and_no_redirect_limits() {
    let (url, worker) = server(|stream, _| {
        stream
            .write_all(
                format!(
                    "HTTP/1.1 200 OK\r\nContent-Length: {}\r\n\r\n",
                    MAXIMUM_BYTES + 1
                )
                .as_bytes(),
            )
            .unwrap();
    });
    assert_eq!(
        generate_sustained(
            &configuration(url),
            "p",
            &AtomicBool::new(false),
            1024,
            180,
            Sampling::GREEDY
        )
        .unwrap_err()
        .category,
        "response-size"
    );
    worker.join().unwrap();
    let trap = TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    trap.set_nonblocking(true).unwrap();
    let address = trap.local_addr().unwrap();
    let (url, worker) = server(move |stream, _| {
        stream.write_all(format!("HTTP/1.1 302 Redirect\r\nLocation: http://{address}/api/chat\r\nContent-Length: 0\r\n\r\n").as_bytes()).unwrap();
    });
    assert_eq!(
        generate_sustained(
            &configuration(url),
            "p",
            &AtomicBool::new(false),
            1024,
            180,
            Sampling::GREEDY
        )
        .unwrap_err()
        .category,
        "http-status"
    );
    worker.join().unwrap();
    assert_eq!(
        trap.accept().unwrap_err().kind(),
        std::io::ErrorKind::WouldBlock
    );
}

// Slow on purpose: the production entry point must actually accept a request
// past the previous 60-second ceiling, not merely serialize the new setting.
#[test]
fn sustained_selected_deadline_accepts_owned_response_after_old_sixty_second_limit() {
    let (url, worker) = server(|stream, _| {
        thread::sleep(Duration::from_secs(61));
        respond(stream, 200, &serde_json::to_vec(&envelope()).unwrap());
    });
    let began = Instant::now();
    let response = generate_sustained(
        &configuration(url),
        "Owned delayed fixture only",
        &AtomicBool::new(false),
        1024,
        180,
        Sampling::GREEDY,
    )
    .unwrap();
    assert!(response.complete);
    assert!(began.elapsed() >= Duration::from_secs(60));
    worker.join().unwrap();
}
#[test]
fn sampled_requests_carry_temperature_and_seed_while_greedy_bodies_are_unchanged() {
    let config = configuration("http://localhost:1234".into());
    let greedy = generation_body(&config, "p", 1024, Sampling::GREEDY);
    assert_eq!(greedy["options"]["temperature"], json!(0));
    assert!(greedy["options"].get("seed").is_none());
    let sampled = generation_body(
        &config,
        "p",
        1024,
        Sampling {
            temperature: 0.7,
            seed: Some(42),
            system: None,
            thinking: None,
        },
    );
    assert_eq!(sampled["options"]["temperature"], json!(0.7));
    assert_eq!(sampled["options"]["seed"], json!(42));
    assert_eq!(sampled["options"]["num_predict"], json!(1024));
    assert_eq!(sampled["messages"], greedy["messages"]);
}

#[test]
fn a_standing_contract_is_sent_as_the_system_message_only_when_present() {
    let config = configuration("http://localhost:1234".into());
    let plain = generation_body(&config, "p", 1024, Sampling::GREEDY);
    assert_eq!(plain["messages"].as_array().unwrap().len(), 1);
    assert_eq!(plain["messages"][0]["role"], json!("user"));
    let contract = generation_body(
        &config,
        "p",
        1024,
        Sampling {
            temperature: 0.7,
            seed: Some(1),
            system: Some("You are a language agent."),
            thinking: None,
        },
    );
    let messages = contract["messages"].as_array().unwrap();
    assert_eq!(messages.len(), 2);
    assert_eq!(
        messages[0],
        json!({"role":"system","content":"You are a language agent."})
    );
    assert_eq!(messages[1], json!({"role":"user","content":"p"}));
}
#[test]
fn a_thinking_flag_is_sent_only_when_configured() {
    let config = configuration("http://localhost:1234".into());
    let as_built = generation_body(&config, "p", 1024, Sampling::GREEDY);
    assert!(as_built.get("think").is_none());
    for flag in [false, true] {
        let body = generation_body(
            &config,
            "p",
            1024,
            Sampling {
                temperature: 0.7,
                seed: Some(1),
                system: None,
                thinking: Some(flag),
            },
        );
        assert_eq!(body["think"], json!(flag));
        assert_eq!(body["messages"], as_built["messages"]);
        assert_eq!(body["options"]["num_predict"], json!(1024));
    }
}
#[test]
fn embedding_requests_and_replies_are_bounded_and_exact() {
    let body = embedding_body("nomic-embed-text", "An entry.");
    assert_eq!(
        body,
        json!({"model":"nomic-embed-text","input":["An entry."],"truncate":false})
    );
    let good = br#"{"model":"nomic-embed-text","embeddings":[[0.1,-0.2,0.3]]}"#;
    let receipt = decode_embedding(good, "nomic-embed-text").unwrap();
    assert_eq!(receipt.vector, vec![0.1, -0.2, 0.3]);
    assert_eq!(receipt.model, "nomic-embed-text");
    for bad in [
        br#"{"model":"other","embeddings":[[0.1]]}"#.as_slice(),
        br#"{"embeddings":[]}"#.as_slice(),
        br#"{"embeddings":[[0.1],[0.2]]}"#.as_slice(),
        br#"{"embeddings":[[]]}"#.as_slice(),
        br#"not json"#.as_slice(),
    ] {
        assert!(decode_embedding(bad, "nomic-embed-text").is_err());
    }
    let config = configuration("http://localhost:1234".into());
    assert!(
        embed(&config, "nomic-embed-text", "x", &AtomicBool::new(false), 1).is_err(),
        "no service listens; bounded failure"
    );
}
