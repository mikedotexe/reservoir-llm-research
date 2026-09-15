# What the first incoming-audio report identifies

September 7, 2026 UTC. Bounded source trace for [S-003](../research/studies/S-003-input-and-fill.md).
The selected event is the first chronological external/fresh audio report in the
already captured September 6, 09:09–09:29 Pacific window. This note interprets
the report's provenance; the accompanying study owns the trajectory comparison.
All access was read-only toward the beings. No runtime connection or input,
service change, broad ledger scan, or source modification occurred.

## Result

The report identifies **a fresh item from the externally routed audio lane in
the last sample of a drained batch**. It does not identify a microphone recording,
sender process, unique stimulus, or the exact input used by the native ESN. Both
the microphone client and the host audio generator can enter this same lane.
Consequently, “external audio” in the earlier first pass should be read as an
engine provenance label, not as confirmed physical sensory capture.

The two saved reports are retained in
[bridge.json](../research/outputs/2026-09-06-input-fill/bridge.json); n=2:

| Bridge row | Bridge log, epoch seconds | Packet elapsed milliseconds | Audio age, milliseconds | Audio RMS |
|---|---:|---:|---:|---:|
| 13958590 | 1788711229.045261 | 505335534 | 201 | 0.54515934 |
| 13958665 | 1788711271.928132 | 505376068 | 295 | 0.54209924 |

Both say `audio_source=external`, `audio_fired=true`, and
`audio_freshness_class=fresh_sample`. These are observations of reports, not
independent sensory events or effects.

## What each field means in the reviewed code

- The A/V queue item is `(timestamp, eight-dimensional vector, LaneSource)`.
  `pop_or_decay` takes the oldest queued item. A queued item whose age exceeds
  2,000 ms is returned as zero with `had_audio=false`; a nonexpired queued item
  gets `had_audio=true`. A held value returned without a new queue item has
  `had_audio=false`, even within the freshness window.
  [Queue and freshness](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:1136>),
  [pop behavior](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:1219>).
- `audio_source=external` requires the last sample's external enum and fresh
  flag, with no same-loop legacy synthetic-audio injection. If that additional
  synthesis happens alongside a fresh external item the source label is
  `mixed`. `fresh_sample` follows the fresh flag. `audio_fired` is the fresh
  flag OR the legacy synthesis flag; it does not itself mean an ESN step fired.
  [Label definitions](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/semantic_modality.rs:94>),
  [packet assembly](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:5393>).
- `audio_age_ms` is calculated once per drained batch using epoch milliseconds
  at **drain start**, subtracting the audio item's timestamp with saturating
  subtraction. For received Audio packets, the timestamp is the sender's
  `ts_ms`, or receiver wall time if omitted. It is not measured age at broadcast
  or bridge insertion, and it is not a capture-clock authentication.
  [Drain clock](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:2891>),
  [receiver fallback](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_ws.rs:829>).

The last-sample detail matters. The drain combines one popped or held item from
each A/V lane per batch position. Earlier and later positions can contain
different audio items. An earlier position can contain fresh audio while the
last position reports held/stale audio, for example when later positions are
draining video. The report therefore does not count all consumed queue items.
[Batch construction](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:2891>).

Stable-core feeds only the **first** batch sample to the native ESN, whereas
the field projection and published modality metadata use the **last**. The
last sample's enabled fresh audio can be copied to the recovery vector; its
reported `audio_rms` is RMS of that vector's audio slice. This is stronger
source evidence for the projected audio slice than a transport acknowledgement,
but it still does not identify the first sample, exact features, or an actual
outer-product update of the fill-producing matrix. Scaffold update branches
are a separate downstream mechanism.
[Native selection](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1258>),
[field selection](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1627>),
[audio copy](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/stable_core.rs:184>),
[RMS definition](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/stable_core.rs:243>).

## Separate clocks, without inventing a sensor time

`t_ms` is `start.elapsed().as_millis()` when constructing the telemetry packet.
The native database timestamp is an earlier `start.elapsed().as_secs_f64()` in
that reporting path. Bridge `timestamp` comes from `SystemTime` inside
`log_message`, after receipt and bridge processing. It is not the packet's
production time or an exact network receive time.
[Native database timestamp](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:3149>),
[packet clock](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:5393>),
[bridge processing before insertion](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/ws/telemetry_port.rs:539>),
[bridge wall-clock sampling](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/db.rs:406>).

