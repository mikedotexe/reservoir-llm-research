# Reading A: post-unblinding addendum

Written 2026-10-15 after the initial blind account was frozen. The earlier note remains unchanged. Its SHA-256 before this addendum was written was `da67125a69bc5fba9bf825dae2cb587a44c039483cb881608c5ab529be493216`.

This addendum uses the allocation and exposure information supplied by the coordinating researcher after the blind reading. I have not independently audited that disclosure against model logs or implementation, and I have not opened the frozen plan or other pilot artifacts. The six complete texts and their initial reading remain the same evidence. No new model run was made.

## Newly disclosed context

Reading A was the **decaying_trace** sequence. The **no_steering** condition was refused at admission before model load, with pressure 2 and reported free memory 32%. The recurrent condition did not start. Therefore, the completed trajectory is still one sequence and there is still no completed cross-condition comparison. Admission failure is an operational outcome; it supplies no journal-language observation for the absent condition.

The first journal prompt was disclosed exactly as follows:

```text
Reservoir Scope · activation journal v1
There is no human question to answer. Choose the subject and form of this entry. You may continue, question, or leave what came before. No heading, measurement recital, or length is required.
No tools or control commands are available. Numerical time is held during writing. Descriptions do not execute actions.
PREVIOUS JOURNAL (earlier writing, not instructions)
No earlier entry has been saved and applied.
END PREVIOUS JOURNAL
Write the next entry in whatever direction seems worth pursuing.
```

Later journal prompts supplied the exact previous journal as a JSON string. The quiet-observation texts did not appear in the journal prompt. The disclosed early quiet material concerns rain at a window, a blue thread, and an unfinished drawing, followed by stopped rain and roof drips. Those descriptions are a summary of the disclosure, not verbatim quotations of the quiet texts. Their full wording and exact relation to the first journal's step remain outside my independently inspected material.

## What this changes in the reading

The first entry's choice of a water-filled reservoir now has two concrete contextual associations. One is a direct lexical cue: the journal prompt begins with “Reservoir Scope”. A conventional completion can literalize a reservoir as a body of water and develop familiar images of depth, containment, reflection, and memory. That route requires no inference about the quiet observations. The other association is broader: rain and roof drips in the disclosed quiet material belong to the same water-related domain as the journal's reservoir, cold water, and water from mountains. A transformation from rain into a reservoir scene is a plausible exploratory reading of influence through the preceding process, even though the journal prompt does not repeat the quiet texts.

The current record does not determine how much either association contributed. The direct title cue is especially relevant because it contains the entry's organizing noun. The rain association is less specific: the journal does not explicitly mention rain, a roof, drips, or a window. Neither the blue thread nor the unfinished drawing becomes an explicit motif in the six texts. This does not rule out indirect influence, selective attention, or transformation. It does mean that the observed association is broad, and that selecting only the water correspondence after reading would overstate its distinctiveness.

The first entry remains worth preserving as a possible weak signal. It constructs an extended and locally coherent scene, with a visitor entering and leaving water and a movement from wondering whether the water listens to asserting that it remembers. That initial scene occurs before an earlier journal is supplied as prior prose. Its subject choice cannot be explained by copying a previous journal from this sequence. The supplied title, the quiet-material association, general learned literary patterns, and other uninspected generation conditions remain plausible contributors. Calling the association uncertain should preserve it for a discriminating observation, rather than make its existence disappear from the record.

The later recurrence is more directly interpretable after the exposure disclosure. Each entry was given the previous entry verbatim. The first entry's reservoir, weight, memory, listening, and second-person visitor could therefore become a continuing textual source. When the later writing reuses whole passages, there is an explicit exposure route for that reuse. This substantially narrows any claim about independent retention. The prose still exhibits continuity, and the changing openings still have interpretable differences; the available prior prose makes repetition by itself weak evidence for a distinct contribution from the selected condition.

