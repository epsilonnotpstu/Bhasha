# Bhasha compiler report

## Abstract

Bhasha is a hand-written educational compiler pipeline for a small language with Bangla keywords. The implemented reference pipeline consists of a deterministic scanner, recursive-descent parser, scoped static analyser, inspectable three-address-code listing, simple identity optimiser, CFG DOT exporter, and portable VM.

## Objectives

The project demonstrates every teaching-stage of a compiler: lexical and syntax analysis, static semantic checking, intermediate representation, optimisation, and more than one execution target. Source positions and diagnostics make each stage explainable in a viva.

## Language and implementation

The language provides integer, floating point and Boolean types, fixed arrays, block scope, `jodi` conditionals, loops, functions and recursion. The scanner is a Unicode-aware deterministic state machine. The parser is recursive descent with precedence climbing. The semantic analyser keeps a stack of scope dictionaries and permits only integer-to-float widening.

The IR is readable TAC with temporaries, labels and conditional/unconditional jumps. CFG construction applies basic-block leaders. Optimisation performs basic-block-local constant/copy propagation, numeric folding, identities and conservative temporary DCE. The VM is the reference backend. The native backend emits C and invokes GCC to produce a Linux ELF; `--asm` exposes GCC's generated System V x86-64 assembly. The optional WAT emitter supports integer literal arithmetic.

## Implementation and testing

The command `PYTHONPATH=src python3 -m bhasha.cli examples/factorial.bh --tac --run` produced `120` during the latest verification. The venv test suite reports 25 passing tests and 92% total coverage, meeting the intended 90% target. Golden tests compare VM and native ELF output for all shipped valid examples.

## Limitations

The current CFG is a one-block representation of structured inspection IR. Native x86-64, WebAssembly, full data-flow optimisation, and the complete academic report remain future phases and must not be represented as implemented.

This statement supersedes the earlier draft: CFG is now label/basic-block based and native ELF is implemented through generated C/GCC. Remaining limitations are direct handwritten assembly, whole-program data-flow optimisation and a full WAT compiler.
