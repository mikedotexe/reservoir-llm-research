# Hold Shelf records

The October 6 full-backlog reconciliation is recorded in
[2026-10-06-reconciliation.json](2026-10-06-reconciliation.json), with source hashes,
canonical identities, aliases, publication decisions and explicit metadata limits.
[2026-10-06-reconciled-backlog.json](2026-10-06-reconciled-backlog.json) is the compact
local mirror of all 189 covered records' actual observed states. The complete live
inventory and editor receipts remain in the private outputs linked by that mirror.

The pre-snapshot board contains 286 cards and 107 logs. All 188 ready operations
match a reloaded readback, and all 113 changed cards match their exact editor
fields. Both repeat checks require zero writes. The overall closeout card remains
active until the recovery snapshot and isolated restore pass; its prepared final
wording is explicitly held in the manifest.

The [reconciliation account](../analyses/2026-10-06-board-reconciliation.md) explains
scope, limitations, corrections and the two-phase snapshot/attestation boundary.
The original dated JSON files and `*-pending.json` payloads remain historical
records. Their filenames do not mean they should be published again. Use the
reconciliation manifest and receipts to resolve current publication status.
`hold-shelf.html` remains the retained board source, not an October 6 database dump.
