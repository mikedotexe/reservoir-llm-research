# Provisional 30% admission rule

The user explicitly asked to relax the free-memory guard on the dedicated Mac.
This window changes only the reported-free threshold from 35% to **30%**, while
requiring normal pressure level **1**, at least **8 GiB** free disk, successful
read-only probes and one exclusive admission after the prospective freeze.
The model, twelve-request ceiling, context/output/deadline, storage, serial
execution, owned-service lifetime, isolation, completion gates and no-retry rule
are unchanged. This is a provisional operating choice, not a validated minimum
memory requirement or guarantee of uninterrupted performance.

## Origin and interpretation

The checked historical [0.14 protocol](../2026-10-13-writing-room-0.14.0/PROTOCOL.md)
already calls 35% an established owned-run method. The
[0.15 follow-up](../2026-10-13-v4-writing-episode02/PROTOCOL.md) explicitly calls
it a narrow operational threshold, not full host qualification. Later copied
admission scripts inherited `free >= 35`; no measured derivation of 35% from this
model’s allocation was found in that bounded trace. This does not assert the
first-ever origin of the number across all historical work.

Apple describes memory pressure using free memory, swap rate, wired memory and
file-cached memory together. A free-memory number alone is not a complete capacity
assessment. [Apple Activity Monitor documentation](https://support.apple.com/guide/activity-monitor/view-memory-usage-actmntr1004/mac)
Ollama also documents that concurrent requests and context length affect memory
requirements; this window retains one serial request and the existing context.
[Ollama FAQ](https://docs.ollama.com/faq)

## Read-only inspection, not admission

At **2026-10-15T20:55:38.211122+00:00**, the task ran these commands once:

```text
/usr/sbin/sysctl hw.memsize hw.model machdep.cpu.brand_string kern.memorystatus_vm_pressure_level vm.swapusage
/usr/bin/memory_pressure
/usr/bin/vm_stat
```

All exited zero. The tool transcript retains their output. Selected readings:

| Reading | Observed value |
|---|---:|
| Physical memory | 68,719,476,736 bytes (64 GiB) |
| Model / CPU | Mac16,11 / Apple M4 Pro |
| Pressure level | 1 |
| `memory_pressure` reported free percentage | 35% |
| Swap used | 15,673.00 MiB |
| VM page size | 16,384 bytes |
| Raw free pages (`vm_stat`) | 70,273 |
| Wired pages | 1,886,276 |
| Compressor occupied pages | 789,683 |

Raw free pages are about 1.07 GiB, demonstrating why the reported 35% must not be
read as 22.4 GiB of literally unused RAM. Existing swap usage and lifetime swap
counters do not, without a rate measurement, establish current thrashing. No such
rate measurement or memory-load attribution is claimed. These observations are
not the future window’s admission and do not authorize a launch.

## Prospective checks and historical preservation

The new admission tests require 29% to refuse and 30%/31% to pass with the other gates
satisfied. They also check pressure 2/4, a disk value one byte below 8 GiB,
missing/failed/malformed probes, out-of-range percentages, altered/unbound policy,
and the no-second-admission rule. All host operations in these tests are mocked.

The parent must first finish product builds/tests and explicitly release the new
window, then freeze and run admission once. Earlier source-role windows remain
closed: the first was refused at runtime identity checking; the second was refused
at 31% under its own fixed 35% rule. Their files and outcomes remain unchanged.
Ollama 0.40.5 source and synthetic checks are conditional preflight evidence;
neither old refusal qualified actual owned startup or model generation.
