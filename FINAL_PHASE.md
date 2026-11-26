# Final hardening queue

1. Direct x86: arrays, loop control, input, bool/string output, floats/SSE.
2. WAT: functions, arrays, floats, strings, host I/O and binary validation.
3. Playground: editor error marks, TAC diff, examples selector, screenshots.
4. Report: measured optimisation table and PDF-ready academic expansion.

Each item requires implementation plus VM/native/WAT equivalence tests. Existing GCC-native and VM paths remain the reference while the new direct/WAT paths are expanded.
