# Independent helper review · episode02

**Conclusion:** no concrete blocker found in the scoped source review. This is
not a launch, runtime-behavior, resource-admission or model-quality result.

Reviewed the episode02 [helper](owned_model.py) and [tests](test_owned_model.py)
against their frozen episode01 versions, together with the explicit
[software overlay](software-selection.json). Final reviewed SHA-256 identities:

| File | SHA-256 |
|---|---|
| `owned_model.py` | `415a585dfa4502e555331b4472cf08b6afbd3207944e6d02d952e133175f8c1b` |
| `test_owned_model.py` | `da68770ceed2999ef55d9a17149b244dde639bf21f0a5aa43e06aab73d57bb5d` |
| `software-selection.json` | `f86c9011ed33881ffae71679a3c96755c3d7d1cfbd434b0b9535a3493192a127` |
| `owned-helper-tests-02.json` | `18b73a3b4c180025dbfe18d30f7a38781e45db856ef0924d7bd53df7997b208f` |

The new launch arguments require an explicit overlay and independent SHA-256 pin.
The overlay binds the unchanged original model selection and exact stage-receipt
path/hash. It cannot change executable paths or the selected `serve` argv. It checks
new executable/plist sizes and digests, executable permission and both parsed plist
version fields. After potentially lengthy private-cache validation, it rechecks
software, overlay and stage identities immediately before `Popen`. Failures do not
fall back to the old version or select a different endpoint.

Read only the exact stage receipt named by the overlay, not cache blobs or key
contents. Its actual format is `reservoir-owned-model-stage-v1`; its 12,823 bytes
hash to `76cf4002d95bffcf6ef2665f728739e15ffb9aff1726dd8270510b50beeca3dc`, matching
the overlay. It binds the original model-selection SHA, retains staged software
0.40.3, six copied files (manifest plus five objects), three conventional metadata
entries and root identity. The new helper therefore accepts the actual retained
schema without rewriting its old software evidence.

The launch still validates every selected private-cache file before creating an
exclusive new worktree `target/qa` supervision directory. Environment filtering,
unchanged HOME, private `OLLAMA_MODELS`, ephemeral loopback listener, no pulls,
metadata-only conventional credential checks and the 1,200-second limit are
unchanged. Original process-group ownership, bounded logs, non-reaping child wait,
scoped cleanup and EOF handling are unchanged by this patch. The overlay does not
broaden those operations or authorize a default/shared endpoint.

[The final test receipt](owned-helper-tests-02.json) records 37 passing temporary-file
and mocked-operation tests with unchanged inputs. Coverage includes wrong/missing
pins; selection/stage/path/argv rebinding; executable and plist mismatch; size and
type bounds; replacement before spawn; and failure before cache validation,
directory creation or process creation. Existing cleanup mocks remain included.
[Run01](owned-helper-tests-01.json) is preserved: one test expected the wrong
exception class for a missing file; the correction changed the assertion only.
This reviewer ran no tests and performed no process, endpoint, UI, model, cache-copy
or resource-probe operation.

The checks are file identity checks, not proof of the behavior of every dynamically
loaded runtime component, an atomic lock against all post-check replacement, or
full-context processing. Runtime startup/cleanup observations and the new episode
still need their own evidence. The changed runtime also remains a comparison
confound under the [reading rubric](RUBRIC.md).
