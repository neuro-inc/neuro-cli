.PHONY: python
python:
	make -C python lint test

.PHONY: all
all: python