# Five-minute live demo

1. Open `examples/factorial.bh` and explain `kaj`, `jodi`, and `ferot` (30 seconds).
2. Run `.venv/bin/bhasha examples/factorial.bh --tokens --ast` to show the front end (45 seconds).
3. Run `.venv/bin/bhasha examples/factorial.bh --tac --cfg --opt-tac --stats` and point out labels, basic blocks, and temporaries (60 seconds).
4. Run `.venv/bin/bhasha examples/factorial.bh --run`; show `120` (30 seconds).
5. Run `.venv/bin/bhasha examples/factorial.bh -o fact && ./fact`; compare the identical `120` native output (45 seconds).
6. Run `.venv/bin/bhasha examples/factorial.bh --asm | head -30`; identify the function label and x86 instructions (30 seconds).
7. Run `PYTHONPATH=src python3 -m bhasha.playground`, visit localhost:8000, run a valid example and `dekhao @;` to demonstrate diagnostics (60 seconds).

If asked about limits, state that native execution is GCC-generated C rather than direct assembler, and WAT currently supports integer literal arithmetic only.
