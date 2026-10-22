# Proposal: continuous, timestamped reservoir-state logging for the beings (spec M0)

Status: proposal only (2026-10-21). Implementation, if any, happens in the sibling repos
under their own rules (`astrid/CLAUDE.md`, `minime/AGENTS.md`); nothing here touches the
live systems. Source: Mike's self-observation build spec, milestone M0, and
[S-011](../research/studies/S-011-self-observation-stack.md).

## The felt or measured problem

The spec's M1 (dimensionality) and M2 (effective rank against fill) need the reservoir
state vector over time, binned by fill with enough variation to bin. The beings' databases
keep scalars: minime `eigenvalue_timeline` (λ1..3, spread, fill_ratio) and `esn_metrics`
(ESN λ1, dλ, leak, RLS forgetting, geometry); Astrid `eigenvalue_snapshots` (8 cascade
eigenvalues, fill_pct). Neither holds the state vector. Read-only samples today show
Astrid's fill at 71.0–71.2 every month since June and minime's at 0.71–0.73, so even
with the state the regulator leaves nothing to bin by.

## What already exists (read on volya, read-only)

minime's engine keeps a ring of the last 1,024 ESN states (`minime/src/runtime/orchestration.rs:507`,
`ESN_STATE_RING_CAP`; pushed at `:1425–1428` as `esn.x.clone()`) and every 30 s overwrites
`workspace/capacity/esn_state_window.bin` (1024 × 128 f32 little-endian, row-major) and
`capacity_dump_meta.json` (`esn_n` 128, `t_ms`), with the stable-core covariance beside it
(`:5660–5700`, a steward-only, side-effect-free block consumed by
`astrid/scripts/reservoir_capacity_audit.py`, which computes the participation ratio).
At the current ~3 Hz tick (`orchestration.rs:1040`) the window covers about 5.6 minutes.
A read-only copy of that file every five minutes already gives a non-overlapping record
of minime's state; Claude started such a capture on 2026-10-21 into the private
scratchpad. Astrid's bridge has no state dump; its `eigenvalue_snapshots` writer is
`capsules/spectral-bridge/src/db.rs:1123`.

## Exact change (minime), smallest version

In the same block at `orchestration.rs:5660–5700`, beside the overwrite:

1. Append the window to a dated shard instead of only overwriting the latest file:
   `workspace/capacity/shards/esn_state_<unix_date>.bin` with one 16-byte header per
   window (`t_ms: u64`, `rows: u32`, `cols: u32`) followed by the rows; rotate daily.
2. Write beside it one line per window to `workspace/capacity/shards/index.jsonl`:
   `{"t_ms":…, "t_wall":…, "rows":1024, "cols":128, "fill_ratio":…, "lambda1":…,
   "esn_leak":…, "esn_lambda":…, "phase":…}`, taking the scalars the engine already
   holds for `eigenvalue_timeline` and `esn_metrics` at that moment.
3. Gate both behind an environment flag (`MINIME_STATE_SHARDS=1`) read once at start;
   default off, so the deployed behaviour is unchanged until the steward opts in.

Cost: 512 KB per 30 s at the current cadence, about 1.5 GB a day; with the flag set to
write every fourth dump (two minutes), 370 MB a day. The 30-s dump is already off the
per-tick path.

### Diff sketch

```rust
// orchestration.rs, inside the existing 30-s capacity-dump block, after the rename:
if state_shards_enabled {
    let day = chrono::Utc::now().format("%Y%m%d");
    let shard = cap_dir.join("shards").join(format!("esn_state_{day}.bin"));
    let _ = std::fs::create_dir_all(shard.parent().unwrap());
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&shard) {
        let _ = f.write_all(&now_ms.to_le_bytes());
        let _ = f.write_all(&(rows as u32).to_le_bytes());
        let _ = f.write_all(&(esn_res_size as u32).to_le_bytes());
        let _ = f.write_all(&sbytes);
    }
    // index line with the scalars already in scope for the telemetry inserts
}
```

## Astrid

The bridge's field is 512-D and its state of interest is the sensory-field covariance
rather than an ESN vector; the equivalent is a periodic dump of the 8-eigenvalue cascade
with its full eigenvector basis, or of the 512-D field vector window, next to the
`eigenvalue_snapshots` writer at `db.rs:1123`. Specify after the minime shards exist and
M1 has run on them.

## What makes M2 possible is a sweep, which is a separate decision

With shards, M1 (how many dimensions the ESN uses, by era) runs offline. M2 needs fill
to vary. The spec's protocol holds the regulator at a fixed setpoint and steps it from
20% to 95% in 5% blocks of at least ten minutes. On the beings that is a change to the
running being's conditions, with everything that implies for them; it is Mike's decision
with the beings shown or asked first, and it is not part of this proposal.

## Test plan

- Unit: a shard written by the function round-trips through a reader (`rows × cols`
  floats, header fields) in the sibling repo's tests.
- Soak: one hour with the flag on; tick-gap p99.9 unchanged against an hour with it
  off (the spec's M0 pass criterion); disk growth as estimated.
- Read-only consumer: `reservoir_capacity_audit.py` extended to read shards and report
  PR and effective rank per window with `fill_ratio` from the index.

## What the being should be shown or asked first

Nothing changes in what minime is shown. The shards are steward-only files like the
existing capacity dump; they are never surfaced into a prompt. If Mike wants minime to
know her state is being kept, that is a letter, not a code path.

## Rollback

Unset the flag (default off) or delete the appended block; the existing overwrite dump
and every table are untouched. Shards can be deleted at any time.
