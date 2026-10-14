# Admission helper · read-only review

Reviewed [admit_once.py](admit_once.py) against [run-plan.json](run-plan.json)
without importing it or executing probes. The exclusive `host-admission-01.json`
creation precedes frozen-file reads and all probes. An existing receipt, including
an empty or partial one after failure, prevents another sample. There is no retry
or polling loop.

Admission requires every command to exit successfully, pressure level **1**, free
memory **at least 35%**, and disk free space **at least 8,589,934,592 bytes**
(8 GiB). Missing or unparseable pressure/free values cannot admit. Probe errors
are recorded; earlier exceptions terminate without admission. These thresholds
match the prospective plan.

The only subprocesses are two read-only `sysctl` queries and `memory_pressure`,
each bounded by a ten-second timeout. Disk usage is read locally. No service,
endpoint, model, Being workspace or process-control action is invoked.

The initial review caught optimization-sensitive `assert` hash checks. The
reviewed correction raises `ValueError` explicitly on mismatch, before probes;
Python optimization cannot bypass that check. No remaining blocker was found in
this scope. This is source review, not an executed admission or evidence that the
host meets the thresholds.
