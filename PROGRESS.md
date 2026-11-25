# Progress

- [x] Bootstrap and plan
- [x] Lexer
- [x] Parser and AST
- [x] Semantic analysis
- [x] Inspectable IR and reference VM
- [x] CLI and basic browser playground
- [x] Initial examples and error diagnostics
- [x] Label-based CFG inspection (leaders algorithm)
- [~] Optimiser (basic-block constant/copy propagation, folding, algebraic identities, local temporary DCE; no global data-flow)
- [~] Native ELF backend (GCC-generated C for implemented AST subset)
- [~] Minimal WAT backend (integer literal arithmetic only)
- [x] Expanded automated test suite and 90% coverage target
- [~] Inspectable System V x86-64 assembly via GCC (`--asm`)
- [ ] Direct handwritten x86 assembly and full global data-flow optimisation

## Latest verification

- `pytest -q --cov=bhasha`: 17 passed, 91% total coverage.
- Native factorial (`-o /tmp/fact`) ran successfully and printed `120`.

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Implement label-based CFG and dataflow optimiser, then implement native x86 or formally scope it out with instructor approval.
