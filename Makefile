.PHONY: all test

lint:
	@echo -e "Running linter"
	@isort skit_pipelines
	@isort tests
	@black skit_pipelines
	@black tests
	@echo -e "Running type checker"

typecheck:
	@mypy -p skit_pipelines

test: ## Run the tests.conf
	@pytest --cov=skit_pipelines --cov-report html --durations=5 --cov-report term:skip-covered tests/

all: lint typecheck test docs
