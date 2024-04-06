#!/usr/bin/env -S make -f

MAKEFLAGS += --warn-undefined-variable
MAKEFLAGS += --no-builtin-rules

-include Makefile.*

SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
.DEFAULT_GOAL := help

help: Makefile  ## Show help
	for makefile in $(MAKEFILE_LIST)
	do
		@echo "$${makefile}"
		@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' "$${makefile}" | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'
	done


# =============================================================================
# Common
# =============================================================================
install:  ## Install the app locally
	poetry install
	pre-commit install --install-hooks
.PHONY: install

update:  ## Update deps and tools
	poetry update
	pre-commit autoupdate
.PHONY: update

LOCUSTFILE = ./environments/tcp/locustfile.py
LOCUST_ARGS =
LOCUST_WORKERS = 10
run:  ## Start Locust
	docker compose run --rm \
		-p 127.0.0.1:8089:8089 \
		-e LOCUSTFILE="$(LOCUSTFILE)" \
		-e LOCUST_ARGS="$(LOCUST_ARGS)" \
		-e LOCUST_WORKERS="$(LOCUST_WORKERS)" \
		workspace \
		./scripts/run-locust.sh
.PHONY: run


# =============================================================================
# Helpers
# =============================================================================
clean:  ## Remove temporary files
	rm -rf .mypy_cache/ .ruff_cache/
	find . -path '*/__pycache__*' -delete
	find . -path "*.log*" -delete
.PHONY: clean
