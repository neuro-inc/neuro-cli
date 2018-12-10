DEVPI_URL ?= "https://$(DEVPI_USER):$(DEVPI_PASS)@$(DEVPI_HOST)/$(DEVPI_USER)"

SHELL := /bin/bash

.PHONY: init
init:
	pip install -r requirements.txt
	pip install -e .
	cp .hooks/* ../.git/hooks

.PHONY: e2e
e2e:
	pytest \
	    -n 0 \
		-m "e2e" \
		--cov=neuromation \
		--cov-report term-missing:skip-covered \
		--cov-report xml:coverage.xml \
		tests

.PHONY: _e2e
_e2e:
	pytest \
	    -n 0 \
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
lint:
	isort -c -rc neuromation tests
	black --check neuromation tests
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
	isort -rc neuromation tests
	black neuromation tests

# TODO (artyom, 07/16/2018): swap e2e and test once coverage output
# of both is combined. Otherwise e2e will override unit tests with
# lower coverage
.PHONY: ci
ci: lint test _e2e coverage

.PHONY: clean
clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +

devpi_setup:
	pip install devpi-client
	pip install wheel
	@devpi use $(DEVPI_URL)/$(DEVPI_INDEX)

devpi_login:
	@devpi login $(DEVPI_USER) --password=$(DEVPI_PASS)

devpi_upload: devpi_login
	devpi upload --formats bdist_wheel

