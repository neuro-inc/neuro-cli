DEVPI_URL ?= "https://$(DEVPI_USER):$(DEVPI_PASS)@$(DEVPI_HOST)/$(DEVPI_USER)"

SHELL := /bin/bash

.PHONY: init
init:
	cp -n README.in.md README.md
	pip install -r requirements.txt
	pip install -e .
	cp .hooks/* ../.git/hooks
.PHONY: e2e
e2e:
	pyьфлу \
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
	isort -c -rc neuromation tests build-tools
	black --check neuromation tests build-tools
	mypy neuromation/client neuromation/logging neuromation/strings
	flake8

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
	isort -rc neuromation tests build-tools
	black neuromation tests build-tools

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