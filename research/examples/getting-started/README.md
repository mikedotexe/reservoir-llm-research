# Synthetic journals for the CLI quickstart

These two files were written for the [offline CLI walkthrough](../../QUICKSTART.md).
They contain invented text and timestamps. Neither file is a Being's journal,
a model response, a telemetry capture, or evidence of a real event.

The parser accepts `minime` and `astrid` as source labels, so the examples use
those directory names and recognized journal headers. The labels exercise the
index format; they do not attribute the invented passages to either Being.
Each passage also carries its synthetic label in the body, so the label survives
cleaned-text search and reading-pack export.

- `minime/synthetic-moment.txt`: one invented question containing “paper lantern”.
- `astrid/synthetic-journal.txt`: one invented observation containing “blue window”.

Only these two `.txt` files are imported by the quickstart. No generation record,
backend, prompt, action, or telemetry evidence is supplied. Coverage should report
two prose entries, two unknown backends, and no exact prompts or generation records.
Those missing fields are intentional; successful indexing does not fill them in.
