# Matched S-013–S-016 figure

`probes/introspection_matched_figure.py` renders an existing JSON report from the
private `replication_comparison.py` helper. It generates PNG, editable SVG, and a
JSON receipt. It does not open score reports, responses, providers, or live data;
it neither rescales scores nor recomputes estimates. Matplotlib is imported only
at render time, separate from the standard-library experiment runner. Use a
plotting environment with Matplotlib (the existing `analysis` package extra is
also sufficient).

From the checkout, with a completed comparison report already present:

```sh
python probes/introspection_matched_figure.py \
  --input research/outputs/introspection-20261024/methods-review/replication-matched-comparison-v1.json \
  --output-prefix research/outputs/introspection-20261024/matched-figure-v1
```

Both input and output paths must resolve beneath this checkout's private
`research/outputs/`; no existing output is replaced. The input is read once and
left unchanged. A synthetic report requires `--synthetic-fixtures` and receives
an explicit **SYNTHETIC FIXTURE — NOT STUDY RESULTS** heading. The default PNG
resolution is 180 dpi; `--dpi` accepts 72–600. Figure dimensions, colors, displayed
summaries, scale limits, dependency versions, input/code SHA-256 hashes, comparison
plan/code hashes when present, and PNG/SVG hashes are retained in the receipt.
Only a separately reviewed aggregate should later be copied for publication.

Use `--analysis-label "Reviewed semantic scores; original-format failures retained"`
to distinguish an export with an explicit subtitle. The label is optional, limited
to 100 printable characters on one line, and saved verbatim in the receipt's
options. It is never inferred from outcomes and changes no score or display scale.
The figure footnote distinguishes S-014/S-015 semantic verdict scores from
strict-format compliance and adjudications, which remain in the source report.

The four panels are fixed before results are inspected:

- S-013: all-four-field structured accuracy for all five source conditions, both
  models, on a fixed 0–1 axis. Dots are the retained equal-episode means. No
  binomial intervals are invented; the figure intentionally omits S-013 intervals.
- S-014: retained within-model self-minus-observer Brier loss for correct verdict.
- S-015: retained delayed original-minus-notebook scenario-conclusion recovery.
- S-016: retained full-minus-concise-padded phrase occurrences per 1,000 prose
  words. This is the mean of per-response rates with equal episode weights,
  never a pooled-word rate or a quality score.

Contrast panels draw the retained episode-bootstrap interval endpoints directly,
including asymmetric, degenerate, or mean-excluding intervals. Each panel has its
own symmetric scale covering its estimates and intervals, with a zero reference.
An entirely missing or zero contrast uses ±0.1 (S-014/S-015) or ±1 (S-016).
Missing estimates get text and no point; an available estimate with a null interval
is labeled “interval unavailable.” Every condition/model shows valid episode–seed
pairs out of 24, contributing episodes out of 12, and unavailable pair counts.
For S-013, a “pair” is one episode–seed observation in that condition, not a paired
arm difference. For other panels it requires both arms at that episode and seed.

The generator validates the frozen models, splits, source-declared episode IDs,
condition/contrast identities, ranges, and denominator arithmetic. It trusts the
comparison helper's estimates and provenance; it does not reverify scoring or the
raw runs. No optional cross-model estimate, marginal arm subtraction, p-value,
superiority annotation, or outcome-selected subset is plotted. Twelve constructed
episode clusters per study are reused across models; they are not independent new
cases. Seeds cluster within episodes, case-family dependence is not additionally
modeled, and the descriptive intervals do not establish population inference.
S-015 uses each model's own reviewed memories; no execution or private-state claim
follows from these endpoints.

Run the focused synthetic checks with:

```sh
python -m unittest tests.test_introspection_matched_figure -v
```

Data/path checks use only the standard library. Rendering checks run when
Matplotlib is available and are explicitly skipped otherwise. The synthetic
fixture builder lives in the test source; it contains no experimental results.
Matplotlib API references: [horizontal segments](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.hlines.html)
and [PNG/SVG export](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.savefig.html).
