# Bhasha compiler report (working draft)

## Abstract

Bhasha is a hand-written educational compiler pipeline for a small language with Bangla keywords. The implemented reference pipeline consists of a deterministic scanner, recursive-descent parser, scoped static analyser, inspectable three-address-code listing, simple identity optimiser, CFG DOT exporter, and portable VM.

## Implementation and testing

The command `PYTHONPATH=src python3 -m bhasha.cli examples/factorial.bh --tac --run` produced `120` during the latest verification. `pytest` is specified as a dev dependency but was not installed in the supplied environment, so a coverage percentage is not claimed.

## Limitations

The current CFG is a one-block representation of structured inspection IR. Native x86-64, WebAssembly, full data-flow optimisation, and the complete academic report remain future phases and must not be represented as implemented.
