# Owned activation worker protocol

Run the selected Python environment with `-B -m activation_worker` from the app
directory, or `-B /absolute/path/activation_worker/__main__.py`. `worker.py` is
also executable directly. The worker opens no socket and imports no sibling/live
Being code. Only `initialize` loads the explicitly selected local model. It does
not download assets. Standard output contains flushed JSON lines only; runtime
logs go to standard error.

Each request is one object with a unique `id` (1–128 ASCII letters, digits, `_`,
`.`, `:`, `-`) and `command`. Unknown fields, duplicate JSON keys, nonfinite values,
and repeated IDs are rejected. The limit is 8 MiB per line. A terminal response is
`{id, command, type:"result", result:{...}}` or
`{id, command, type:"error", error:{code,message}}`. No progress messages are
currently emitted. A malformed request with no trusted ID has `id:null`.
Every envelope, including errors, cancellation and shutdown, also carries
`protocolVersion` and `workerIdentity`: pinned model/revision, actual Python and
dependency versions, worker-source digest and the loaded model-manifest digest
(null before initialization). A structurally invalid request retains its valid
ID when one can be recovered unambiguously.

Commands:

- `inspect`: optional `modelPath`. Without it, reports protocol/architecture and
  initialization status without loading MLX. With it, independently hashes the
  owned model and verifies `model-provenance.json`, then returns `manifest`.
- `initialize`: required `modelPath`; optional `existingCalibration`. The local
  pinned Qwen3 assets must be accompanied by `{modelId,revision,files:[{path,sha256}]}`
  in `model-provenance.json`. All model/tokenizer assets must be covered. This
  receipt binds the steward-owned download; matching filenames alone do not
  establish a revision. Fresh initialization captures the 32 committed raw texts,
  returning `manifest`, `calibration`, `calibrationObservations`, `calibrationSource`,
  and EOS/special token IDs. A restored calibration must match the actual committed
  basis/texts and model/runtime manifest. Initialization happens once per child.
- `quiet_capture`: required `text`. A fresh raw prefill uses no template, steering,
  or sampling. Returns `activation[2560]`, `projection[32]`, `promptTokenIds`,
  `norms`, and `receipt`. Input is limited to 512 encoded tokens; it is never trimmed.
- `generate_journal`: required `prompt` and `steeringState[32]`; optional `gain`
  (`0` or `0.01`, default `0.01`), `arm` (receipt label), `maxTokens` (1–1024,
  default 1024), `seed` (u32, default 0), `temperature` (0–2, default 0.7).
  The worker applies the Qwen chat template with thinking disabled to the supplied
  open writing invitation and any quoted previous entry. Prompt cap: 8192 tokens,
  no truncation. Returns `text`, `complete`, `stopReason`, `promptTokenIds`,
  `generatedTokenIds` (content only), `sampledTokenIds` (including stop token),
  `stopTokenId`, `activation`, `projection`, `norms`, and `receipt`.
- `cancel`: required `targetId`. Marks that queued/running request cancelled.
  Returns `cancellationRequested`. The inference loop checks cancellation between
  native forward passes. The owner may terminate and wait for this one child to
  stop a blocked native call. Cancelling does not mutate another process.
- `shutdown`: cancels queued/running work, finishes its terminal response, then
  returns `{shutdown:true}` and exits. An EOF drains queued work and exits.

Calibration defines the exact frozen matrix `Q` as 2560 rows × 32 columns from the
committed little-endian Float32 `.npy` file. It was generated once with NumPy PCG64
seed 20261015, Gaussian entries, reduced QR and positive diagonal sign convention.
The saved matrix bytes, not regeneration on another runtime, define the basis.
`mean[32]` and `scales[32]` are the population statistics of the 32 raw projected
calibration captures; scales have a `1e-6` floor. The returned bounded input is
`tanh((Qᵀh - mean) / scales)`. Host projection arithmetic uses Float64; array
receipt hashes use canonical little-endian Float32 bytes. Calibration identity
hashes canonical sorted JSON excluding its own `sha256`.
Projection multiplication uses explicit Float64 NumPy `einsum(optimize=False)`
summation instead of a platform BLAS path; the pinned-runtime tests compare it with
an independently expressed column sum.

Capture is after block 18 (zero-based 17) before the added residual. Steering holds
the supplied reservoir/trace state for the entire writing pass. Nonzero `Qr` is
normalized, then its requested magnitude at each token is 1% of that token's own
pre-steer residual L2 norm. Actual Float16/BFloat16 addition is rounded: per-position
receipts distinguish requested and actual delta norms. Gain zero or state exactly
zero returns the original residual object without an add-zero operation.

Generation uses an owned serial loop, not an inference library's lookahead
generator. It prefills once, samples a content token, processes that token exactly
once, and samples the next token. EOS is sampled but never processed. Consequently
the final completed journal capture is the final generated content token from the
same pass, with no extra forward replay. No result receives feedback eligibility
unless nonempty content ended at a model EOS before cancellation/deadline. Empty EOS,
non-EOS special tokens, 1024-token exhaustion, a 180-second deadline, cancellation,
and inference errors return `complete:false` and `activation:null,projection:null`.
Every operation drops its cache. Capturing and restoring calibration are mechanics,
not evidence of useful continuity or a measurement of felt state.

`python -B -m unittest discover -s activation_worker/tests` exercises the fake
backend, math, manifest integrity and JSONL/cancellation protocol without loading
a model. After separate resource admission, the owner can explicitly run
`python -B -m activation_worker.qualify --model LOCAL_PATH --output NEW_DIRECTORY`.
It freezes its plan before loading one model, retains the actual 32 calibration
captures and calibration file, checks prefill and three incremental-token stages
against the uninstrumented block, and runs three short independent writing probes.
The fixed parity tolerance is `rtol=1e-5, atol=1e-5`; exact equality is also required
for the zero paths. Intended injection ratio is checked at absolute tolerance
`1e-7`. Actual rounded ratio uses the declared envelope
`u*gain + u*(1+gain+u*gain)` where `u` is half the residual dtype epsilon; for bf16
the allowance is approximately 0.003985 around the 0.01 target. This follows the
triangle bound for rounding the injected delta and then the residual sum, with
normal finite activations. The script does not retune or retry failed checks.
