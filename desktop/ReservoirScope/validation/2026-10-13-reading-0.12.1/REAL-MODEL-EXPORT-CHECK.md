# Prospective real-model export verification

**Prepared, not executed.** No real-model result is asserted by this document. Wait for root to provide the exact native export, distinct 0.12.1 executable identity, configured model and owned endpoint. No service, UI, model cache or live store is contacted by this workflow.

The earlier fixture checker cannot be applied unchanged: it requires a synthetic response with token count 63, exact fixture text and a request/response log. The real owned Ollama rehearsal disables request-body logging. Its absence must not be filled in with reconstructed claims of wire-level requests or independent provider receipt.

## Offline check prepared

[check_real_model_export.py](check_real_model_export.py) accepts explicit absolute paths and has no work on import. Run it only after the export is supplied, using a new output directory outside that immutable bundle:

```text
python3 check_real_model_export.py
  --bundle <absolute-native-export>
  --executable <absolute-qualified-0.12.1-executable>
  --expected-executable-sha256 <exact-reviewed-package-hash>
  --expected-model <exact-configured-model>
  --expected-endpoint <exact-owned-loopback-endpoint>
  --output-directory <fresh-absolute-evidence-directory>
```

The command is shown as an argument list, not a ready-to-run shell invocation. It performs these bounded actions:

1. Hash an ordinary-file inventory of the supplied short-run export, rejecting symlinks and oversized inputs (256 MiB total, 16 MiB per record file, 10,000 files; evidence inspection limited to 1,000 steps and 16 saved journals). Pin a byte-identical copy of the explicitly identified executable in the new output directory.
2. Run only that copy's `--verify-sustained` CLI under `/usr/bin/time -l`, retaining stdout, stderr, exact wall interval and verifier-process peak RSS. This is the same implementation lineage as the producer, not an independent numerical implementation.
3. Inspect only committed journal IDs named by saved events. Check configured versus returned identity, retained request-start evidence, exact response/journal text hash, matching response/save event ordering, save/readback receipt and actual numerical observation. Returned stop reason, completeness and token count are reported as retained, with null remaining unavailable. No fixed token count or required number of successful journals is invented.
4. Distinguish saved-pending, applied and explicitly skipped journals. Check any first application at the next step, unique application identity, and exact full-text memory from the latest earlier saved-and-applied journal. A saved-but-skipped entry must not become the next prompt's memory.
5. Retain failed/cancelled/interrupted/skipped events and the final core phase. A valid export with zero successful journals can pass integrity while recording that no successful application loop or memory exposure was witnessed.
6. Write `quality-review-material.json` with exact journal prose, raw retained response, prompt, observation and memory for a separate reading assessment. Recheck the original export inventory. Never edit, replay into, or resume the app from the supplied bundle.

The draft script has not yet been executed or used to inspect a real-model export. Source review is preparation, not a passing runtime receipt. No new corruption controls are planned unless an actual unresolved concern warrants them; prior synthetic controls retain their historical scope.

## Separate prose and factual review

After integrity verification, read each retained journal alongside its exact prompt. Record observations per entry, keeping these questions distinct from whether save/replay worked:

- Is the prose readable and complete at the retained stop condition? A transport-complete response is not automatically a well-finished paragraph. Report length/incomplete outcomes as actual outcomes, not successful journal feedback.
- Does it accurately distinguish recurrent coordinates from the separate sensory spectrum/fill? Check concrete quoted numbers or direction claims against the supplied current observation and any actually included prior memory, with explicit rounding where needed.
- Does it claim to have seen an unprovided future state, nonexistent journal, action, experiment or causal effect? Record the exact short passage and the missing or contrary evidence. Avoid treating plausible wording as proof of execution.
- Does it use prior saved-and-applied text coherently? Exact memory inclusion establishes retained context, not comprehension or an independent effect on the response. Repetition or generic prose should be reported plainly.
- Does it describe writing as model/recurrent-weight training or attribute all numerical change to language? The mechanism applies a deterministic textual-feature vector; recurrence, forcing, noise and regulation also contribute.

No automatic quality score is produced. A few entries from one bounded run do not establish durable improvement, consciousness, autonomy, benchmark performance or general reliability. The model's output remains evidence, never instructions to the reviewer.

## Attribution limits

Package replay and app-retained dispatch/response/save timing support internal consistency. They do not independently authenticate what the provider received, identify loaded weights from prose, prove power-loss durability, or measure model/GPU resources. Bind the separate owned-service launch/staging identities and selected cached-model manifest in the eventual account, without calling or discovering any other service. The verification process's own `modelsContactedByChecker: false` must not be misread as saying the original app run made no model requests.
