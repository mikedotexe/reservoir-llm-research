# Reading work: normalized background-load intervals

Six closed UTC envelopes are retained in `load-intervals-01/`. Their flat index, exact original-source hashes, timestamp pointers and coverage limitations are in [load-intervals-01.json](load-intervals-01.json). The originals are unchanged. The index itself is not accepted by the existing analyzer; pass each envelope as a separate `--load-receipt`.

| Work | Start UTC | End UTC |
| --- | --- | --- |
| journal-focused-01 | 2026-10-13T18:10:35.838072Z | 2026-10-13T18:10:36.771293Z |
| journal-focused-02 | 2026-10-13T18:11:12.549514Z | 2026-10-13T18:11:13.069353Z |
| setup-checks-01 | 2026-10-13T18:12:58.937318Z | 2026-10-13T18:13:02.223816Z |
| integrated-01 | 2026-10-13T18:14:42.891838Z | 2026-10-13T18:14:46.390795Z |
| owned-preview | 2026-10-13T18:16:59.981049Z | 2026-10-13T18:21:02.432561Z |
| integrated-02 | 2026-10-13T18:21:34.819000Z | 2026-10-13T18:21:39.229833Z |

The setup interval is the union of overlapping test and TypeScript processes at `checks[0]` and `checks[1]`. Its end is **18:13:02.223816 UTC**, not the later **18:13:37.966435 UTC** top-level receipt capture. Failed checks remain documented load. Preview start/end values agree with the two retained preview receipts and PID 70308. Open start receipts are not duplicated. Point-only edit/model-selection metadata does not establish another closed execution interval.

The six nonoverlapping envelopes total **255.100860 seconds**. This does not account for every source edit, browser/editor operation, thermal/cache effect or other host workload. Exclusion remains a resource sensitivity analysis; functional progress, missing rows, stalls and errors must stay unfiltered.

## Final command, after capture is closed

The following command adds these six intervals to the prior closed receipt list explicitly named by `FINAL-ANALYSIS-WORKFLOW.md`. Its arguments were checked for the analyzer's top-level timestamp contract. Add any other subsequently retained closed load intervals; this is not a claim that the list covers all host activity. Use a new output filename if this one already exists. Run the separate raw, unfiltered analysis first as specified by that workflow.

```sh
python3 validation/2026-10-13-reliability-0.12.0/analyze_run.py \
  --input validation/2026-10-13-reliability-0.12.0/samples-01.jsonl \
  --markers validation/2026-10-13-reliability-0.12.0/ui-markers.jsonl \
  --load-receipt validation/2026-10-13-reliability-0.12.0/publisher-final-01-qualification.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/sampler-analysis-02-qualification.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/natural-quota-01-command.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/frontend-final-load-02.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/frontend-final-load-03.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/quota-repair-final-01-qualification.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/quota-repair-final-02-qualification.json \
  --load-receipt validation/2026-10-13-reading-0.12.1/load-intervals-01/journal-focused-01.json \
  --load-receipt validation/2026-10-13-reading-0.12.1/load-intervals-01/journal-focused-02.json \
  --load-receipt validation/2026-10-13-reading-0.12.1/load-intervals-01/setup-checks-01.json \
  --load-receipt validation/2026-10-13-reading-0.12.1/load-intervals-01/integrated-01.json \
  --load-receipt validation/2026-10-13-reading-0.12.1/load-intervals-01/owned-preview.json \
  --load-receipt validation/2026-10-13-reading-0.12.1/load-intervals-01/integrated-02.json \
  --output validation/2026-10-13-reliability-0.12.0/final-phase-analysis-reading-01.json
```

Do not use this command to label a growing capture final. The existing analyzer requires a footer unless explicitly requested as interim; do not add `--allow-incomplete` for the final report. This metadata task did not read the sampler or markers, run tests, launch/control an app or contact a provider.
