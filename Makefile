SHELL := /bin/bash
.PHONY: all test pipes docs

BASE := skit_pipelines/pipelines
BLANK := 
SOURCE_FILES := $(shell find ${BASE} -name "__init__.py" ! -wholename "${BASE}/__init__.py")

lint:
	@echo -e "Running linter"
	@isort skit_pipelines
	@isort tests
	@black skit_pipelines
	@black tests
	@echo -e "Running type checker"

test: ## Run the tests.conf
	@pytest --cov=skit_pipelines --cov-report html --durations=5 --cov-report term:skip-covered tests/

clean:
	@if [ -d "secrets" ]; then rm -rf secrets; fi

update_secrets:
	@dvc get https://github.com/skit-ai/skit-calls secrets

pipes:
	@if [ -d "build" ]; then rm -rf build/**; fi
	@for file in $(SOURCE_FILES); do \
		echo "Building $$file"; \
		pipeline_file=$${file/skit_pipelines\/pipelines\/}; \
		pipeline_name=$${pipeline_file/\/__init__.py/}; \
		echo "Building $$pipeline_name"; \
		touch build/$$pipeline_name.yaml; \
		source secrets/env.sh && dsl-compile --py $$file --output build/$$pipeline_name.yaml; \
	done

temp_pipes:
	@for file in $(SOURCE_FILES); do \
		echo "Building skit_pipelines/pipelines/$$file.py"; \
		touch build/$$file.yaml; \
		source secrets/env.sh && dsl-compile --py skit_pipelines/pipelines/$$file.py --output build/$$file.yaml; \
	done
	
docs:
	@sphinx-apidoc -f -o source ./skit_pipelines
	@sphinx-build -b html source docs
	@cp source/index.rst README.rst

all: clean update_secrets pipes
