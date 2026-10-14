# Reviewed-case conformance

`research-cases-v1` validates one to twenty reviewed cases. Each case retains its
question, ownership, interval, limits, bounded materials, claims and event sequence.
The core checks exact embedded UTF-8 SHA-256 hashes, recognized interpretation and
observation labels, unique IDs, exactly one quotation occurrence, and internal
references. It never follows `sourcePath` or treats an authored interpretation as a
numerical or scientific verification result.

Swift string equality is canonically equivalent. IDs and quotation comparisons
therefore use an NFC comparison view while original strings and original file bytes
remain unchanged. Quotation matching respects extended grapheme boundaries and
non-overlap, including CRLF, combining marks, emoji modifiers/ZWJ and flag sequences.
Foundation whitespace includes U+200B, which Rust's ordinary trim does not include.
Dependencies are pinned: [unicode-normalization 0.1.25](https://docs.rs/unicode-normalization/0.1.25/unicode_normalization/)
and [unicode-segmentation 1.13.3](https://docs.rs/unicode-segmentation/1.13.3/unicode_segmentation/).

Run `scripts/check_case_conformance.py --output NEW_RECEIPT.json` on macOS to
compile the unchanged native `ResearchCase.swift` into a temporary harness and
compare the canonical catalog plus positive/negative variants with the Rust CLI.
A finite conformance corpus does not establish exhaustive Unicode-version parity.

The desktop keeps bounded, temporary catalog handles. A rejected replacement or
cancelled operation preserves the accepted reading; responses echo request and
catalog identities. Text is rendered inertly. Navigation preserves the current
question and expanded material. Opening never imports into the Library or creates
a watcher. Two explicit export actions are available:

- **Export selected case** constructs a new `research-cases-v1` catalog containing
  exactly the selected case. It retains every material, including uncited context,
  exact embedded text and its SHA-256, recorded `sourcePath` and `sourceSHA256`,
  notes, claims and references, the complete event sequence, ownership and limits.
- **Export original case catalog** writes the entire accepted catalog's exact
  original bytes, including original formatting and fields the typed reader does
  not recognize. It remains independent of the derivative action.

The derivative follows native `ResearchCaseCatalog(cases: [item]).encoded()`.
Rust verifies the selected case again, serializes pretty JSON with sorted keys,
omits absent optional fields as Swift does, and bounds the encoded result to
32 MiB. It never constructs content in JavaScript or follows a historical path.
Unknown fields are omitted by the typed derivative, matching Swift Codable; no
new parent-catalog provenance or interpretation is invented. The original file's
SHA-256 remains in the reading and is echoed in the export response, separately
from the derivative file's own SHA-256. JSON formatting need not be byte-identical
between Swift and Rust; interoperability and retained case values are the contract.

The desktop command `export_selected_case` accepts only the accepted catalog
handle, selected index and exact case ID, plus a request ID. It resolves and verifies
that immutable selection before showing a native save dialog, then uses the same
atomic export helper and bundled-resource protection as original export. The
suggested filename follows native ASCII filtering, with a 120-character basename
cap and `reviewed-research-case` fallback. The complete case ID remains unchanged
inside the derivative. Cancellation, invalid identity, failed construction or a
write error leaves the accepted catalog and reading intact. Request/selection
generations prevent late success or failure messages from replacing a newer reading.

Run `scripts/check_case_export_conformance.py --output NEW_RECEIPT.json` on macOS
to compare selected derivatives produced with unchanged native `ResearchCase.swift`
and the Rust core. The temporary native harness uses the exact construction in
`ResearchCaseView.swift`; it does not modify native sources. Each successful row
compares decoded exported objects, requires exactly the requested case, and opens
each implementation's output in the other. The corpus covers both bundled cases,
multiple synthetic selections, complete uncited material, inert unsafe text,
Unicode IDs, optional metadata, unknown fields and rejected evidence/selections.
Original input bytes are checked unchanged, and rejected rows must not create output.

The 0.5 focused implementation checks passed: 9 core case tests, 3 desktop case
tests, 16 frontend tests, and 10 independent Swift/Rust export oracle rows.
The new execution receipt is `target/qa/selected-case-export-0.5-01.json`.
These are source-level and offline filesystem results. Packaged native-dialog,
permission, human usability, and Windows/Linux qualification remain pending until
recorded separately by the release owner; older receipts remain historical evidence.
