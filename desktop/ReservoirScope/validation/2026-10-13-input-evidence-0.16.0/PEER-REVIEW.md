# Independent source review: optional input-count evidence

The source review found no remaining concrete blocker in the frozen core,
transport, sustained-store and frontend changes identified by
[peer-review-01.json](peer-review-01.json). This is a source review; the separately
recorded automated suites, packaged UI and exported-bundle probes own their
execution claims.

- Missing/null metadata remains omitted in typed serialization. Existing prompt,
  codec, completeness, journal-save and next-step application predicates do not
  consume this evidence. Reported zero remains distinct from absence.
- The transport reads the optional field's raw JSON token. It preserves full u64
  integers and classifies unusable optional values without rejecting otherwise
  complete prose. Invalid JSON and existing response-envelope failures still fail.
  Duplicate fields become an explicit unusable diagnostic.
- Saved candidates and response events carry the same typed evidence; current
  replay compares retained consistency. A self-consistent external assertion is
  still a replay input, not independently authenticated tokenization.
- Journal IPC and checkpoint inspection project reported counts into decimal
  strings. The new recovery view derives at most 50 metadata rows from verified
  response events, with total/truncation status and no response-body history.
- Review identified a new recovery-output-count precision edge: an incomplete
  reply can retain an i64 value beyond JavaScript's safe range. The final projection
  uses exact signed decimal strings. The independently requested 256-character
  stop-reason preview also carries explicit truncation; portable originals remain
  unchanged. Core already bounded retained stop reasons to 4096 bytes.
- Frontend evidence remains in a selected journal's closed disclosure and uses
  that session's immutable requested context setting. Recovery uses the inspected
  manifest's setting and labels received responses separately from saved journals.
  None of these displays creates a save gate or initiates a provider operation.

The pinned 0.15 reader's acceptance of the new optional field does not qualify it:
the retained old-reader probe shows unknown metadata can be ignored. The current
contract therefore requires a 0.16-aware reader for field schema and event/journal
consistency checks. New-reader rejection of the two reanchored negative probes and
acceptance of preserved historical bundles are separately qualified after the new
package is built.

The owned fixture was also read by the backend owner without a concrete finding.
Its seven pure tests do not establish native HTTP/UI execution. No real model,
Being system, app action or service call was performed as part of this review.
