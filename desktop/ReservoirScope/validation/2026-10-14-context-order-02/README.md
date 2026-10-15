# Fresh context-order window: safe cleanup, admission refused

**October 14, 2026, Pacific · Closed before any model request.** The user authorized safe memory cleanup and one fresh attempt with the same bounds. DaisyDisk was quit normally after confirming its idle visualization and empty collection tray. The new admission reported normal pressure level **1**, but only **30%** free memory against the unchanged **35%** threshold. Disk passed. The comparison did not start; all twelve slots are unstarted.

The [cleanup receipt](cleanup-result-01.json) records the actual actions. A bound accessibility read reopened DaisyDisk after the first quit; a second normal quit corrected that, and an exact-executable process check confirmed absence. No document editor, terminal, shared service or Being process was stopped. No file, cache or evidence was deleted. RSS and before/after percentages do not establish a reclaimed-memory amount.

The [prepared design](PROTOCOL.md) remains unchanged: six v8 contexts, two exact-content block orders, twelve standalone responses at most, the same model and generation/storage/time bounds, and no retries or feedback. [Twelve focused preparation tests](preparation-checks-01.json) passed; [independent review](PRE-RUN-REVIEW.md) confirmed the exact prompts and narrow attempt-path changes. Earlier transport and renderer qualifications were reused for unchanged behavior.

The [admission](host-admission-01.json) and [complete outcome ledger](outcome-01.json) preserve this second refusal. No supervisor, readiness request, generation, new journal or feedback application occurred. No response-only reading pack exists. [Preservation](preservation-01.json) confirms all 530 frozen files and all 51 files in the first context-order attempt remain exact, including its original refusal.

**Next:** the prepared comparison needs a resource window that meets the fixed admission requirements. This attempt is closed without polling, a third attempt, threshold relaxation or further application cleanup. Production v8 stays unchanged; neither refusal supplies evidence about block-order effects or writing quality. Minime and Astrid remain untouched.

To reproduce the numeric outcome from retained receipts, run in this directory:

```sh
python3 - <<'PY'
import json
from pathlib import Path
outcome = json.loads(Path('outcome-01.json').read_text())
preserved = json.loads(Path('preservation-01.json').read_text())
print({k: outcome[k] for k in ('status', 'actualPressureLevel',
    'actualMemoryFreePercent', 'actualDiskFreeBytes', 'realGenerationRequests')})
print('planned', len(outcome['slots']), 'unstarted',
      sum(s['status'] == 'unstarted' for s in outcome['slots']))
print('frozen', preserved['frozenFiles'], 'changed', preserved['changed'])
print('prior refusal files', preserved['priorContext01Files'],
      'unchanged', preserved['priorContext01FilesUnchanged'])
PY
```
