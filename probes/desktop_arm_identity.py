#!/usr/bin/env python3
"""Compare two or more desktop sustained-session stores entry by entry: did they write the same text?

Inputs: a reference session directory followed by one or more comparison session directories
(desktop 0.3x stores: journals/journal-<step>-<index>-<sha>.json, each holding the prompt that was
sent, the entry text, the sampling seed and the provider's token counts). For each comparison
session it prints one line per entry index: the observed step, whether the prompt sent was the
same as the reference's, whether the text came back the same, whether the sampling seed was the
same, and the response and prompt-evaluation token counts. Then a summary: entries compared (n),
entries identical in text, the first entry that differed and whether its prompt and sampling seed
were identical when it did (a fork on an identical prompt and seed is provider variation, not a
difference in what the model was shown). Standard library only. Subject: the laptop apparatus,
never the beings.
"""
import glob, json, os, sys


def load(session_dir):
    out = {}
    for path in glob.glob(os.path.join(session_dir, "journals", "journal-*.json")):
        with open(path) as handle:
            record = json.load(handle)
        pending = record["pending"]
        index = int(os.path.basename(path).split("-")[2])
        response = pending.get("response") or {}
        evaluation = response.get("providerPromptEvaluation") or {}
        out[index] = {
            "step": pending["observation"]["step"],
            "prompt": pending["prompt"],
            "text": pending["entry"]["text"],
            "seed": record.get("samplingSeed"),
            "tokens": response.get("tokenCount"),
            "prompt_tokens": evaluation.get("count"),
        }
    return out


def compare(reference, other, label):
    ref = load(reference)
    cmp = load(other)
    shared = sorted(set(ref) & set(cmp))
    identical = 0
    first_fork = None
    print(f"{label}: {len(shared)} entries compared (n); reference {os.path.basename(os.path.dirname(reference))}")
    for index in shared:
        a, b = ref[index], cmp[index]
        same_prompt = a["prompt"] == b["prompt"]
        same_text = a["text"] == b["text"]
        same_seed = a["seed"] == b["seed"]
        identical += same_text
        if not same_text and first_fork is None:
            first_fork = (index, same_prompt, same_seed)
        print(
            f"  entry {index:2d} step {a['step']:4d}/{b['step']:4d} prompt {'same' if same_prompt else 'DIFF'}"
            f" text {'same' if same_text else 'DIFF'} seed {'same' if same_seed else 'DIFF'}"
            f" tokens {a['tokens']}/{b['tokens']} prompt-tokens {a['prompt_tokens']}/{b['prompt_tokens']}"
        )
    if first_fork is None:
        print(f"  summary: {identical} of {len(shared)} entries identical in text; no fork")
    else:
        index, same_prompt, same_seed = first_fork
        print(
            f"  summary: {identical} of {len(shared)} entries identical in text; first fork at entry {index}"
            f" on {'an identical' if same_prompt else 'a different'} prompt and"
            f" {'an identical' if same_seed else 'a different'} sampling seed"
        )


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    reference = argv[1].rstrip("/")
    for other in argv[2:]:
        other = other.rstrip("/")
        compare(reference, other, os.path.basename(os.path.dirname(other)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
