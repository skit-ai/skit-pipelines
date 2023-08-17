SHELL := /bin/bash
.PHONY: all test secrets compile_pipes pipes docs dev start_server

BASE := skit_pipelines/pipelines
BLANK := 
SOURCE_FILES := $(shell find ${BASE} -name "__init__.py" ! -wholename "${BASE}/__init__.py")

CURRENT_TAG=$(shell git describe --tags --abbrev=0)
NEW_TAG=$(shell echo $(CURRENT_TAG) | awk -F. '{$$NF=$$NF+1;} 1' | sed 's/ /./g')
CHANGELOG=$(shell git log $(CURRENT_TAG)..HEAD --oneline --pretty=format:%s | sed -e 's/^/- [x] /' | sed -e '1s/^/\n$(NEW_TAG)\n/' | awk -v ORS='\\n' '1')

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
	@cat pipeline_secrets/env.sh >> secrets/env.sh

compile_pipes:
	@if [ -d "build" ]; then rm -rf build/**; fi
	@for file in $(SOURCE_FILES); do \
		pipeline_file=$${file/skit_pipelines\/pipelines\/}; \
		pipeline_name=$${pipeline_file/\/__init__.py/}; \
		echo "Building $$pipeline_name"; \
		touch build/$$pipeline_name.yaml; \
		source secrets/env.sh && dsl-compile --py $$file --output build/$$pipeline_name.yaml; \
	done

dev:
	@source secrets/env.sh && ./docker_build_dev_image $(tag)

us_dev:
	@source pipeline_secrets/us_env.sh && ./us_docker_build_dev_image $(tag)

docs:
	@source secrets/env.sh && sphinx-apidoc -f -o source ./skit_pipelines
	@source secrets/env.sh && sphinx-build -b html source docs

start_server:
	@source secrets/env.sh && task serve

commit:
	@git add .
	@git commit -m "$(msg)"

changelog:
	@sed -i -e "2s/^/$(CHANGELOG)/" CHANGELOG.md; if [ -f "CHANGELOG.md-e" ]; then rm CHANGELOG.md-e; fi
	@sed -e "1s/^version.*/$(NEW_TAG)/;t" -e "1,/^version.*/s//version = \"$(NEW_TAG)\"/" pyproject.toml >> temp.toml; mv temp.toml pyproject.toml

release:
	# @make changelog; echo "Changelog updated.."
	@make commit msg="update: $(NEW_TAG)"
	@git tag $(NEW_TAG); echo "Tagged $(NEW_TAG)"
	@git push origin main $(NEW_TAG); echo "Pushed $(NEW_TAG), please check - https://github.com/skit-ai/skit-pipelines"

pipes: secrets compile_pipes
all: lint pipes docs
