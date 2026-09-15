# Verification

The Swift package suite exercises both mechanism equations and runtime evidence:

```sh
swift test --package-path essentials --scratch-path /tmp/reservoir-essentials-runtime-build
```

`ActionComparisonTests.swift` adds 19 checks for the A–H ladder, exact paired
inputs and state, independent memory-sensitive fixtures, journal save/readback,
manual and scheduled opportunities, wait behavior, incomplete output, failure,
timeout, cancellation and late-response rejection, and impossible-history rejection.
The [0.11.0 core receipt](../../native/ReservoirScope/validation/0.11.0/core-tests.json)
retains the full 51-test suite and source identity.

Two additional scripts exercise the packaged runner:

```sh
python3 essentials/tests/action_cli_smoke.py --cli /absolute/path/to/essentials-run --output action-cli.json
python3 essentials/tests/action_http_smoke.py --cli /absolute/path/to/essentials-run --output action-http.json
```

The first runs eight 91-step versions and rejects twelve altered exports. The
second checks five real HTTP transport cases on newly owned ephemeral loopback
ports, including exact saved-memory delivery in a second request. It does not
contact a model. Native action lifecycle, paired layout, presented inspector and
camera checks are retained separately under `native/ReservoirScope/validation/0.11.0/`.

`MechanismTests.swift` covers hand-calculated recurrence, bias/leak/noise ordering,
seeded weight bounds, covariance/eigenvector equations, codec mapping, fill denominator,
controller direction/deadband/slew/anti-windup, same-input paired regulation, and
rank-one/zero-input cases that cannot reach the target. Its retained scalar
[qualification](../examples/regulation-qualification.json) describes synthetic
reduced-model behavior only.

`RuntimeTests.swift` covers all four stages and measurement availability, recipe
bounds, deterministic noise, the exact prompt/reply/features/application chain,
frozen simulated time, stopped/failed replay, timeout, cancellation, ignored late
responses, and a Stop arriving during the asynchronous waiting-status update.
Provider metadata tests retain returned model, stop reason and token counts, reject
partial/length/over-limit output, and accept a reported stop at exactly 256 tokens.
No actual model endpoint is contacted. Corruption tests alter dimensions, states,
time, covariance, prompts, codec vectors and feedback step references.

The paired runtime runs share synthetic forcing, noise and scripted replies; their
spectral-dependent semantic shaping can differ. The separate mechanism test holds
all actual inputs constant while changing retention control.

[Original stage suite log](runtime-validation.log) and
[runtime verification receipt](../examples/runtime-verification.json) retain the
checked source identity, 22-test result and four independently reopened/verified
300-step example runs (1,200 steps and 27 text turns in total). Rendering and viewer
lifecycle checks belong to the native application test suite.

The native checks include `check-essentials-ui.sh` (17 lifecycle cases),
`check-essentials-layout.sh` (40 changing regulation frames at two window sizes),
and `check-essentials-run-layout.sh` (an actual 300-step run and timed Stop under
the AppKit event loop). Their retained receipts match the packaged viewer sources
and shared core. Offscreen hosting timings do not measure presented frame rate.

`http_smoke.py` starts its own temporary server on a fresh loopback port for
each of five transport cases. It checks the actual chat request, successful
next-step feedback, retained incomplete/length responses, HTTP errors and
redirect rejection, then independently verifies every saved run. It does not
contact an existing Ollama server or language model.

```sh
python3 essentials/tests/http_smoke.py --cli /absolute/path/to/essentials-run \
  --output native/ReservoirScope/validation/0.8.0/http-smoke.json
```