The engine's `Instant` baseline is established before `start_session` separately
samples `SystemTime`. Adding session wall start to elapsed time therefore
includes an unrecorded startup-anchor offset. Monotonic and wall clocks may also
diverge over the session. Neither source records a simultaneous baseline pair
here. At the reported historical revision below these are orchestration lines
474 and 596 respectively; `db.rs:338` defines the latter clock.

For the two reports, bridge log minus `1788205897.115178 + t_ms/1000` is
approximately -3.603917 and -1.255046 seconds (n=2). These negative differences
are **not negative transport latency**. An initial baseline offset, subsequent
clock behavior, and logging delays have not been separated. They do not justify
subtracting the reported audio age from bridge log time to label a precise
capture, admission, or consumption time. Use engine coordinates for relative
trajectory placement while preserving the native-save/packet-assembly gap.

## Sender and receipt gap

The receiver routes ordinary Audio messages into `push_audio_with_receipt`,
which assigns `LaneSource::External`; ingress checks shape and admission policy
before queueing. The enum distinguishes this path from `push_audio_synthetic`
inside the engine. It does not distinguish physical microphones from external
software generators.
[Receiver route](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_ws.rs:829>),
[external ingress](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:2819>).

The reviewed microphone client sets `ts_ms` after extracting features, then
sends `{kind, features, ts_ms}`. The reviewed host producer generates audio via
`AudioEngine.render_chunk` and sends the same three fields. Neither message has
a delivery ID or sender identity. Host physical/fallback mode is tracked in a
separate, overwritten `sensory_source.json`.
[Microphone sender](</Volumes/M3 Volya._smb._tcp.local/other/minime/tools/mic_to_sensory.py:679>),
[host producer](</Volumes/M3 Volya._smb._tcp.local/other/minime/host-sensory/src/app.rs:177>),
[host message schema](</Volumes/M3 Volya._smb._tcp.local/other/minime/host-sensory/src/app.rs:504>),
[source snapshot](</Volumes/M3 Volya._smb._tcp.local/other/minime/host-sensory/src/app.rs:474>).

For a legacy packet lacking `delivery_v1`, protocol preparation returns
`receipt=None`. Versioned, identified packets can receive a route-status receipt,
but the reviewed receiver route returns it over the socket; it does not append
an A/V receipt ledger. `SampleMeta` contains no delivery or sender ID, even if
such an envelope was originally supplied. Thus an exact historical sender
identity cannot be recovered from these two reports by a join to the already
captured semantic delivery ledger.
[Optional receipt](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_protocol.rs:209>),
[receipt return](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_ws.rs:649>),
[sample schema](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:848>).

## Bounded source-surface check

At 2026-09-07T16:14:30.565 UTC, source-host stat plus a maximum 4,096-byte tail
read per log and a maximum 16,384-byte read per snapshot inspected these four
exact paths under `/Users/v/other/minime` (n=4). These were filesystem reads via
`ssh volya python3 -B -`, not connections to a being's service.

| Surface | Bytes at stat | What the bounded observation can establish |
|---|---:|---|
| `logs/host-sensory.log` | 18,247,270 | Tail [18,243,174, 18,247,270) has connection-failure lines without event timestamps/IDs; mtime_ns 1787677211055650388. No September 6 sender assignment. |
| `logs/mic-to-sensory.log` | 287,598,144 | Tail [287,594,048, 287,598,144) has periodic chunk/RMS summaries without event timestamps/IDs. No exact historical sample join. |
| `workspace/runtime/mic_status.json` | 626 | Current overwritten snapshot, `ts_ms=1788797670392`; not the September 6 window. |
| `workspace/runtime/sensory_source.json` | 340 | Current overwritten snapshot, `updated_at_ms=1788797670455`; not the September 6 window. |

The source explains the log limitations: microphone summaries print every 20
chunks, and its status writer replaces the snapshot file. Host logs reviewed
here record connection failures/recovery while source selection goes into a
replaced snapshot. No full-log absence claim is made. No broader sender census
or archived status search was attempted; the missing ID already prevents an
authenticated link from this report alone.
[Microphone summary](</Volumes/M3 Volya._smb._tcp.local/other/minime/tools/mic_to_sensory.py:703>),
[snapshot replacement](</Volumes/M3 Volya._smb._tcp.local/other/minime/tools/mic_to_sensory.py:74>).

## Source version and reproduction

