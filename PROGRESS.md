# Progress

- [x] Bootstrap and plan
- [ ] Lexer
- [ ] Parser and AST
- [ ] Semantic analysis
- [ ] IR, CFG, optimiser, VM
- [ ] CLI, playground, documentation, examples, tests

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Create the package metadata and implement the lexer/parser pipeline.
