.PHONY: help install test lint run-eval report dashboard db-up db-down build-sandbox

# Default values (override with: make run-eval LAYER=L2 COUNT=5)
ADAPTER ?= craycode
COMMAND ?=
LAYER   ?= L1
COUNT   ?= 5
SEED    ?=
AGENT   ?= craycode
OUTPUT  ?= reports/report.md

help:
	@echo "Coding Agent Evaluation Framework"
	@echo ""
	@echo "  make install        Install dependencies"
	@echo "  make test           Run all tests"
	@echo "  make lint           Run linting"
	@echo "  make db-up          Start PostgreSQL"
	@echo "  make db-down        Stop PostgreSQL"
	@echo "  make build-sandbox  Build Docker sandbox images"
	@echo "  make run-eval       Run evaluation (LAYER=L1 COUNT=10)"
	@echo "  make report         Generate report"
	@echo "  make dashboard      Start Streamlit dashboard"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

test-unit:
	python -m pytest tests/unit/ -v --tb=short

test-integration:
	python -m pytest tests/integration/ -v --tb=short

lint:
	ruff check eval_framework/

db-up:
	docker-compose up -d

db-down:
	docker-compose down

build-sandbox:
	cd eval_framework/sandbox/dockerfiles && \
	docker build -t eval-sandbox-python:latest -f python.Dockerfile . && \
	docker build -t eval-sandbox-node:latest -f node.Dockerfile . && \
	docker build -t eval-sandbox-go:latest -f go.Dockerfile .

run-eval:
	PYTHONUTF8=1 python -m eval_framework.cli run \
		--adapter $(ADAPTER) \
		$(if $(COMMAND),--command "$(COMMAND)",) \
		--layer $(LAYER) \
		--count $(COUNT) \
		$(if $(SEED),--seed $(SEED),)

# ── Full pipeline ─────────────────────────────────────────

full-eval:       ## Quick: L1=10 L2=2 L3=skip (≈10 min)
	bash run_full_eval.sh --adapter $(ADAPTER) --quick

full-eval-full:  ## Complete: L1=50 L2=8 L3=5 (needs API key, ≈2-4h)
	bash run_full_eval.sh --adapter $(ADAPTER)

report:
	PYTHONUTF8=1 python -m eval_framework.cli report --agent $(AGENT) --output $(OUTPUT)

dashboard:
	streamlit run eval_framework/dashboard/app.py

test-eval:       ## Reset + Full Eval + Report (one command, needs API key)
	bash run_full_eval.sh --adapter $(ADAPTER) --reset
