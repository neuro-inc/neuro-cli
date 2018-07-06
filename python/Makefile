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


.PHONY: lint
lint:
	flake8

.PHONY: publish
publish:
	echo 'Not implemented'

.PHONY: coverage
coverage:
	$(SHELL) <(curl -s https://codecov.io/bash) -X coveragepy

.PHONY: ci
ci: test lint coverage

.PHONY: clean
clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
