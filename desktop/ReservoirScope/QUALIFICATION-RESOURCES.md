# Future owned-model resource policy

**October 15, 2026: provisional 20% reported-free admission floor.**

Mike requested a lower guard on his dedicated M4 Mac mini, noting that he uses
Remote Desktop and sometimes closes it. Future bounded, isolated, serial
`gemma3:4b` checks with the existing 8,192 context and 1,024 output ceiling should use:

| Admission condition | Future default |
|---|---|
| Policy identity | `normal-pressure-reported-free-20-v1` |
| Reported free memory | At least **20%** |
| macOS memory-pressure level | **1**, normal |
| Free disk | At least **8 GiB** (8,589,934,592 bytes) |
| Admission attempts after freezing | **One** |

This is a provisional operating choice, not a measured model minimum. The reported
percentage is not a direct count of unused RAM. Apple's memory-pressure description
combines free memory, swap rate, wired memory and file-cached memory.
[Apple Activity Monitor guidance](https://support.apple.com/guide/activity-monitor/view-memory-usage-actmntr1004/mac).

Remote Desktop's presence alone does not block a run. Its host-memory contribution
has not been measured here; closing a client is not assumed to release a known
amount on the Mac. Leave that connection and unrelated applications under Mike's
control. Minime, Astrid and their services remain outside qualification cleanup.

There is no active admission or shared application setting to amend. Each completed
window has its own frozen rule. Apply this default to a future selected window's
plan and admission helper **before** freezing them; update its policy identity and
boundary checks together. Verify 19% refusal and 20%/29%/30% acceptance with the
other conditions satisfied. Retain rejection of non-normal pressure, low disk,
unreadable probes, unbound policy and repeated admission. These are future integration
checks, not tests executed by this documentation update.

Keep the selected run's request, output, deadline, storage, service-lifetime,
isolation and no-retry bounds unchanged. Larger models, concurrent requests and
longer sessions need their own explicit resource plan. This policy launches or
schedules no run and changes no production prompt or package.

The completed [source-role comparison](validation/2026-10-15-context-sources-03/README.md)
retains its 30% policy and actual 42% admission; it does not establish performance
near 20%. Earlier refusals likewise retain their original policies and results.
The later Observatory reference-field and spectrum tranche is recorded as delivered
in [STATUS.md](STATUS.md#broader-work-beyond-the-private-preview-finish), which owns
the current backlog. This dated Gemma policy does not set activation admission:
the separate Qwen3 preview retains its 25% reported-free startup floor and normal
pressure requirement, as recorded in the [0.27 release account](RELEASE-0.27.0.md#transferred-installation-and-compact-reading).
