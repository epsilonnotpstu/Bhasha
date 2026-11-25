# Progress

- [x] Bootstrap and plan
- [x] Lexer
- [x] Parser and AST
- [x] Semantic analysis
- [x] Inspectable IR and reference VM
- [x] CLI and basic browser playground
- [x] Initial examples and error diagnostics
- [x] Label-based CFG inspection (leaders algorithm)
- [~] Optimiser (constant folding, algebraic identities, local temporary DCE; no global data-flow)
- [~] Native ELF backend (GCC-generated C for implemented AST subset)
- [~] Minimal WAT backend (integer literal arithmetic only)
- [ ] Direct x86 assembly, full data-flow optimisation, expanded tests and 90% coverage

## Latest verification

- `pytest -q --cov=bhasha`: 13 passed, 80% total coverage (not yet the 90% target).
- Native factorial (`-o /tmp/fact`) ran successfully and printed `120`.

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Implement label-based CFG and dataflow optimiser, then implement native x86 or formally scope it out with instructor approval.
