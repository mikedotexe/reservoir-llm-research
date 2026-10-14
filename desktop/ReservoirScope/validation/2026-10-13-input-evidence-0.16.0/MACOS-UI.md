# Native macOS check · 0.16.0 r2

Executed October 13, 2026 on this Apple-silicon host using the actual packaged app
and native folder dialogs. These are agent UI observations, separate from human
acceptance, headless replay and real-model writing quality.

The first candidate showed a hardcoded 0.15 header despite a 0.16 package identity.
[The finding](candidate01-ui-finding.json) was retained. Its archive and pinned
verifier remain intact. The replacement imports the package version into the
header; [build 02](package-build-02.json) binds unchanged build inputs and
[archive 02](archive-check-02.json) binds exact read-back contents.

Qualified executable: `73872388b56d2483054497aa8513e3659f79dfaf255699d6bca29041cafd258d`.
Archive: `ReservoirScopeTauriPreview-0.16.0-r2-macos-arm64.tar.gz`, SHA-256
`8c3ddbca021e381ecd39c6aadd8cad5ecc47fb1070857acb92a0f51138395d5e`.
[Package identity](qualification-before-ui-02.json) records 46 files and observed
local ad-hoc signature verification; it establishes no notarization or public release.

## Five-response run

The [frozen plan](packaged-ui-plan-01.json) was executed with the owned fixture at
`http://127.0.0.1:55860`, exact synthetic model
`reservoir-fixture:input-evidence-0.16`. The [pre-start receipt](before-start-01.json)
records one explicit inventory request and no generation from setup or Create.
The [accepted setup](ui-r2-before-start.txt) matches seed 20261013, v4, cadence 10,
51 steps, five attempts, three-minute active duration, 32 MiB, one-second pace,
8192 requested context and 1024 output tokens. Start was explicit.

Session `sustained-1791934324379-1`, generation 1, revision 76, reached step 50
and held the incomplete fifth response. Retained active duration is **51.705
seconds**, not the fixture service lifetime or a minimized/multi-hour measurement.

| Writing step | Native evidence | Save/application |
| --- | --- | --- |
| 10 | `9007199254740993 tokens`, exactly | Saved; first applied at 11 |
| 20 | `Not retained` | Saved; first applied at 21 |
| 30 | `Unavailable · the returned value had the wrong type` | Saved; first applied at 31 |
| 40 | `18446744073709551615 tokens`, exactly | Saved; first applied at 41 |
| 50 | Received-response inspection shows count 321, completeness false, stop reason length | No fifth journal or application |

The first journal was selected while numerical work continued; its entry-bound
evidence stayed selected. Switching entries exposed their own counts without
carrying values between them. [Wide-count observation](ui-r2-wide-count-during-run.txt),
[absence and held response](ui-r2-absent-count-and-blocked-fifth.txt),
[unusable count](ui-r2-unusable-count-saved.txt), and the
[maximum-count screenshot](ui-r2-maximum-count.png) retain the observations.
Some intermediate AX receipts are incremental diffs; the full observations below
are explicitly named `full`.

## Export and offline recovery

Native export published `sustained-1791934324379-1-1-76`: 28 files, 1,742,891 bytes,
four journals and 22 segments. Its manifest SHA-256 is
`8b0c90a18b3b8c367f4788885f693bf6154e6f10d34e5e7a1e62612a452da61b`.
The [full export observation](ui-r2-original-export-full.txt) includes the export
receipt and five retained response summaries. No Skip, Stop, retry or budget
extension was used to obtain the export.

The app quit cleanly: [running-state observation](ui-r2-clean-quit.json).
The fixture then stopped through its own stop file, with shell exit zero.
[Retained fixture outputs](fixture-run-01/retention.json) bind one inventory request,
five accepted generation requests, five completed writes, zero rejected requests
and explicit shutdown after 507.373108 seconds. This is an owned synthetic HTTP
service lifetime, not LLM generation time or app resource measurement.

Relaunch with the provider stopped showed [idle setup](ui-r2-relaunch-idle.txt).
Explicit catalog inspection and replay preceded **Restore paused for review**.
Generation 2/revision 77 stayed at step 50 with four journals and five attempts;
Resume was disabled. The [restored evidence](ui-r2-restored-evidence-full.txt)
retains both wide counts, absence, unusability and the incomplete fifth response.
No provider was started or reconnected.

A second native export published `sustained-1791934324379-1-2-77` separately.
[Independent comparison](recovered-export-equality-01.json) found 27 of 28 files
byte-identical, including all journals, segments and the exact checkpoint. Only
manifest generation, revision and wrapper phase changed. Both original and recovered
exports passed the exact r2 verifier and independent fixture joins;
[original results](NATIVE-EXPORT-RESULTS.md) and
[recovered results](recovered-export-evidence-01.json) own those checks.

The app is left paused, reading the fourth synthetic entry, with technical
disclosures closed: [final screenshot](ui-r2-final-reading.png) and
[full state](ui-r2-final-state.txt). No fixture process remains intentionally running.

## Limits

No real LLM, Being service or producer was contacted. These fixed replies test
transport/storage/UI behavior; they establish no prose accuracy or emergence.
This was a clean relaunch, not crash/power-loss recovery. No new minimized duration,
GPU/energy, minimum-macOS, Windows/Linux or broad accessibility claim follows.
