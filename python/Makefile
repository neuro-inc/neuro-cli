.PHONY: init
init:
	pip install -r requirements.txt
	pip install -e .

.PHONY: test
test:
	pytest --cov=neuromation

.PHONY: lint
lint:
	flake8

.PHONY: publish
publish:
	echo 'Not implemented'

.PHONY: clean
clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +
