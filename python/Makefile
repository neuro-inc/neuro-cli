DEVPI_URL ?= "https://$(DEVPI_USER):$(DEVPI_PASS)@$(DEVPI_HOST)/$(DEVPI_USER)"

SHELL := /bin/bash
BRANCH := $(shell git branch | grep \* | cut -d ' ' -f2)

ISORT_DIRS := neuromation tests build-tools
ISORT_REGEXP := ^python/(neuromation|tests|build-tools)/.+\\.py
BLACK_DIRS := $(ISORT_DIRS)
BLACK_REGEXP := $(ISORT_REGEXP)
MYPY_DIRS := neuromation/client neuromation/logging neuromation/strings
MYPY_REGEXP := ^python/neuromation/(client|logging|strings)/.+\\.py
FLAKE8_DIRS := .
FLAKE8_REGEXP := ^python/.+\\.py

.PHONY: init
init:
	cp -n README.in.md README.md
	pip install -r requirements.txt
	pip install -e .
	cp .hooks/* ../.git/hooks
	rm -rf .mypy_cache
.PHONY: e2e
e2e:
	pytest \
	    -n auto \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: _e2e
_e2e:
	pytest \
	    -n auto \
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
	    -n 4 \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: lint
lint: lint-docs
	isort -c -rc ${ISORT_DIRS}
	black --check $(BLACK_DIRS)
	mypy --cache-dir .mypy_cache/$(BRANCH) $(MYPY_DIRS)
	flake8 $(FLAKE8_DIRS)

.PHONY: lint-diff
lint-diff: ISORT_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(ISORT_REGEXP)") print substr($$NF, 8)}')
lint-diff: BLACK_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(BLACK_REGEXP)") print substr($$NF, 8)}')
lint-diff: MYPY_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(MYPY_REGEXP)") print substr($$NF, 8)}')
lint-diff: FLAKE8_TARGETS:=$(shell git diff --name-status --diff-filter=d $(FROM) $(TO) . |  awk '{if ($$NF ~ "$(FLAKE8_REGEXP)") print substr($$NF, 8)}')
lint-diff:
	@ [ -z "${ISORT_TARGETS}" ] || (echo "Lint isort:"; echo "   ${ISORT_TARGETS}" && isort -c -rc ${ISORT_TARGETS})
	@ [ -z "${BLACK_TARGETS}" ] || (echo "Lint black:"; echo "   ${BLACK_TARGETS}" && black -q --check ${BLACK_TARGETS})
	@ [ -z "${MYPY_TARGETS}" ] || (echo "Lint mypy:"; echo "   ${MYPY_TARGETS}" && mypy --cache-dir .mypy_cache/$(BRANCH) ${MYPY_TARGETS})
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
	rm -rf .testmondata .tmontmp

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
lint-docs: TMP:=$(shell mktemp -t README.XXXXXXXX.md)
lint-docs:
	build-tools/cli-help-generator.py README.in.md ${TMP}
	markdown-toc -t github -h 6 ${TMP}
	diff -q ${TMP} README.md