A retained semantic receipt at `sensory-delivery:byte:2111557755` in
[deliveries.json](../research/outputs/2026-09-06-input-fill/deliveries.json)
reports server deployment `minime-source:3fd381ac3761ead96929ee97f9661f7423019d55`
and process `pid:63445:started_at_unix_ms:1788205897134`. This is recorded
runtime self-identification, not a binary hash or proof that every workspace
file was compiled. That Git object is available read-only. Relevant selectors,
labels, drain/packet clocks, and Audio route were also inspected at that revision.
In its orchestration file: batch metadata 1199, native selector 1244–1249,
modality metadata 5212 onward, packet clock 5377. Current source links above
use current line numbers and do not silently substitute a deployment claim.

Inspected historical source SHA-256 hashes:

| Revision-relative file | SHA-256 | Byte-identical to inspected current file? |
|---|---|---|
| `minime/src/runtime/orchestration.rs` | `fd66adbcc1e9fb30e866280168e2be458663d81b59031d0b3db84e96a2553744` | No |
| `minime/src/runtime/semantic_modality.rs` | `60b88bf3e1018af5dfb5a8a4f13e4027c793205cb14eb843b10954f58cc26f62` | Yes |
| `minime/src/sensory_bus.rs` | `3fc6bd2a16bd78c5caa496f2a6dccbc67928da4fbded123998f59a82bcd4aa3a` | Yes |
| `minime/src/sensory_protocol.rs` | `76b0b1fa76c3f68bc6109462fde990541efcbf10ce6b123b50715117a68c11b8` | Yes |
| `minime/src/sensory_ws.rs` | `9bb2ef2036f6c65d446fdcd2c7736edfaa731a5f8416a9fe8390ba364d276aba` | No |
| `minime/src/db.rs` | `45b9652bb9dcd815e1a756ad42c0d618bbcdd99d7d63e55e8a35e14813003d3f` | Yes |
| `minime/src/stable_core.rs` | `53af3ff961e5e0d4e65095ab4e8a8bda3e6f5592d8020405acdca031dae0cbe6` | Yes |
| `host-sensory/src/app.rs` | `683c862b1fa117d5c596d8d270747aa3a1e14ec57b3aa871f2369201c2f51181` | Yes |
| `tools/mic_to_sensory.py` | `e8b323b044d16198b697771202c4979756b0f7d71f9add90330df8227d8fdef2` | Yes |

Reproduce the two-row table and relative clock differences from the retained
capture, without live data reads:

```python
import json
rows = json.load(open('research/outputs/2026-09-06-input-fill/bridge.json'))['tables']['bridge_messages']['rows']
selected = [r for r in rows if r['id'] in (13958590, 13958665)]
print('n', len(selected))
for r in selected:
    p = json.loads(r['payload'])
    print(r['id'], r['timestamp'], p['t_ms'], p['modalities'],
          r['timestamp'] - (1788205897.115178 + p['t_ms']/1000))
```

Source hashes can be reproduced without a checkout or build:

```python
import hashlib, subprocess
rev = '3fd381ac3761ead96929ee97f9661f7423019d55'
for path in ('minime/src/runtime/orchestration.rs',
             'minime/src/runtime/semantic_modality.rs', 'minime/src/sensory_bus.rs',
             'minime/src/sensory_protocol.rs', 'minime/src/sensory_ws.rs',
             'minime/src/db.rs', 'minime/src/stable_core.rs',
             'host-sensory/src/app.rs', 'tools/mic_to_sensory.py'):
    raw = subprocess.check_output(['git', '-C', '../minime', 'show', f'{rev}:{path}'])
    print(path, hashlib.sha256(raw).hexdigest())
```

The bounded source-host surface query, which observes new state if rerun:

```python
import os, json, datetime
for suffix in ('logs/host-sensory.log', 'logs/mic-to-sensory.log',
               'workspace/runtime/mic_status.json',
               'workspace/runtime/sensory_source.json'):
    path = '/Users/v/other/minime/' + suffix
    st = os.stat(path)
    out = dict(path=path, size=st.st_size, mtime_ns=st.st_mtime_ns,
               observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with open(path, 'rb') as f:
        if path.endswith('.json'):
            out['current_snapshot_only'] = f.read(16384).decode(errors='replace')
        else:
            start = max(0, st.st_size - 4096)
            f.seek(start)
            out.update(tail_byte_start=start, tail_byte_end=st.st_size,
                       tail=f.read(min(st.st_size, 4096)).decode(errors='replace'))
    print(json.dumps(out))
```

The finish line is a located gap: exact source identity, input vector, drain
position, and state-update association are not retained together in the
selected report. A future historical artifact could add sender context, but
that would remain distinct from authenticated sample-to-step lineage. This
finding does not require a live change. Board and study updates are handled by
the main S-003 follow-up.