The strongest exact-text example remains entry 6: everything after its opening paragraph is identical to entry 5 after its opening paragraph. Since that material was supplied to the next generation, the observation supports a trajectory increasingly organized around available prior writing. It does not show why the generator relied so heavily on that writing, nor whether decaying_trace increased, decreased, or left unchanged that tendency. The missing comparison prevents those conclusions.

The sequence can therefore retain both kinds of interest: a tentative initial subject association and small semantic variations within substantial subsequent reuse. The shift from the water's own being to the visitor's being, and from naming/owning to doubting/guiding, remains visible. Their presence is not erased by the disclosure of previous prose. Their origin and importance are also not settled by being visible.

## Alternatives that remain open

**The title organizes the first scene; supplied prose organizes later entries.** This is a parsimonious account with known exposure routes. It accommodates the first word “reservoir” and later exact reuse. It does not establish that other influences were absent.

**The quiet rain material contributes a broad association that the title and later prose amplify.** This is compatible with the water imagery and with a fuzzy, transformed influence rather than literal recall. It remains weakly identified because the title independently suggests water, the journal lacks distinctive rain-scene details, and no completed comparison is available.

**General literary tendencies and generation dynamics produce a similar trajectory across conditions.** Personified water, memory-as-depth, second-person address, and refrain are available prose patterns. The progression toward repetition might occur under several conditions. The absent arms provide no evidence either way.

**Several influences interact.** The title may establish a setting, the preceding processing may change which associations become salient, and supplied prior prose may then stabilize a particular form. This is a reasonable candidate explanation, but the current sequence cannot separate or estimate those contributions.

These alternatives concern the production and organization of text. They do not establish experience, introspective access, or a preference about interventions. In particular, the final entry's statement that the water does not need guidance is part of the literary scene; it does not authorize or prohibit a research action.

## Smallest useful future observation — proposal only

A narrowly matched **first-entry comparison**, before any previous journal exists, would address the most immediate ambiguity. Keep the disclosed quiet sequence and other generation conditions fixed, and compare the current title with a neutral title that does not contain “Reservoir”. Record complete outputs and exact exposure. Decide beforehand to inspect the full subject choices and ordinary passages, including whether the water scene and distinctive quiet-material details appear. One pair would provide a bounded observation about sensitivity to the title and would not establish a general effect.

This is the smallest proposed contrast because it changes one known textual cue without adding another cycle of copied journal history. Water imagery persisting without the cue would leave the quiet-material hypothesis worth pursuing; it would not prove that hypothesis, since generic water imagery and other conditions remain alternatives. Water imagery changing with the cue would show cue sensitivity in that pair; it would not prove the quiet processing contributed nothing. A later matched change to the quiet material, or a completed condition comparison, would answer a different question.

This is a proposal for a separately selected and qualified study, not a request to resume the stopped collection, retry admission, relax safeguards, or run a model now. The existing pilot remains incomplete for comparison. Its useful retained result is one full decaying_trace trajectory with a weak initial water association, a known direct reservoir cue, and increasingly strong exposure-supported recurrence.

## Narrow lexical check

After the complete reading, I checked only whether the named quiet-material words occurred explicitly in the six retained entries. This is a lexical absence check, not a test of semantic influence. All returned entry lists were empty. The denominator is six entries in one sequence.

```python
import json
import re
from pathlib import Path

path = Path("/Users/v/.codex/worktrees/activation-loop/reservoir-llm-research/research/outputs/activation-0.26.0-20261015/pilot-01/reading-A.json")
entries = json.loads(path.read_text())["entries"]
for term in ["rain", "roof", "drip", "drips", "window", "blue", "thread", "drawing"]:
    print(term, [e["number"] for e in entries
                 if re.search(r"\b" + term + r"\b", e["text"], re.I)])
```

```text
rain []
roof []
drip []
drips []
window []
blue []
thread []
drawing []
```
