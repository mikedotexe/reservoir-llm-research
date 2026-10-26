# 0.40.1 · a clearer first journal session

October 25, 2026. A local development checkpoint on `codex/s021-walkthrough`.

The root README and app guide now lead with launch, what appears first, a short
journal session, reading and export. The source setup includes the previously
missing bootstrap staging command. Build details moved to [Building](BUILDING.md);
the full prior app README is preserved in [the dated copy](README-HISTORY-2026-10-25.md).

Advanced settings now offers **Writing invitation** with **Current readout (as
built)** and **Plain journal · prior text, no numerical readout**. The plain choice
selects the existing `reservoir-journal-inert-plain-contract-no-tag-v1` prompt.
It changes no model, memory, numerical or limit settings. Current readout remains
the default, and existing research invitations retain their values.

The [first-session guide](GETTING-STARTED.md) suggests up to twelve writing attempts
or thirty minutes, while explaining that the existing six-hour defaults and custom
pre-start limits remain available. Extending an already-created session was not
implemented in this checkpoint; Mike requested it as the next part of this work.

## Checks

- All 520 frontend tests across 62 files passed, including four invitation tests.
- TypeScript and the production frontend build passed, followed by a native macOS
  debug app bundle with a separate preview identity. The existing bundle-size
  advisory remains; the local app is ad-hoc signed and not notarized.
- Native UI inspection reached My reservoir → Advanced settings → Writing
  invitation and selected Plain journal. No model request or new research run.
- The bootstrap helper downloaded and verified both pinned assets into a temporary
  manifest-only directory; its second run reused both without downloads.
- Canonical reference verification passed: 180 sources, 43 resources and one fixture.
- Independent source/setup and new-reader reviews checked the launch steps and labels.

Private local proof is under `research/outputs/readme-polish-20261025/` (ignored).
This is not second-machine installation, an hours-long endurance test, or newcomer
acceptance. The frozen 0.39.0 instrument, 0.27.0 candidate 04, closed study evidence
and live systems are unchanged. No publication is claimed.
