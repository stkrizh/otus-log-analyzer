test:
	python -m unittest discover --start-directory ./tests

install:
	pip install .

.PHONY: test
