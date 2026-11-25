# Design notes

The lexer is a deterministic character scanner; it retains line and column on every token. Parsing is recursive descent because the grammar is intentionally LL-friendly. Semantic analysis uses a stack of dictionaries, one per lexical scope, and permits only `int -> float` widening. The VM is deliberately the reference implementation while native code generation is deferred.

Future optimiser DCE will use backwards liveness: `OUT[B] = union(IN[S])`, `IN[B] = USE[B] union (OUT[B] - DEF[B])`.

The current CFG uses the classic leaders algorithm: first instruction, every label, instruction following a branch, and branch targets begin basic blocks. The local optimiser folds numeric TAC expressions and removes `x + 0` / `x * 1`; full global propagation and liveness DCE remain planned.

The optimiser also performs backwards liveness to a fixed point over CFG successors. Its equations are `OUT[B] = union(IN[S])` and `IN[B] = USE[B] union (OUT[B] - DEF[B])`. A temporary whose definition is not live-out is removed only when its right-hand side has no function call, preserving side effects.
