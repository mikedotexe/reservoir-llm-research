# Try the research CLI offline

From a fresh checkout, index two [synthetic journal files](examples/getting-started/README.md),
search a phrase, inspect its original text, and export a small reading pack.
This demonstrates the tools with invented data; it makes no finding about Astrid
or Minime. It needs no private corpus, app bundle, model, account, or network.

Use a macOS or Linux shell and an installed **Python 3.12 or later**, built with
SQLite FTS5 and able to load the system's `America/Los_Angeles` timezone data.
The preflight below checks these requirements before creating files. No package
installation is needed: running `-m reservoir_research` from the repository root
uses the source checkout. `-S` excludes site packages; this route uses only the
Python standard library.

## Run the walkthrough

Open a terminal in the repository root, the directory containing `pyproject.toml`.
Copy the whole block below. If `python3` is older than 3.12, change the `PYTHON`
assignment to your compatible executable, such as `python3.14`. A failed preflight
means you need a compatible local Python before continuing.

```sh
(
set -eu
PYTHON=python3

"$PYTHON" -B -S - <<'PY'
import sqlite3
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

if sys.version_info < (3, 12):
    raise SystemExit("Use Python 3.12 or later; change the PYTHON assignment.")
if not Path("reservoir_research/__main__.py").is_file():
    raise SystemExit("Run this block from the repository root.")
with sqlite3.connect(":memory:") as connection:
    connection.execute("CREATE VIRTUAL TABLE check_fts USING fts5(text)")
ZoneInfo("America/Los_Angeles")
print("Python, SQLite FTS5, and timezone checks passed.")
PY

quickstart_dir=$("$PYTHON" -B -S -c 'import tempfile; print(tempfile.mkdtemp(prefix="reservoir-quickstart-"))')
printf 'Your fresh database and results: %s\n' "$quickstart_dir"

"$PYTHON" -B -S -m reservoir_research --db "$quickstart_dir/index.sqlite3" index \
  --source "minime=$PWD/research/examples/getting-started/minime" \
  --source "astrid=$PWD/research/examples/getting-started/astrid" \
  > "$quickstart_dir/index.json"

"$PYTHON" -B -S -m reservoir_research --db "$quickstart_dir/index.sqlite3" search \
  'paper lantern' > "$quickstart_dir/search.json"
cat "$quickstart_dir/search.json"

entry_id=$("$PYTHON" -B -S -c 'import json, sys; print(json.load(open(sys.argv[1]))[0]["id"])' "$quickstart_dir/search.json")
"$PYTHON" -B -S -m reservoir_research --db "$quickstart_dir/index.sqlite3" show \
  "$entry_id" --raw > "$quickstart_dir/show.json"

"$PYTHON" -B -S -m reservoir_research --db "$quickstart_dir/index.sqlite3" coverage \
  --output "$quickstart_dir/coverage.json" > "$quickstart_dir/coverage.stdout.json"

"$PYTHON" -B -S -m reservoir_research --db "$quickstart_dir/index.sqlite3" sample \
  --per-being 1 --context 0 --label 'Synthetic quickstart only' \
  --out "$quickstart_dir/reading" > "$quickstart_dir/sample.json"

printf '\nOpen these saved results in a text editor:\n%s\n%s\n%s\n' \
  "$quickstart_dir/show.json" "$quickstart_dir/coverage.json" \
  "$quickstart_dir/reading/reading-pack.md"
)
```

The block prints its fresh temporary directory. Every command uses that explicit
database, and the import names only the two example directories. It leaves the
checkout and any existing research index unchanged. Running the block again creates
a different temporary directory; keep the printed path if you want to revisit this run.
Temporary files are disposable and may be removed by your operating system.

## Read the result

- `index.json`: two files included, one from each synthetic source.
- `search.json`: one result with a full entry ID, a source path inside the example
  directory, and a snippet containing the invented “paper lantern” question.
- `show.json`: that same entry's `raw_text`, cleaned `body_text`, source hash, and
  metadata. Both the header and body identify it as synthetic.
- `coverage.json`: `counts.entries` is 2, `unknown_backend` is 2, and
  `exact_prompt_entries` and `generation_records` are 0. Imported text does not
  establish a model backend, prompt, or live event.
- `reading/reading-pack.md` and `reading/manifest.json`: both synthetic passages,
  a reproducible selection, and empty reader notes. The `minime` and `astrid` labels
  are parser categories here, not claims of authorship.

For more commands, run `python3 -B -S -m reservoir_research --help`, using the same
compatible Python as above. `--db` belongs **before** the command. Use explicit
sources when importing a chosen corpus; `index` without `--source` discovers
the sibling journal directories and is not part of this walkthrough.

## Go further with the right inputs

The tracked repository contains the toolkit, these synthetic fixtures, selected
reviewed examples, and written accounts. Locally retained evidence under
`research/outputs/`, the existing journal index, original sibling sources, and
machine-specific app paths are not supplied by a public checkout. A link to a
private receipt records where the evidence was retained; it is not a downloadable
input. Follow [Tools](TOOLS.md) for the interfaces and their evidence requirements.

Maintained daily replay needs an explicit sealed input manifest, its matching
report, and the retained files they bind. `verify --group research-replay` requires
`--daily-manifest` and `--daily-report`; relocated captures also need the appropriate
`--data-root`. `all-offline` includes that group and native app checks, so a checkout
alone cannot make it pass. Missing prerequisites are reported as incomplete.
Use the [daily pipeline instructions](TOOLS.md#maintained-daily-evidence-and-verification)
only when you have those retained inputs; they are not needed for this quickstart.

Model generation is separate and optional. This CLI walkthrough never invokes a
model or makes a network request. To explore the macOS app and its recorded examples,
see the [app build guide](../native/ReservoirScope/README.md) and
[current candidate status](CURRENT-RELEASE.md). Replaying recorded output does not
create a new model response.
