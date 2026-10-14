# Independent prospective review

2026-10-14 UTC, before admission or model output. No remaining concrete blocker
was found in the scoped plan, admission, supervisor reuse and offline-checker
review. This note is not an admission result or permission to substitute a new
episode after refusal.

The [run plan](run-plan.json) fixes v5 on the existing 0.17.0 executable
`7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081`,
Gemma3:4b, seed 20261013, cadence 30, 361 steps, twelve attempts, 900 active
seconds, 64 MiB, output 1024, deadline 180 seconds and requested context 8192.
The first bound or failed/incomplete outcome can leave slots unstarted; no Retry,
Skip, replacement or extension is permitted. These are one dependent sequence,
not twelve independent trials. The [rubric](RUBRIC.md) separates optional compact
readings actually supplied from full retained human evidence, and eligible prose
memory from the preceding reached observation.

`admit_once.py` creates its receipt exclusively **before** any probes and checks
every frozen file hash with an explicit exception on mismatch. Its only change
from the prior qualified source is the episode ID. It requires all passive probe
commands to succeed, pressure level **1**, reported free memory **at least 35%**,
and free disk **at least 8,589,934,592 bytes**. Missing/error evidence refuses
admission; an existing or partial receipt prevents another invocation. I did not
execute any probes or inspect processes.

The copied supervisor and tests match the prior files byte for byte: helper SHA
`9c5351878ff5ee634f8f6c3afa49f0e9c6e5108224073a7b8ebda14d0d35ae9f`,
test SHA `145d75ad5d1d8a090bb3c1a9830a59d1127d3424354b8b59db208d0006da9b87`.
The launch path revalidates selected executable/private model hashes, uses a new
exclusive owned directory/group, preserves HOME, and checks conventional
key/config metadata without reading their contents. The listener comes from the
owned process; there is no default endpoint or download. Cleanup retains the
leader until original-group quiescence is checked; escaped descendants remain
outside that stated scope. The 1,200-second supervisor ceiling and **at least
1,140 seconds remaining before Start** account for 900 active + 180 in-flight +
60 margin. The root must retain its monotonic check and both actual Start-click
UTC endpoints; this review does not establish their future execution.

The v5 integrity checker keeps twelve slots and incomplete response text,
requires pinned whole-chain replay, and binds exact JSON-decoded full memory
without requiring its hash in the compact prompt. Its scaffold-only omissions
do not censor words inside historical prose. Numerical rendering remains the
production replay's responsibility. The owner's
[checker-tests-01.json](checker-tests-01.json) records **31 passing tests**;
I read the source and receipt without rerunning that suite.

One pre-freeze mismatch was resolved: the global prose extractor accepted only
v1–v4. The episode now owns local `journal_quality.py` and
`test_journal_quality.py` copies. V5 is accepted with the same partial extraction
rules and no required metric, heading or length. Global/historical sources remain
unchanged. I executed **47 passing tests**, including four new v5 tests, in
[quality-helper-tests-01.json](quality-helper-tests-01.json), at
01:54:59.668012–01:55:00.327174 UTC:

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B -m unittest -v test_journal_quality.py
```

The command ran from this episode directory. It exercised synthetic/temporary
Python fixtures and preserved known historical regressions, not new model writing.
Input counts remain provider assertions, and retained values used for claim review
are not automatically model exposure. The helper assigns no scientific or
creative-quality verdict.

The final freeze script includes these local quality sources/receipt, the
integrity-checker freeze, this review, rubric, plan, admission/helper provenance and
v5 fixtures. Freeze must precede the one admission; subsequent outcomes append
without rewriting these inputs. No app, model, endpoint, service, or Being action
was performed by this review. Actual delivery, cleanup and all-text reading remain
pending execution.
