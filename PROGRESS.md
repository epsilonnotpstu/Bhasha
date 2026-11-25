# Progress

- [x] Bootstrap and plan
- [x] Lexer
- [x] Parser and AST
- [x] Semantic analysis
- [x] Inspectable IR and reference VM
- [~] CLI, playground, documentation, examples, tests

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Run examples and add the remaining advanced project phases (optimiser, CFG, native/WAT, playground, full academic report).
