# Progress

- [x] Bootstrap and plan
- [x] Lexer
- [x] Parser and AST
- [x] Semantic analysis
- [x] Inspectable IR and reference VM
- [x] CLI and basic browser playground
- [x] Initial examples and error diagnostics
- [x] Label-based CFG inspection (leaders algorithm)
- [x] Optimiser (basic-block constant/copy propagation, folding, algebraic identities, global CFG-liveness DCE)
- [~] Native ELF backend (GCC-generated C for implemented AST subset)
- [~] Minimal WAT backend (integer literal arithmetic only)
- [x] Expanded automated test suite and 90% coverage target
- [x] Golden VM/native example equivalence tests
- [x] Inspectable artifact export and DFA diagram generator
- [x] Ten valid golden examples across key language features
- [x] Error-message fixtures for lexical, syntax, semantic, and type errors
- [x] Slide outline, demo script, and viva Q&A
- [~] Inspectable System V x86-64 assembly via GCC (`--asm`)
- [ ] Direct handwritten x86 assembly and full WAT backend

## Latest verification

- `pytest -q --cov=bhasha`: 32 passed, 94% total coverage; ten valid examples match on VM and native ELF; four erroneous examples have checked diagnostics.
- Native factorial (`-o /tmp/fact`) ran successfully and printed `120`.

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Implement label-based CFG and dataflow optimiser, then implement native x86 or formally scope it out with instructor approval.
