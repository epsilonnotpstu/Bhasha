# Bhasha compiler report

## Abstract

Bhasha is a hand-written educational compiler pipeline for a small language with Bangla keywords. The implemented reference pipeline consists of a deterministic scanner, recursive-descent parser, scoped static analyser, inspectable three-address-code listing, simple identity optimiser, CFG DOT exporter, and portable VM.

## Objectives

The project demonstrates every teaching-stage of a compiler: lexical and syntax analysis, static semantic checking, intermediate representation, optimisation, and more than one execution target. Source positions and diagnostics make each stage explainable in a viva.

## Language and implementation

The language provides integer, floating point and Boolean types, fixed arrays, block scope, `jodi` conditionals, loops, functions and recursion. The scanner is a Unicode-aware deterministic state machine. The parser is recursive descent with precedence climbing. The semantic analyser keeps a stack of scope dictionaries and permits only integer-to-float widening.

The IR is readable TAC with temporaries, labels and conditional/unconditional jumps. CFG construction applies basic-block leaders. Optimisation performs basic-block-local constant/copy propagation, numeric folding, identities and conservative temporary DCE, repeating to a fixed point. The VM is the reference backend. The native backend emits C and invokes GCC to produce a Linux ELF; `--asm` exposes GCC's generated System V x86-64 assembly. The optional WAT emitter supports numeric programs including recursion and top-level fixed arrays. Its default `run` function returns the final numeric output; a separate host-I/O mode supports input and multiple outputs.

Dead-code elimination uses backwards CFG liveness to a fixed point: `OUT[B] = union(IN[S])` and `IN[B] = USE[B] union (OUT[B] - DEF[B])`. Only pure unused temporary definitions are removed.

The browser playground is dependency-free (`http.server`) and exposes every implemented inspection stage in tabs. Its CFG response includes both DOT and block/edge data, which the UI renders as inline SVG.

## Implementation and testing

The command `make native-demo` compiled factorial to a native executable and produced `120`. The latest `.venv/bin/pytest -q` run reports 156 passing tests, including optional Wasmtime execution tests. A previous coverage run measured 95% overall statement coverage; this number has not been remeasured for the latest changes. Golden tests compare VM and GCC-native ELF output for the original ten examples. Coverage does not establish complete language correctness.

## Measured optimisation results

The following table is reproduced by `make optimization-report`. Counts are TAC listing lines, including labels and declarations, rather than machine instructions. Each row is included only after AST VM, original TAC and optimized TAC produce the expected output.

| Example | Before | After | Folded | Simplified | Dead |
|---|---:|---:|---:|---:|---:|
| arithmetic | 7 | 7 | 0 | 0 | 0 |
| array_sum_max | 25 | 25 | 0 | 0 | 0 |
| condition | 9 | 9 | 0 | 0 | 0 |
| factorial | 17 | 17 | 0 | 0 | 0 |
| fibonacci_iterative | 17 | 17 | 0 | 0 | 0 |
| fibonacci_recursive | 19 | 19 | 0 | 0 | 0 |
| function_heavy | 16 | 16 | 0 | 0 | 0 |
| gcd | 14 | 14 | 0 | 0 | 0 |
| hello | 1 | 1 | 0 | 0 | 0 |
| loop | 12 | 12 | 0 | 0 | 0 |
| optimization_demo | 4 | 1 | 1 | 2 | 3 |

## Limitations

The experimental TAC interpreter can execute optimized TAC for supported programs; the primary VM and native backends still execute the AST. The hand-written x86 backend requires more equivalence testing. The WAT backend supports numeric functions and globals, fixed-size global and local arrays and optional host I/O. Its default `run` export returns only the final printed value; dynamic arrays and full backend parity remain unfinished. The report, grammar, playground, and examples do not yet cover every original acceptance criterion.

## References

1. Aho, Lam, Sethi and Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd edition.
2. GCC Project, GCC documentation, https://gcc.gnu.org/onlinedocs/.
3. LLVM Project, LLVM Language Reference Manual, https://llvm.org/docs/LangRef.html.
4. WebAssembly Community Group, WebAssembly Core Specification, https://webassembly.github.io/spec/.
