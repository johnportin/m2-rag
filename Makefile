UV ?= uv
PY := $(UV) run python
K ?= 5

.PHONY: install data parser test

install:
	$(UV) sync

data:
	$(PY) src/scripts/get_data.py

parser:
	$(PY) src/scripts/run_parser.py

test:
	$(UV) run pytest

query-embed:
	$(PY) -m src.cli.query_index "$(Q)" -k $(K)

query-ms:
	$(PY) -m src.cli.query_ms_index "$(Q)" -k $(K)

rag-query:
	$(PY) -m src.cli.rag_query --query "$(Q)"

judge:
	$(PY) scripts/run_judged_prompts.py --input input/judged_prompts.json