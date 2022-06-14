SHELL := /bin/bash
.PHONY: all test secrets compile_pipes pipes docs dev dev_image

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

secrets:
	@if [ -d "secrets" ]; then rm -rf secrets; fi
	@dvc get https://github.com/skit-ai/skit-calls secrets
	@dvc pull
	@cat env.sh >> secrets/env.sh

compile_pipes:
	@if [ -d "build" ]; then rm -rf build/**; fi
	@for file in $(SOURCE_FILES); do \
		pipeline_file=$${file/skit_pipelines\/pipelines\/}; \
		pipeline_name=$${pipeline_file/\/__init__.py/}; \
		echo "Building $$pipeline_name"; \
		touch build/$$pipeline_name.yaml; \
		source secrets/env.sh && dsl-compile --py $$file --output build/$$pipeline_name.yaml; \
	done

dev_image:
	@source secrets/env.sh && ./docker_build_dev_image master

docs:
	@source secrets/env.sh && sphinx-apidoc -f -o source ./skit_pipelines
	@source secrets/env.sh && sphinx-build -b html source docs
	@cp source/index.rst README.rst

dev: dev_image compile_pipes
pipes: secrets compile_pipes
all: lint pipes docs
