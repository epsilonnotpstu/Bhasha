# Bhasha compiler

A readable, hand-written teaching compiler for a small statically typed language with romanised and Unicode Bangla keywords. It has a scanner, LL-style recursive-descent parser, scoped type checker, inspectable TAC listing, and portable reference VM.

```sh
make setup
.venv/bin/bhasha examples/factorial.bh --tokens --ast --tac --run
```

Use `make test` for the test suite. The native x86 and WebAssembly emitters described in the original project brief remain planned work; `--run` is the supported execution path.
