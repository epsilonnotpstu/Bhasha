# 12-slide presentation outline

1. **Bhasha compiler** — Bangla-keyword teaching language; course, author, date.
2. **Problem and objectives** — Build an inspectable compiler pipeline from scratch.
3. **Language design** — Keywords, types, blocks, functions, arrays and examples.
4. **Architecture** — Lexer → parser/AST → semantic analysis → TAC → optimizer → VM/native/WAT.
5. **Lexical analysis** — State scanner, token position, Unicode identifiers and diagnostics.
6. **Syntax analysis** — LL-friendly grammar, recursive descent and precedence climbing.
7. **Semantic analysis** — Symbol scopes, type rules and static errors.
8. **IR and CFG** — TAC temporaries, labels, leaders algorithm and DOT graph.
9. **Optimisation** — Folding, copy propagation, identities and safe temporary DCE.
10. **Backends** — Portable VM, GCC-produced x86-64 ELF, minimal WAT target.
11. **Testing and demo** — 19 passing automated tests, 90% measured coverage.
12. **Limitations/future work** — Direct assembly, global dataflow, complete WAT; closing questions.

Speaker notes: demonstrate a single factorial source through `--tokens`, `--ast`, `--tac`, `--cfg`, `--asm`, `--run`, then show the playground.
