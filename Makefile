.PHONY: setup test coverage demo playground native-demo optimization-report clean
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
	mkdir -p build
	.venv/bin/bhasha examples/factorial.bh -o build/factorial
	./build/factorial
optimization-report:
	.venv/bin/python tools/optimization_report.py
clean:
	rm -rf .venv .pytest_cache .coverage build dist *.egg-info
