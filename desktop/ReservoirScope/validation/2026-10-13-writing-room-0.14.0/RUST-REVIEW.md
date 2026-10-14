# Independent source readback

A separate agent reviewed the writing-budget changes read-only before packaging; the parent also inspected the core configuration, transport body/decoding, backend configuration and worker interfaces. No actionable blocker was identified. This is code review, separate from executed tests and actual provider observations.

Reviewed contracts:

- Serde missing defaults and skip-serialization rules preserve old 256/60 typed bytes. New Rust defaults use 1024/180 explicitly.
- Core validation bounds output and deadline, delegates language/context range checks, and requires explicit context to exceed output.
- Retained pending requests and replay compare budgets against the session specification. The worker forwards those values to sustained transport.
- Sustained transport sets `num_predict` and both request/overall deadlines from the retained policy. Finite generation continues through its 256-token/60-second path.
- A `length` stop, incomplete response, or reported count outside the selected output bound cannot become eligible feedback. Missing count retains the existing contract; this change does not invent provider usage evidence.
- Size, cancellation, loopback selection, model identity and no-redirect boundaries remain intact.

Full automated receipts, exact build identities and the new owned-service run establish separate scopes. Review does not prove absence of all defects or authenticate provider processing.
