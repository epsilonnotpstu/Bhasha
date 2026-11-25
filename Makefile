.PHONY: setup test coverage demo playground native-demo clean
setup:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
test:
	.venv/bin/pytest -q
coverage:
	.venv/bin/pytest --cov=bhasha --cov-report=term-missing
demo:
	.venv/bin/bhasha examples/factorial.bh --run
playground:
	.venv/bin/python -m bhasha.playground
native-demo:
	@echo "Native x86 emission is not implemented; use --run (the portable VM)."
clean:
	rm -rf .venv .pytest_cache .coverage build dist *.egg-info
