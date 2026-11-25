# Viva questions and short answers

1. What is a compiler? A translator from source language to another representation or executable.
2. What is lexical analysis? Converting characters into tokens; see `lexer.py`.
3. What is a token? A typed lexeme with source position.
4. Why retain line/column? To print precise diagnostics.
5. What is DFA? A finite-state recogniser with one active state.
6. What is parsing? Turning tokens into an AST.
7. Why recursive descent? It is readable for an LL-friendly grammar; see `parser.py`.
8. What is LL(1)? Left-to-right input, leftmost derivation, one-token lookahead.
9. What is precedence climbing? A compact expression parser by binding precedence.
10. What is an AST? Syntax tree without punctuation-only nodes.
11. What is semantic analysis? Static checks beyond grammar; see `semantic.py`.
12. What is a symbol table? Scoped mapping from names to symbols.
13. What is lexical scope? A name resolves in its nearest enclosing block.
14. What is type widening? Safe `int` to `float` conversion.
15. What is an undeclared-variable error? Name absent from every active scope.
16. What is TAC? Three-address intermediate code; see `irgen.py`.
17. Why use IR? It separates front-end from execution backends.
18. What is a temporary? Compiler-created name holding an intermediate expression.
19. What is a label? Named branch target in TAC.
20. What is a basic block? Maximal straight-line instruction sequence.
21. What is a CFG? Graph of basic blocks and possible transfers; see `cfg_new.py`.
22. What is a leader? First instruction of a basic block.
23. What begins a leader? Entry, label, branch target, or code after branch.
24. What is constant folding? Compile-time evaluation of constants.
25. What is algebraic simplification? For example replacing `x + 0` by `x`.
26. What is fixed point? Repeating analysis until it stops changing.
27. What is liveness? Whether a value may be read in the future.
28. What is DCE? Removing computations whose values are not live.
29. What is a VM? Software executing language operations directly; see `backend/vm.py`.
30. Why is the VM the reference? It is portable and easy to validate.
31. What is recursion? A function calling itself.
32. How are calls represented in TAC? `param` instructions followed by `call`.
33. What is a backend? Component mapping IR/AST to an execution target.
34. What is ELF? Standard Linux executable format.
35. How is native output made? `native_x86.py` emits C and invokes GCC.
36. Why use GCC currently? It produces a reliable ELF while direct assembly is future work.
37. What is WebAssembly? Portable binary instruction format for sandboxed execution.
38. What is panic-mode recovery? Skipping to synchronisation tokens after syntax errors.
39. What is a golden test? Compare a known program output to expected output.
40. What is the largest limitation? No direct assembly/WAT and no global data-flow optimiser yet.
