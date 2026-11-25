# Design notes

The lexer is a deterministic character scanner; it retains line and column on every token. Parsing is recursive descent because the grammar is intentionally LL-friendly. Semantic analysis uses a stack of dictionaries, one per lexical scope, and permits only `int -> float` widening. The VM is deliberately the reference implementation while native code generation is deferred.

Future optimiser DCE will use backwards liveness: `OUT[B] = union(IN[S])`, `IN[B] = USE[B] union (OUT[B] - DEF[B])`.
