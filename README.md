# m2-rag
A retrieval-augmented agent for the Macaulay2 mathematical research language. The goal is to let users ask natural-language questions about M2 and get grounded answers with citations.

The agent uses these tools:
- `search_docs`: semantic search over structured Macaulay2 docs (or chunked text if `M2_INDEX_MODE=chunks`).
- `summarize_docs`: condenses multiple search hits into a brief summary.
- `search_wikipedia`: fallback for general background when the M2 docs have no hits (Wikipedia references include full URLs).

## Setup (with uv)

This project targets Python 3.12+ and uses [uv](https://docs.astral.sh/uv) to manage the virtual environment defined in `pyproject.toml`/`uv.lock`.

1) Install uv (one-time):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2) Create the local env and install deps:

```bash
uv sync
```

This creates `.venv/` in the repo. You can run commands through uv without manual activation, e.g. `uv run python -m src.main "your query"`.

If you prefer an activated shell:
- PowerShell: `.\.venv\Scripts\Activate.ps1`
- cmd.exe: `.\.venv\Scripts\activate.bat`
- bash/zsh: `source .venv/bin/activate`

## Running the project

This section contains the details needed to run the project from scratch

### Downloading data

Run the `get_data.py` script to download the documents from the M2 GitHub repository.

```bash
uv run python src/scripts/get_data.py
```

### Parsing data

The data comes in raw `.m2` files, a format which is not often worked with outisde of the small world of commutative algebra research. Thus we have a custom parser for these documents. To parse all files, run:

```bash
uv run python src/scripts/run_parser.py
```

### Chunked docs for embeddings

If you want to try a simpler chunked approach (raw text chunks instead of structured fields), first build chunks:

```bash
uv run python src/scripts/chunk_docs.py --root data/macaulay2docs --output data/m2_chunks.jsonl
```

Then use `--index-mode chunks` when running the agent/CLIs to search the chunk index instead of the structured doc index (no need to set env vars). If you omit `--index-mode`, the default is `chunks`:

```bash
uv run python -m src.main "How do I define a monomial ideal?" --index-mode chunks
```

You can also query the indexes directly:

```bash
uv run python -m src.cli.query_index "hilbert polynomial" -k 5 --show-scores        # FAISS docs
uv run python -m src.cli.query_ms_index "hilbert polynomial" -k 5 --show-scores     # Minsearch docs
uv run python -m src.cli.query_chunk_index "hilbert polynomial" -k 5 --show-scores  # Chunked text
```

## Using the Agent

Set `OPENAI_API_KEY`, then run prompts using the commands in the `Makefile`. 

### Querying

You can  run a one-off query using the Makefile target (defaults to `--index-mode chunks` and uses the `QUERY` variable):

```bash
make rag-query QUERY="What is a hilbert polynomial?"
```

This wraps `uv run python -m src.main ...` for convenience.

## Running judged prompt sweeps

Simply run

```bash
make judge
```
to run the judge against all prompts in `input/judged_prompts.json`. 

Alternatively, for more control, you are able to use the following cli:
```bash
uv run python scripts/run_judged_prompts.py --prompt "What is a monomial ideal?" --index-mode chunks
```

You can also pass `--input prompts.json` where the file contains `["prompt1", "prompt2"]`.
Results are saved to `output/judged_prompts_<timestamp>.jsonl` by default, and each entry
records the agent answer, references, tool events, and the judge verdict.
