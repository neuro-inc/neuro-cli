DEVPI_URL ?= "https://$(DEVPI_USER):$(DEVPI_PASS)@$(DEVPI_HOST)/$(DEVPI_USER)"

SHELL := /bin/bash
BRANCH := $(shell git branch | grep \* | cut -d ' ' -f2)

MYPY_CACHE_DIR=.mypy_cache/$(shell md5sum setup.py | awk '{print $$1}')-$(shell find requirements -type f -exec md5sum {} \; | sort -k 2 | md5sum | awk '{print $$1}')

ISORT_DIRS := neuromation tests build-tools
ISORT_REGEXP := ^python/(neuromation|tests|build-tools)/.+\\.py
BLACK_DIRS := $(ISORT_DIRS)
BLACK_REGEXP := $(ISORT_REGEXP)
MYPY_DIRS :=  neuromation
MYPY_REGEXP := ^python/+.\\py
FLAKE8_DIRS := .
FLAKE8_REGEXP := ^python/.+\\.py

DEPS_REGEXP := ^python/(requirements/.+|setup.py+)

.PHONY: help
.SILENT: help
help:
	echo -e "Available targets: \n\
	* Common: \n\
	- help: this help \n\
	- init: initialize project for development \n\
	- update-deps: install.update all development dependencies \n\
	- release: Generate changelog and tag new version \n\
	  example: make release VERSION=0.5 \n\
	- dist-clean: remove files generated during publish \n\
	- clean: remove generated files \n\
	- update-deps-fast: update deps only if requirements changed betwwen two points(hook)\
\n\
	* Modifications and generations: \n\
	- format: format python code(isort + black) \n\
	- docs: generate docs \n\
	- changelog: generate and commit changelog \n\
	  example: make changelog VERSION=0.5 \n\
\n\
	* Lint (static analysis) \n\
	- lint: run linters(isort, black, flake8, mypy, lint-docs) \n\
	- lint-docs: validate generated docs \n\
	- lint-diff: lint only modified files, between two points(hook) \n\
	- publish-lint: lint distribution \n\
\n\
	* Tests \n\
	- test: run usual(not e2e) tests \n\
	- e2e: run e2e tests \n\
	- test-all: run all tests \n\
	- test-fast: run usual test for modified from latest execution files \n\
	  example: make lint diff FROM=e2d9e591f6d413588b4d4a0af0a3aa066a0ae8eb TO=a0a5b84e31c7d36d2c440d3707d25fc0ef567a61 \n\
\n\
	* Distribution \n\
	- dist: generate python distribution(wheel) \n\
	- publish: publish distribution to pypi index \n\
\n\
	* CI \n\
	- coverage: upload coverage information to codecov.io \n\
	- ci: run CI related targets \n\
    "

.PHONY: init
init: _init-readme update-deps
	cp .hooks/* ../.git/hooks
	chmod a+x ../.git/hooks/*
	rm -rf .mypy_cache

_init-readme:
	cp -n README.in.md README.md

.PHONY: e2e
e2e:
	pytest \
	    -n auto --forked \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: _e2e
_e2e:
	pytest \
	    -n auto --forked \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		--cov-append \
		tests

.PHONY: _e2e_win
_e2e_win:
	pytest \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		--cov-append \
		tests


.PHONY: test
test:
	pytest \
	    -n auto \
		-m "not e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: test-fast
test-fast:
	pytest \
			--quiet \
			--testmon --tlf \
			-m "not e2e" \
			tests || test $$? -eq 5

.PHONY: test-all
test-all:
	pytest \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: lint
lint: lint-docs
	isort -c -rc ${ISORT_DIRS}
	black --check $(BLACK_DIRS)
	mypy --cache-dir $(MYPY_CACHE_DIR) $(MYPY_DIRS)
	flake8 $(FLAKE8_DIRS)

.PHONY: lint-diff
lint-diff: ISORT_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(ISORT_REGEXP)") print substr($$NF, 8)}')
lint-diff: BLACK_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(BLACK_REGEXP)") print substr($$NF, 8)}')
lint-diff: MYPY_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(MYPY_REGEXP)") print substr($$NF, 8)}')
lint-diff: FLAKE8_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(FLAKE8_REGEXP)") print substr($$NF, 8)}')
lint-diff:
	@ [ -z "${ISORT_TARGETS}" ] || (echo "Lint isort:"; echo "   ${ISORT_TARGETS}" && isort -c -rc ${ISORT_TARGETS})
	@ [ -z "${BLACK_TARGETS}" ] || (echo "Lint black:"; echo "   ${BLACK_TARGETS}" && black -q --check ${BLACK_TARGETS})
	@ [ -z "${MYPY_TARGETS}" ] || (echo "Lint mypy:"; echo "   ${MYPY_TARGETS}" && mypy --cache-dir $(MYPY_CACHE_DIR) ${MYPY_TARGETS})
	@ [ -z "${FLAKE8_TARGETS}" ] || (echo "Lint flake8:"; echo "   ${FLAKE8_TARGETS}" && flake8 ${FLAKE8_TARGETS})


.PHONY: dist-clean
dist-clean:
	rm -rf dist || true
	rm -rf build || true

.PHONY: dist
dist: dist-clean
	python setup.py bdist_wheel

.PHONY: publish-lint
publish-lint:
	twine check dist/*


.PHONY: publish
publish: dist publish-lint
	twine upload dist/*

.PHONY: coverage
coverage:
	$(SHELL) <(curl -s https://codecov.io/bash) -X coveragepy

.PHONY: format
format:
	isort -rc $(ISORT_DIRS)
	black $(BLACK_DIRS)
	# generate docs as the last stage to allow reformat code first
	make docs

# TODO (artyom, 07/16/2018): swap e2e and test once coverage output
# of both is combined. Otherwise e2e will override unit tests with
# lower coverage
.PHONY: ci
ci: lint test _e2e coverage

.PHONY: clean
clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm README.md
	rm -rf .testmondata .tmontmp .mypy_cache .pytest_cache

devpi_setup:
	pip install devpi-client
	pip install wheel
	@devpi use $(DEVPI_URL)/$(DEVPI_INDEX)

devpi_login:
	@devpi login $(DEVPI_USER) --password=$(DEVPI_PASS)

devpi_upload: devpi_login
	devpi upload --formats bdist_wheel

.PHONY: docs
docs:
	build-tools/cli-help-generator.py README.in.md README.md
	markdown-toc -t github -h 6 README.md


.PHONY: lint-docs
lint-docs: TMP:=$(shell mktemp $${TMPDIR:-/tmp}/README.XXXXXXXX.md)
lint-docs:
	build-tools/cli-help-generator.py README.in.md ${TMP}
	markdown-toc -t github -h 6 ${TMP}
	diff -q ${TMP} README.md

.PHONY: update-deps
update-deps:
	pip install --disable-pip-version-check -r requirements/dev.txt

.PHONY: changelog
changelog:
	echo "Read RELEASE.md for release process instructions"

.PHONY: release
release:
	echo "Read RELEASE.md for release process instructions"

.PHONY: update-deps-fast
update-deps-fast: REQUIREMENTS_CHANGED:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(DEPS_REGEXP)") print substr($$NF, 8)}')
update-deps-fast:
	@ [ -z "${REQUIREMENTS_CHANGED}" ] || (make update-deps)
