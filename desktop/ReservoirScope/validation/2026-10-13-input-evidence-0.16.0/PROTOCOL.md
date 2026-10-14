# 0.16 input-count evidence: prospective synthetic qualification

This is a functional check of optional provider-reported input counts, not a
language-model or writing-quality episode. No Being workspace or service is in
scope. The parent operator alone launches the fixture and app. This plan does not
authorize an automatic retry, real-model request, download, or default endpoint.

## Existing package preservation

[The preservation receipt](prior-package-preservation-01.json) compares every one
of the current 0.15 app's 46 files, its immutable archive and separately pinned
verifier with the preceding qualified identities. The archive remains
`ReservoirScopeTauriPreview-0.15.0-macos-arm64.tar.gz`, SHA-256
`b02018a34fb1d80a4801b9c070354071985dae977546cbee87aa7379cc31909c`.
The old pinned executable remains `target/qa/0.15-pinned/reservoir-scope-desktop`,
SHA-256 `18949732cf48c926003ffcf7b5b216bccc32ea071d0bff8a411e841eaba123d5`.
The parent confirms the old GUI is quit before a build replaces the working app
path. Historical archives, raw exports and qualification records are not replaced.

## Fixture and run

[owned_provider.py](owned_provider.py) adapts the bounded loopback pattern from
the retained 0.12 reliability fixture. It uses only the Python standard library,
binds a newly allocated `127.0.0.1` port, writes into one new `target/qa` directory,
and accepts the exact synthetic model name shown in `endpoint.json`. No models
are loaded or contacted. Generation responses follow the fixed sequence below;
there is no live control file that can change their content mid-episode.

From `desktop/ReservoirScope`, only after explicit launch authorization:

```sh
python3 -B validation/2026-10-13-input-evidence-0.16.0/owned_provider.py target/qa/0.16-input-evidence-provider-01 --lifetime-seconds 900
```

The parent directory `target/qa` must already exist. The output directory must be
new and must not resolve through a symlink. Startup prints the exact endpoint and
writes an identity file. The service stops when its own `stop-request` file exists
or its 900-second lifetime expires; a currently handled request may take at most
the five-second socket timeout to settle. No process group or unrelated service
is signalled. At most five accepted chat requests and 32 handled GET/POST requests
are allowed. The fixture does not retry a disconnected response or wrap its
sequence. Root creates the stop file after use and retains the terminal log.

Use exactly the configuration in [packaged-ui-plan-01.json](packaged-ui-plan-01.json):
new v4 sustained session, seed 20261013, 51 steps, five attempts, cadence 10,
one-second pacing, 180-second session duration, 32 MiB, context 8192, output 1024,
request deadline 180 seconds. Fill/state settings retain the normal defaults.
Readiness uses one explicit inventory request to this fixture only. Create itself
must not send a generation request. Start is explicit.

| Attempt / observed step | Raw optional field | Complete? | Expected retained result |
| --- | --- | --- | --- |
| 1 / 10 | `9007199254740993` | Yes | Reported count displayed exactly, saved and first applied at 11 |
| 2 / 20 | Field absent | Yes | Not retained/unknown, saved and first applied at 21 |
| 3 / 30 | String `"2450"` | Yes | Unusable `wrongType`, saved and first applied at 31 |
| 4 / 40 | `18446744073709551615` | Yes | Reported maximum u64 displayed exactly, saved and first applied at 41 |
| 5 / 50 | `321` | No, `done=false` / `length` | Count cannot make the response complete; blocked, no fifth journal or application |

These intentionally implausible counts test representation and missingness. The
app must not compare them with prompt bytes, requested context, or output counts
to decide scientific acceptance or save eligibility. Decimal strings at the IPC
boundary must preserve both wide integers. All prose is clearly labelled synthetic
test material. No full-context, tokenizer, comprehension, or accuracy claim follows.

## Native checks and receipts

Before Start, retain accepted configuration, endpoint identity, app executable
hash and request log baseline. Inspect each saved entry's Evidence disclosure;
the count must remain attached to that entry when live state advances or another
entry is selected. Missing and malformed metadata must leave the full prose,
prompt, memory, save and application evidence available. There is no requirement
to add these bookkeeping values above the journal prose or to the prompt.

At the held fifth response, retain the phase and inspectable failure evidence.
Four journals/feedback applications remain accepted; the incomplete fifth must
not become a journal or eligible feedback. Export a snapshot using the native
folder dialog, then use the exact new pinned packaged CLI for offline verification.
Any explicit Stop or Skip needed for terminal cleanup is separately recorded and
must not resume numerical progress or dispatch another request. No automatic retry.

Compare fixture request hashes with retained prompts/response cases where the
formats permit an exact join; socket-write success is not itself app acceptance.
Preserve exact exported bytes and the fixture's endpoint, log and response files.
Optionally clean-quit/relaunch and explicitly restore for read-only evidence
inspection; no automatic reconnection or additional generation. This is not a
crash, power-loss, minimized-duration, GPU or all-platform qualification.

## Source, compatibility and package evidence

The [fixture test receipt](fixture-tests-01.json) records seven pure tests of the
sequence, exact integer lexemes, incomplete case, configuration and bounds. It
does not claim the HTTP server or native UI has been executed. Production tests
should additionally cover null, zero, negative, fractional/exponent, duplicate,
wrong-type and out-of-range optional fields; legacy omission; full-width IPC;
and unchanged completion/save gates. Their owners record exact executed counts.

Use `scripts/qualification_receipt.py` for source/package inventories and observed
signing status. Its receipt alone does not prove a binary was built from captured
sources: bind a source inventory before the actual SDK-bound build and compare it
afterward, retaining the exact command and exit status. Caller-supplied test results
remain labelled as such. Capture package identity before UI, create a new exclusive
0.16 archive, verify its contents/resources, and retain separate after-UI continuity.
Do not rerun unrelated tests merely to obtain a new date or copy prior results into
new execution claims.

The new pinned verifier must accept preserved old v1/v3/v4 bundles unchanged.
Old records with omitted evidence remain omitted when serialized and hash-bound.
A narrow new bundle with retained optional evidence should be checked against the
old pinned reader. Record its actual behavior: an old reader might ignore unknown
fields and therefore cannot qualify their consistency, even when its earlier
numerical checks pass. Do not rewrite new records to make that reader accept them.
An expected new-reader rejection of tampered evidence is distinct from historical
record validity. No new public release, notarization or platform acceptance follows.
