# Bhasha implementation plan

1. Bootstrap the Python package, CLI, build targets, and project checkpoints.
2. Implement hand-written lexing, recursive-descent parsing, and AST display.
3. Add scoped semantic checking and diagnostics.
4. Lower programs to three-address code, build CFGs, optimise it, and execute it on a VM.
5. Add optional text/native output, playground, examples, tests, and course documentation.

Phase gates are recorded in `PROGRESS.md`. The VM is the reference execution backend.
