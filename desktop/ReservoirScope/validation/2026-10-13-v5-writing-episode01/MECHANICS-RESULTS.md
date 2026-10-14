# Completed first v5 real-model episode

The [frozen plan](run-plan.json) ran once on the unchanged 0.17.0 macOS package.
The [preparation audit](PREPARATION-AUDIT.md) binds all 21 frozen inputs, all 46
package files, the archive, pinned executable and exact accepted configuration.
No application source changed and no package was rebuilt for this episode.

The single admission passed with normal pressure level 1, 52% reported free memory
and 11,902,164,992 free disk bytes. This is a prelaunch admission, not a resource
benchmark. The recorded native Start witnesses retain 1,150.952 and 1,150.861
seconds of the owned service lifetime, exceeding the prospective 1,140-second
requirement. The preceding monotonic check also passed. These operator-recorded
witnesses are not authenticated OS input timestamps.

Session `sustained-1791942995555-1`, generation 1, used the explicit owned endpoint
`http://127.0.0.1:60782`, exact cached `gemma3:4b` identity, seed 20261013 and
`reservoir-journal-v5`. Twelve opportunities at steps 30–360 yielded twelve
complete `stop` replies, saved/read-back journals and applications at steps 31–361.
All eleven later prompts contained the exact latest eligible full journal.
No retry, skip, replacement, incomplete reply, failure or limit extension occurred.

The [original export receipt](real-model-export-01/receipt.json) passes exact
0.17.0 production replay and the frozen v5 checker. It records all twelve slots
as reached, dispatched, received, complete, saved and applied. The original
revision 423 bundle contains 73 files and 59 segments, totals 6,304,053 bytes, and
ends at step 361 after 653,082 ms retained active time. The step and attempt limits
were reached; the 900-second duration and 64 MiB storage limits were not reached.
This is one dependent sequence, not a multi-hour test.

All responses retained optional provider input counts. They are provider assertions,
not evidence of complete attention or accurate prose. Output counts were 276–849
within the 1,024-token ceiling. No token/character ratio or quality score is used.
The offline prose helper produced a candidate inventory; complete contextual
reading is recorded separately in [the prose review](PROSE-REVIEW.md).

## Native workflow and recovery

The previous synthetic session was already exported and paused. Native Command-Q
closed it; app inventory confirmed absence before a fresh launch. The next form
was prepared before admission, with the endpoint blank. After owned launch, the
app made one explicit identity check, created local state, displayed the exact
accepted configuration, then started via its native button. No navigation began
generation. [Running configuration](ui-running-config-01.txt).

The final UI showed twelve journals, step 361, and Run budget reached. Export used
the actual macOS chooser into a new owned parent directory. Go to Folder and Return
worked, without user intervention. The app then confirmed the immutable export.
[Original export UI](ui-original-export-01.txt).

After owned model shutdown, native Command-Q and an absent-app observation preceded
relaunch. Navigation returned to idle setup; the recovery catalog required an
explicit read and verification. Inspect reported step 361, twelve journals and
59 segments. Restore paused changed the wrapper generation and left Resume
disabled at the exhausted step/attempt bounds. A second native export produced
revision 424. [Recovery](RECOVERY-RESULTS.md) confirms all 72 nonmanifest files
byte-identical, with only generation, revision and wrapper phase changed.

The app remains paused for reading, with Evidence, numerical details and recovery
collapsed. [Recovered reader](ui-recovered-reading-01.png).

## Owned service shutdown

The [supervision receipt](owned-run-01/supervision-result.json) records PID/PGID 9866,
one inventory GET and twelve generation POSTs in the owned log, followed by an
explicit stop at 747.302220 seconds within the original 1,200-second limit.
Only the owned group received TERM; no KILL was needed. Quiescence was verified
before leader reap and the child exited zero. Transient identity reads during
exit remain in the receipt. Conventional key/config metadata stayed unchanged;
no credential contents were read. The helper does not claim to inventory escaped
descendants. The exact final owned files are copied in [the evidence inventory](owned-evidence-copy-01.json).

Service lifetime includes readiness and idle time and differs from session active
time. Neither measures GPU efficiency, energy use, physical power-loss durability,
sleep behavior or long-duration reliability. Windows/Linux and earlier qualification
retain their existing scope. Minime and Astrid's systems were untouched.
