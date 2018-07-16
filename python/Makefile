SHELL := /bin/bash

.PHONY: init
init:
	pip install -r requirements.txt
	pip install -e .
	cp .hooks/* ../.git/hooks

.PHONY: e2e
e2e:
	pytest \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: test
test:
	pytest \
		-m "not e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: test-all
test-all:
	pytest \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: isort
isort:
	isort -rc neuromation
	isort -rc tests
	isort -rc .

.PHONY: lint
lint:
	flake8

.PHONY: publish
publish:
	echo 'Not implemented'

.PHONY: coverage
coverage:
	$(SHELL) <(curl -s https://codecov.io/bash) -X coveragepy


# TODO (artyom, 07/16/2018): swap e2e and test once coverage output
# of both is combined. Otherwise e2e will override unit tests with
# lower coverage
.PHONY: ci
ci: lint e2e test coverage

.PHONY: clean
clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
