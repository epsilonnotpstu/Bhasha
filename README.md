# Bhasha compiler

A readable, hand-written teaching compiler for a small statically typed language with romanised and Unicode Bangla keywords. It has a scanner, LL-style recursive-descent parser, scoped type checker, inspectable TAC listing, and portable reference VM.

```sh
make setup
.venv/bin/bhasha examples/factorial.bh --tokens --ast --tac --run
```

Use `make test` for the test suite. The native x86 and WebAssembly emitters described in the original project brief remain planned work; `--run` is the supported execution path.

Native ELF for the supported language subset: `.venv/bin/bhasha examples/factorial.bh -o fact && ./fact`.

Inspect the corresponding GCC-generated System V x86-64 assembly with `.venv/bin/bhasha examples/factorial.bh --asm`.

Export tokens, AST, TAC, optimised TAC, and CFG together with `.venv/bin/bhasha examples/factorial.bh --emit-all build/factorial`.

Start the browser playground with `PYTHONPATH=src python3 -m bhasha.playground`, then visit `http://localhost:8000`.
