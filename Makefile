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
install:  ## Install deps
	poetry install --no-root
.PHONY: install

init:  ## Initialize project repository
	poetry run pre-commit autoupdate
	poetry run pre-commit install --install-hooks --hook-type pre-commit --hook-type commit-msg
.PHONY: init

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
# CI
# =============================================================================
ci: format lint scan test  ## Run all tasks
.PHONY: ci

format:  ## Run autoformatters
	poetry run ruff --fix .
	poetry run black .
.PHONY: format

lint:  ## Run all linters
	poetry run ruff check .
	poetry run black --check .
	poetry run mypy --show-error-codes --pretty .
.PHONY: lint

scan:  ## Run all scans
	poetry run checkov -d .
.PHONY: scan

test:  ## Run tests

.PHONY: test


# =============================================================================
# Helpers
# =============================================================================
clean:  ## Remove temporary files
	rm -rf .mypy_cache/ .ruff_cache/
	find . -path '*/__pycache__*' -delete
	find . -path "*.log*" -delete
.PHONY: clean
