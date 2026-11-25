# Progress

- [x] Bootstrap and plan
- [x] Lexer
- [x] Parser and AST
- [x] Semantic analysis
- [x] Inspectable IR and reference VM
- [x] CLI and basic browser playground
- [x] Initial examples and error diagnostics
- [~] CFG/optimiser (inspection implementation only)
- [ ] Native x86/WAT backend, full optimiser, full academic documentation and coverage

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Implement label-based CFG and dataflow optimiser, then implement native x86 or formally scope it out with instructor approval.
