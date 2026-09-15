# Actions lifecycle and independent verifier qualification

The production `ActionComparisonViewModel` is exercised on the main actor with a controlled monotonic clock, injected journal storage, fake language responses, asynchronous file loaders and record writers. The checks create no model requests or journal files. They cover paired cursors and differences, complete journal save → next-step feedback, actual memory reads, cancellation, late responses, source switching, pacing, replay and save failures.

Run from the research root:

```sh
native/ReservoirScope/check-actions-ui.sh
```

The script builds the shared library in temporary local storage by default. An existing library directory may be supplied as its first argument. `receipt.json` records the exact sources and shared library used for the retained `run.log`.

`VerifierMutationAudit.swift` independently constructs real small D/E comparisons, then changes only recorded evidence to probe three impossible histories: omitting the left manual journal, claiming right-side journal work after the left save failed, and claiming provider failure during fixed-tape replay. The final audit log should reject all three. Compile it against the same shared library to reproduce the audit:

```sh
xcrun swiftc -parse-as-library -swift-version 6 -I CORE_LIB -L CORE_LIB -lEssentialsCore -framework Accelerate VerifierMutationAudit.swift -o /tmp/actions-verifier-audit
/tmp/actions-verifier-audit
```

These checks qualify lifecycle mechanics and record consistency. They do not measure adaptive writing, memory benefit, or behavior of any live being.
