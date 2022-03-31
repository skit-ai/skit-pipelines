SHELL := /bin/bash
.PHONY: all test build

SOURCE_FILES := $(shell find skit_pipelines/pipelines ! -name "__init__.py" -name "*.py" -execdir basename {} .py ';')

lint:
	@echo -e "Running linter"
	@isort skit_pipelines
	@isort tests
	@black skit_pipelines
	@black tests
	@echo -e "Running type checker"

test: ## Run the tests.conf
	@pytest --cov=skit_pipelines --cov-report html --durations=5 --cov-report term:skip-covered tests/

build:
	@for file in $(SOURCE_FILES); do \
		echo "Building skit_pipelines/pipelines/$$file.py"; \
		touch build/$$file.yaml; \
		source env.sh && dsl-compile --py skit_pipelines/pipelines/$$file.py --output build/$$file.yaml; \
	done

all: lint build
