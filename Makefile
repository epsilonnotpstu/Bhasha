.PHONY: setup test coverage demo playground native-demo clean
setup:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
test:
	PYTHONPATH=src python3 -m pytest -q
coverage:
	PYTHONPATH=src python3 -m pytest --cov=bhasha --cov-report=term-missing
demo:
	PYTHONPATH=src python3 -m bhasha.cli examples/factorial.bh --run
playground:
	PYTHONPATH=src python3 -m bhasha.playground
native-demo:
	@echo "Native x86 emission is not implemented; use --run (the portable VM)."
clean:
	rm -rf .venv .pytest_cache .coverage build dist *.egg-info
