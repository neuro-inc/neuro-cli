SHELL := /bin/bash

ISORT_DIRS := neuromation tests build-tools setup.py
BLACK_DIRS := $(ISORT_DIRS)
MYPY_DIRS :=  neuromation tests
FLAKE8_DIRS := $(ISORT_DIRS)

PYTEST_XDIST_NUM_THREADS ?= auto

.PHONY: help
.SILENT: help
help:
	echo -e "Available targets: \n\
	* Common: \n\
	- help: this help \n\
	- init: initialize project for development \n\
	- update-deps: install.update all development dependencies \n\
	- clean: remove generated files \n\
\n\
	* Modifications and generations: \n\
	- fmt: format python code(isort + black) \n\
	- docs: generate docs \n\
	  example: make changelog VERSION=0.5 \n\
\n\
	* Lint (static analysis) \n\
	- lint: run linters(isort, black, flake8, mypy, lint-docs) \n\
	- lint-docs: validate generated docs \n\
	- publish-lint: lint distribution \n\
\n\
	* Tests \n\
	- test: run usual(not e2e) tests \n\
	- e2e: run e2e tests \n\
	- test-all: run all tests \n\
\n\
        * API-DOC \n\
        - api-doc: generate sphinx html docs \n\
        - api-doc-spelling: check dockumentation spelling \n\
    "

.PHONY: init
init: _init-readme update-deps
	rm -rf .mypy_cache

_init-readme:
	cp -n README.in.md README.md

.PHONY: update-deps
update-deps:
	pip install -r requirements/dev.txt
	touch .update-deps

.update-deps: $(shell find requirements -type f)
	pip install -r requirements/dev.txt
	touch .update-deps

.PHONY: e2e
e2e: .update-deps
	pytest \
	    -n ${PYTEST_XDIST_NUM_THREADS} \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		--verbose \
		--durations 10 \
		tests

.PHONY: e2e-jobs
e2e-jobs: .update-deps
	pytest \
	    -n ${PYTEST_XDIST_NUM_THREADS} \
		-m "e2e and e2e_job" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		--verbose \
		--durations 10 \
		tests

.PHONY: e2e-sumo
e2e-sumo: .update-deps
	pytest \
	    -n ${PYTEST_XDIST_NUM_THREADS} \
		-m "e2e and not e2e_job" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		--verbose \
		--durations 10 \
		tests


.PHONY: test
test: .update-deps
	pytest \
		-m "not e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: test-all
test-all: .update-deps
	pytest \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: lint
lint: lint-docs
	isort -c -rc ${ISORT_DIRS}
	black --check $(BLACK_DIRS)
	mypy $(MYPY_DIRS)
	flake8 $(FLAKE8_DIRS)

.PHONY: publish-lint
publish-lint:
	twine check dist/*


.PHONY: format fmt
format fmt:
	isort -rc $(ISORT_DIRS)
	black $(BLACK_DIRS)
	# generate docs as the last stage to allow reformat code first
	make docs

.PHONY: clean
clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm README.md

.PHONY: docs
docs:
	build-tools/cli-help-generator.py README.in.md README.md
	markdown-toc -t github -h 6 README.md


.PHONY: lint-docs
lint-docs: TMP:=$(shell mktemp -d)/README.md
lint-docs:
	build-tools/cli-help-generator.py README.in.md ${TMP}
	markdown-toc -t github -h 6 ${TMP}
	diff -q ${TMP} README.md

.PHONY: api-doc
api-doc:
	make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"

.PHONY: api-doc-spelling
api-doc-spelling:
	make -C docs spelling SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"
