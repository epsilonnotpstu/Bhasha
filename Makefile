.PHONY: setup test coverage demo playground native-demo optimization-report live-demo clean
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
live-demo:
	@echo "=== 1. Running factorial.bh on Reference VM ==="
	.venv/bin/bhasha examples/factorial.bh --run
	@echo "\n=== 2. Compiler Stages (TAC + Optimization Stats) ==="
	.venv/bin/bhasha examples/factorial.bh --tac --opt-tac --stats
	@echo "\n=== 3. Native ELF Binary Execution ==="
	mkdir -p build
	.venv/bin/bhasha examples/factorial.bh -o build/factorial
	./build/factorial
	@echo "\n=== 4. Running Test Suite ==="
	.venv/bin/pytest -q
clean:
	rm -rf .venv .pytest_cache .coverage build dist *.egg-info
