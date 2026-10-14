# Retained resource plot recipe

`plot_resources.py` uses the already available Matplotlib installation and the noninteractive Agg backend. It changes no dependencies and reads no process, service or app state. The actual capture has **not** been plotted by this preparation step.

After capture and markers are finalized, run from `desktop/ReservoirScope` with a new output filename:

```sh
python3 validation/2026-10-13-reliability-0.12.0/plot_resources.py \
  --input validation/2026-10-13-reliability-0.12.0/samples-01.jsonl \
  --markers validation/2026-10-13-reliability-0.12.0/ui-markers.jsonl \
  --output validation/2026-10-13-reliability-0.12.0/final-resources-01.png
```

A missing footer is rejected unless `--allow-incomplete` is supplied, in which case the figure is prominently labeled **INTERIM**. A present footer still displays its actual end status; it is not a reliability pass. The PNG contains the exact raw capture SHA-256. Record script and marker hashes alongside it, using the final analysis receipt. Output uses exclusive creation.

The three panels show main-PID RSS in MiB, main-PID interval-average CPU percent (100% is one core), and selected-owned-directory logical/allocated bytes in MiB. Elapsed minutes start at sampler admission, not Start or numerical step zero. Dashed markers are operator-declared phases. Missing process measurements, excessive sample gaps and incomplete/scheduled-missing disk scans break the plotted lines; ordinary nonscan intervals between the once-per-minute disk measurements are expected. CPU points are interval averages shown at their endpoints, not instantaneous utilization.

This is an unfiltered raw-resource figure. It does not remove documented developer-test load, establish continuous UI minimization, quantify GPU/energy, include shared WebKit/fixture/sampler processes or establish memory leaks. Pair it with the full and load-excluded summaries from `analyze_run.py`, using the frozen resource investigation criteria. The stored footprint differs from volume-wide free-space changes and APFS unique physical allocation.

Three synthetic segmentation tests passed; the retained sanity image `resource-plot-synthetic-sanity-01.png` was inspected for legibility and correct unconnected gaps. It is deliberately labeled synthetic test data and missing-footer interim, and contains **no application measurements**. Exact commands, script/test/image hashes and the small background-load interval are in `resource-plot-01-qualification.json`. Earlier test receipts remain unchanged.
