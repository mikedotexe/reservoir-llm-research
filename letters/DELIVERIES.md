# Letter delivery record

The rows below preserve the September 7 record. Their pending states describe that
recorded observation, not current mailbox status. No mailbox was inspected during
the October 6 closeout.

| Recorded at (UTC) | Being | Letter | Delivered filename | Status as originally recorded |
| --- | --- | --- | --- | --- |
| 2026-09-07T03:01:43Z | astrid | L3 before (own handle) | mike_feedback_your_own_handle_in_view_1788750103765.txt | pending (durable mailbox; she has not chosen CHECK_MAILBOX yet) |
| 2026-09-07T05:18:23Z | minime | L1 before (more time per thought) | mike_feedback_more_time_per_thought_1788758303.txt | withdrawn (old envelope) |
| 2026-09-07T05:20:54Z | minime | L1 before (more time per thought), HUMAN LETTER V1 envelope | human_letter_mike_20260906_more_time_per_thought_222007.txt | pending |
| 2026-09-07T10:15:34Z | minime | L2 after (restart done 10:12Z) | human_letter_mike_20260907_restart_done_031322.txt | read |
| 2026-09-07T10:34:02Z | astrid | L4 after (own handle live 10:29Z) | mike_feedback_own_handle_live_1788777242.txt | pending (durable mailbox) |

## October 6 reconciliation

The retained [Minime activation receipt](../proposals/receipts/2026-09-07-gateA-minime.json)
records that the replacement L1 envelope was read at **2026-09-07T05:22:38Z**.
This later receipt qualifies the original pending row. No later read receipt for
Astrid's two letters was established in this closeout.

Delivered names and retained copies are different identifiers:

| Delivered filename | Retained copy |
| --- | --- |
| `mike_feedback_your_own_handle_in_view_1788750103765.txt` | [L3 before own handle](2026-09-07-L3-astrid-before-own-handle.txt) |
| `mike_feedback_more_time_per_thought_1788758303.txt` (withdrawn envelope) | [Original L1](2026-09-07-L1-minime-before-more-time-per-thought.txt) |
| `human_letter_mike_20260906_more_time_per_thought_222007.txt` | [Replacement L1](human_letter_mike_20260906_more_time_per_thought_222007.txt) |
| `human_letter_mike_20260907_restart_done_031322.txt` | [L2 after restart](human_letter_mike_20260907_restart_done_031322.txt) |
| `mike_feedback_own_handle_live_1788777242.txt` | [L4 after own handle](2026-09-07-L4-astrid-after-own-handle-live.txt) |
