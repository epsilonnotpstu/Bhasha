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
- [~] WAT backend (integer scalar variables, expressions, if/while/for; no functions, arrays, floats, strings, or host I/O)
- [x] Expanded automated test suite and 90% coverage target
- [x] Golden VM/native example equivalence tests
- [x] Inspectable artifact export and DFA diagram generator
- [x] Supported WAT artifact export and control-flow tests
- [x] Tabbed playground compiler inspection UI
- [x] Ten valid golden examples across key language features
- [x] Error-message fixtures for lexical, syntax, semantic, and type errors
- [x] Slide outline, demo script, and viva Q&A
- [~] Inspectable System V x86-64 assembly via GCC (`--asm`)
- [ ] Direct handwritten x86 assembly and full WAT backend

## Latest verification

- `pytest -q --cov=bhasha`: 34 passed, 94% total coverage; ten valid examples match on VM and native ELF; four erroneous examples have checked diagnostics.
- Native factorial (`-o /tmp/fact`) ran successfully and printed `120`.

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Add the remaining WAT features or formally scope the optional backend; direct native execution is already verified through GCC ELF generation.
