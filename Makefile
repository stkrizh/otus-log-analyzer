test:
	python -m unittest discover --start-directory ./tests

install:
	pip install -e .

.PHONY: test
