# Design notes

The lexer is a deterministic character scanner; it retains line and column on every token. Parsing is recursive descent because the grammar is intentionally LL-friendly. Semantic analysis uses a stack of dictionaries, one per lexical scope, and permits only `int -> float` widening. The AST VM is the reference implementation; the GCC and handwritten x86 backends lower the AST. A separate experimental `--tac-x86` path lowers an explicitly validated integer scalar TAC subset directly to x86-64 stack slots and System V argument registers. It is not yet a full TAC-native backend.

The TAC optimizer also performs conservative local common-subexpression elimination for pure arithmetic and comparisons. It clears available expressions at control-flow boundaries, calls, input and assignments that may change operands; division, remainder and array reads are excluded because they may trap.

Future optimiser DCE will use backwards liveness: `OUT[B] = union(IN[S])`, `IN[B] = USE[B] union (OUT[B] - DEF[B])`.

The current CFG uses the classic leaders algorithm: first instruction, every label, instruction following a branch, and branch targets begin basic blocks. The local optimiser folds numeric TAC expressions and removes `x + 0` / `x * 1`; full global propagation and liveness DCE remain planned.

The optimiser also performs backwards liveness to a fixed point over CFG successors. Its equations are `OUT[B] = union(IN[S])` and `IN[B] = USE[B] union (OUT[B] - DEF[B])`. A temporary whose definition is not live-out is removed only when its right-hand side has no function call, preserving side effects.

Array indices must satisfy `0 <= index < length`; negative indices are errors, not Python-style indexing. The AST VM and TAC interpreter raise an index error, WAT traps, and the GCC-generated C and direct x86 backends report an error and exit with status 2. Native support remains limited to the array forms each backend accepts.

WAT fixed local arrays occupy offsets in a per-call linear-memory frame. A stack pointer allocates a separate frame for each recursive call, restores it on return, and grows memory when necessary. Array declarations clear their storage each time they execute, including inside loops. Each `run` resets the stack pointer so an instance can be invoked again after a trap; host callbacks must therefore not re-enter that same instance's `run`. Array sizes must currently be positive integer literals in WAT.

Float `dekhao` output uses six significant digits, matching C's `%g` formatting (for example, `-3.0` prints as `-3`). This is an output-format rule; stored floating-point values retain their precision.

`cholo` introduces a loop-local integer variable. Its start expression is evaluated in the outer scope, then the new variable is created, and the end expression is evaluated once. An outer variable with the same name becomes visible again after the loop.

`poro` reads one numeric value per line, permits surrounding ASCII whitespace and an optional sign, and rejects trailing text. Float input permits a decimal point and decimal exponent. Integer input is limited to signed 64-bit; out-of-range values are runtime errors. Native input parsing uses a shared C runtime helper.

Uninitialized reads and unused variables produce warnings rather than compilation errors. For `if`/`else`, a variable is definitely initialized afterwards only if both branches initialize it; a loop body may execute zero times, so it does not establish initialization afterwards. Function bodies are analyzed conservatively without treating their assignments as executed at declaration. This is not a complete interprocedural or reachability analysis and may over-report warnings. Declared but uninitialized scalar variables currently default to zero at runtime.
