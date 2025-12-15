## Evaluation Outline

### Problem Description

Getting started in math reserach can be difficult for incoming graduate students. In commutative algebra, having access to software to explore conjectures and come up with examples is important. The Macaulay2 (M2) programming language was built for that purpose. However, the [documentation](https://macaulay2.com/doc/Macaulay2/share/doc/Macaulay2/Macaulay2Doc/html/) is not always straight forward. The purpose of this RAG agent is to assist new (and experienced) researcers in understanding M2 so they can quickly test conjectures and experiment. 

### Knowledge Base and Retrieval

The [documentation files for M2](https://github.com/Macaulay2/M2/tree/stable/M2/Macaulay2/packages/Macaulay2Doc) can be found its Github.

- Three retrieval backends were tested:
  - Chunked text embeddings/index over raw chunks (`src.cli.query_chunk_index`, toggled with `M2_INDEX_MODE=chunks`).
  - FAISS embeddings over structured docs (`src.cli.query_index` / `search_docs` default).
  - Minsearch text index over structured docs (`src.cli.query_ms_index`).
- Evaluation: manual spot-checks on common M2 questions (Hilbert polynomial, Krull dimension, monomial ideals) comparing top-5 hits from each backend. The chunked index consistently surfaced the most on-topic snippets (fewer irrelevant prefatory lines, clearer code-context), so it is the preferred mode and is what we use when `M2_INDEX_MODE=chunks` is set.

At first, the source files seem to be highly structured. However, there are actually two different structures used for the formatting: one relies on whitespace/newlines to delimit sections, and the other uses explicit parentheses for grouping. My first approach was to use a parser that would extract the different parts of the text. However, several things got in the way, such as nested pages and page redirects. Because of this, the quality of the parsed data was substandard.

With the parsed data, I constructed two indexes using minsearch and FAISS embeddings. These would sometimes reference the correct documentation, but often failed to find the relevant passages needed to answer a query. In the end, the parsed documentation simply wasn't good enough for these methods. 

Chunking requires little preprocessing, and with large enough chunk sizes, keeps all the relevant information together. The solution to the bad parsing was to simply embed chunks. The chunks were embedded with a token size of 200 and an overlap of 40 tokens. The chunking technique turned out to experimentally provide the best results, and so is used for the final version.

The other indexes can be used for experimentation purposes, and are still exposed through the CLI. See `README.md` for further information. 

### Agents and LLM

The LLM used for the development of this project is provided by OpenAI. Defined in `src/agents/rag_agent.py`, the model is defined as `gpt-4o-mini`. This can be modified if the user wishes to expand the capabilities of the agent. However, I have found that such a small and inexpensive model is sufficient for the current scope of the project.

This agent is given three tools: 
- `search_docs`: This tool is used to query the provided database (usually the chunked embedding)
- `summarize_docs`: This tool is used to summarize the results from search_docs. Since search_docs can return multiple chunks which may or may not be related, summazrize tool is used to bring those results together into a coherent chunk. 
- `search_wikipedia`: To augment the agents capabilities, I have given it access to wikipedia incase it needs to learn more about math concepts to answer the questions. 
  
All three of these tools are used in conjunction to provide detailed and coherent mathematical examples with M2 code. Experimentally, I have found that adding the `search_wikipedia` tool has improved the depth of the responses by allowing the agent to provide more context to its answers, and also using the given wikpedia results to further query the documentation. 

### Code Organization

```
src/
|-- agents/       rag_agent, judge_agent, validators
|-- tools/        search_docs, summarize_docs, search_wikipedia, etc.
|-- db/           FAISS embedding index, minsearch text index, chunked index helpers
|-- cli/          CLI entrypoints + shared search runner
|-- scripts/      data prep (download, parse, chunk)
tests/            unit and judge tests
data/             corpora (parsed docs, chunks)
input/            prompt inputs (evaluation/judge)
output/           saved query/judge outputs
README.md         project overview and usage
```

### Testing

- Unit tests cover tools, indexes, and CLI helpers (see `tests/test_tools.py`, `tests/test_db_index.py`, `tests/test_cli_query_index.py`, `tests/test_cli_ms_index.py`, etc.).
- Judge-style tests validate the evaluator agent behavior (see `tests/test_judge_agent.py` for structured verdict checks).
- To run all tests: `make test` (invokes `uv run pytest`).

### Evaluation

- LLM-based evaluation: `scripts/run_judged_prompts.py --input input/judged_prompts.json` runs the RAG agent on each prompt and passes the answer/references/tool trace to the judge agent, which returns a structured verdict (`decision`, `score`, `rationale`). Outputs are saved to `output/judged_prompts_<timestamp>.jsonl`.
- The prompt set in `input/judged_prompts.json` (10 **hand-curated** questions) exercises docs knowledge, language specifics, and math tasks.

### Monitoring

Logs for each run at appended to `logs/judge.jsonl`. They contain information that one might want to eventually add to a dashboard for real-time monitoring. 

### Reproducibility

### Best Coding Practices

Makefile: There is a makefile that makes running things easier: 1 point
Dependency management and virtual environment: UV or a similar tool is used: 1 point

### Additional Bonus Points
A simple CLI has been implemented that the user can use to make queries with this agent. For example usage, see the `README.md`. 
