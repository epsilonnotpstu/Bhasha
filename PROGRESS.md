# Progress

- [x] Bootstrap and plan
- [x] Lexer
- [x] Parser and AST
- [x] Semantic analysis
- [x] Inspectable IR and reference VM
- [x] CLI and basic browser playground
- [x] Initial examples and error diagnostics
- [x] Label-based CFG inspection (leaders algorithm)
- [x] Optimiser (basic-block constant/copy propagation, folding, algebraic identities, local common-subexpression elimination, global CFG-liveness DCE)
- [~] Native ELF backend (GCC-generated C for implemented AST subset)
- [~] WAT backend (numeric functions and globals, fixed arrays in local and global scopes, optional host I/O; dynamic arrays and full parity remain)
- [x] Expanded automated test suite and 90% coverage target
- [x] Golden VM/native example equivalence tests
- [x] Inspectable artifact export and DFA diagram generator
- [x] Supported WAT artifact export and control-flow tests
- [x] Tabbed playground compiler inspection UI
- [x] Inline SVG CFG rendering in playground
- [~] Playground diagnostic highlighting and TAC diff polish
- [x] Ten valid golden examples across key language features
- [x] Error-message fixtures for lexical, syntax, semantic, and type errors
- [x] Slide outline, demo script, and viva Q&A
- [~] Inspectable System V x86-64 assembly via GCC (`--asm`)
- [~] Direct handwritten x86-64 subset backend (integers, control flow, functions/recursion, print)
- [~] TAC-native x86 backend (integer scalar subset, I/O and stack arguments; float, arrays and mixed-type calling convention remain)
- [ ] Complete backend parity and WAT dynamic arrays

## Latest verification

- `.venv/bin/pytest -q`: 240 passed. WAT also resets uninitialized scalar declarations on each execution and global declarations on each `run`, matching the reference VM in the tested cases.

- WAT fixed local arrays use per-call linear-memory frames, including in recursive functions; declarations clear their storage, and bounds checks trap. Wasmtime tests cover recursion, shadowing, loop initialization, memory growth and trap handling. Host callbacks must not re-enter the same instance's `run`.

Next: extend the experimental `--tac-x86` path to preserve type information and lower float operations, I/O and arrays, then cover wider calling conventions and numeric edge cases. The existing GCC and handwritten backends lower the AST; neither is the requested complete TAC-native backend.

- `.venv/bin/pytest -q`: 230 passed, including real Wasmtime host-I/O execution and CLI coverage. WAT uses i32 integers, so integer range and overflow semantics still differ from the VM.

- WAT supports numeric functions, recursion and fixed float, integer and Boolean arrays. `--wat-host` adds imports for input and mixed-type output, including UTF-8 strings and printing inside functions; the default `--wat` keeps its final-value-only contract. Wasmtime execution tests exercise both modes. Dynamic arrays and full backend parity remain unfinished.

- `.venv/bin/pytest -q`: 172 passed. Definite-initialization warnings now merge if/else states and conservatively restore state after loops and function definitions. This remains conservative rather than complete interprocedural/reachability analysis.

- `.venv/bin/pytest -q`: 170 passed. Uninitialized reads and unused variables now produce non-blocking semantic warnings, shown on CLI stderr and in the playground Warnings tab. Warning analysis is traversal-based, not path-sensitive; uninitialized scalar runtime values currently default to zero.

- `.venv/bin/pytest -q`: 168 passed with Wasmtime. Plain assignment can initialize an uninitialized scalar without a false read error; `cholo` introduces a loop-local integer variable and validates integer bounds. A shadowing example matches AST VM, O0/O2 TAC, GCC-native, direct x86, and Wasmtime's final-value contract.

- `.venv/bin/pytest -q`: 164 passed. TAC parsing now accepts Bangla identifiers containing combining marks, and direct x86 function labels use generated ASCII names. Two Bangla-identifier programs (function and array) match AST VM, O0/O2 TAC, GCC-native and direct x86. Other Unicode edge cases still need coverage.

- `.venv/bin/pytest -q`: 162 passed; playground API returns line/column diagnostics and before/after TAC diff entries. UI adds selectable diagnostic lines and colored TAC diff. JavaScript passed `node --check`; local HTTP GET returned 200. Firefox headless screenshot was attempted but no screenshot file was produced, so interactive visual verification and screenshots remain outstanding.

- Symbol table inspection now preserves global, function and block scope records, including parent scope, symbol types and initialization/use flags. `--symtab`, `--emit-all` (`symtab.json`) and playground Symbols tab expose them. Flags reflect the current analyzer's traversal rather than path-sensitive definite-assignment analysis.

- `.venv/bin/pytest -q`: 160 passed. The FIRST/FOLLOW tool now computes sets for statement grammar and precedence-level expressions, including calls, indexing and argument lists. The generated table in `docs/first_follow.md` is checked against tool output; the parser itself uses precedence climbing.

- `.venv/bin/pytest -q`: 159 passed. FIRST/FOLLOW are computed by fixed-point iteration from statement-level BNF; nullable propagation and documentation/table consistency are tested. Expressions remain an atomic terminal in this teaching table, so full-expression FIRST/FOLLOW is still outstanding.

- `.venv/bin/pytest -q`: 156 passed. Optimizer now iterates to a fixed point. `make optimization-report` checks output equivalence and prints measured listing counts for 11 examples; `optimization_demo` decreases from 4 to 1 lines. Latest coverage has not been remeasured.

- `.venv/bin/pytest -q`: 155 passed. `-O0/-O1/-O2` select the corresponding GCC level for native ELF/assembly; `--run-tac` selects original TAC at O0 and the current shared optimizer at O1/O2. AST `--run` and direct x86 do not use optimized TAC. TAC invalid numeric input now returns runtime exit code 2.

- `.venv/bin/pytest -q`: 150 passed. CLI VM and TAC now stream each print, and direct x86 exits via libc to flush previous output. Division, bounds and missing-input errors were tested after a print across both CLI execution modes and both native ELF backends.

- `.venv/bin/pytest -q`: 147 passed. VM, TAC and native input paths use strict line-oriented decimal input instead of accepting numeric prefixes; tests cover invalid suffixes, multiple values on one line, empty input and two valid consecutive lines. Extremely long inputs and floating-point range edge cases require more cross-platform testing.

- `.venv/bin/pytest -q`: 142 passed. GCC-native and direct x86 now detect failed/EOF numeric `scanf` and exit 2 with an input diagnostic; invalid and missing integer/float input are tested. Native scanf accepts numeric prefixes that Python's input parser may reject, so input parsing is not yet fully equivalent.

- `.venv/bin/pytest -q`: 138 passed with Wasmtime. Integer division/remainder and scalar float division by zero, including `/=`, are tested across AST VM, O0/O2 TAC, GCC-native and direct x86. Native ELF backends report the error on stderr and exit 2; other numeric edge cases remain to be checked.

- `.venv/bin/pytest -q`: 133 passed. GCC-native expressions and function arguments are sequenced left-to-right using GCC statement expressions; array-store RHS is evaluated before index, matching the AST VM and direct x86. O0/O2 TAC and both native executables match the AST VM on three side-effect regressions. This GCC-specific C output is not portable ISO C.

- `.venv/bin/pytest -q`: 130 passed. IR captures a mutable name or array element before evaluating a later function call in a binary expression or argument list; O0/O2 TAC and AST VM agree in regression tests. GCC C argument evaluation order and wider side-effect cases still need verification.

- `.venv/bin/pytest -q`: 128 passed. Direct x86 now passes integer and float arguments beyond the System V register limits on the stack, with alignment and separate integer/SSE classification. Executed ELF tests compare integer overflow, float overflow and mixed overflow arguments with VM and GCC-native. Other ABI edge cases still need coverage.

- Direct x86 supports System V integer/float argument register classes and float return values, including widening, nested and recursive calls (up to six integer and eight float register arguments). Tests compare generated ELF output with AST VM and GCC-native. Stack-passed arguments and full ABI/language equivalence remain unfinished.

- Direct x86 supports fixed-size float/Boolean arrays, zero-initialization and float element widening; tests compare float-array output across AST VM, O0/O2 TAC, GCC-native and direct x86, and verify local-array bounds failures. Float function ABI remains unfinished.

- `.venv/bin/pytest -q`: 119 passed with Wasmtime. Direct x86 now supports scalar float input and `+=`, `-=`, `*=`, `/=` using SSE2; a single input program matches AST VM, O0/O2 TAC, GCC-native and direct x86. Direct x86 float function ABI and float arrays remain unsupported.

- `.venv/bin/pytest -q`: 118 passed. Float output now uses six significant digits in AST VM and TAC, matching GCC-native/direct x86 `%g`; direct x86 also implements SSE2 float comparisons. Cross-backend tests include integer-valued float, rounding and mixed float/integer comparisons. Float function ABI, arrays, input and complete numerical edge-case parity remain unfinished.

- Direct x86 now has an experimental scalar SSE2 float subset (literals, widening, assignment, arithmetic and printing). Float function calls, comparisons, arrays, compound assignments and input remain unsupported. Float output formatting differs across backends for integral-valued floats (`-3.0` vs `-3`) and needs reconciliation.

- Float arrays now retain float element values in AST VM and typed TAC, with integer element assignments widened; a fractional division test compares O0/O2 TAC and GCC-native ELF. Boolean array zero-initialization is also tested. Direct x86 and WAT float arrays remain unsupported.

- `.venv/bin/pytest -q`: 112 passed with Wasmtime. TAC emits explicit int-to-float conversions for scalar initialization, assignment, function arguments and returns; O0/O2 TAC match the AST VM for regression cases. Float arrays and full backend parity remain unfinished.

- `.venv/bin/pytest -q`: 108 passed with Wasmtime. Semantic analysis rejects non-Boolean conditions/logical operands, nonnumeric ordering, incompatible equality and noninteger remainder. The AST VM widens integer scalar initializers/assignments to float. TAC and other backend float-widening parity still requires work.

- `.venv/bin/pytest -q`: 101 passed with Wasmtime. GCC-native and direct x86 now check both negative and upper-bound array reads/writes, print a runtime diagnostic to stderr and exit 2; tests execute both ELF backends. Unsupported array forms and broader backend parity still require work.

- `.venv/bin/pytest -q`: 97 passed with Wasmtime. AST VM and O0/O2 TAC reject negative and out-of-range array reads/writes; WAT traps on the same cases. GCC-native and direct x86 still lack bounds checks, so full parity is not claimed.

- `.venv/bin/pytest -q`: 90 passed with Wasmtime. WAT supports top-level fixed-size integer/Boolean arrays in linear memory, zeroes them on each run, supports indexed load/store from functions, and traps on out-of-bounds indices. Local/recursive arrays, float arrays and input/output imports remain unsupported; negative indices differ from the current Python VM behavior.

- `.venv/bin/pytest -q`: 87 passed with Wasmtime. WAT functions can read and modify scalar integer/Boolean globals; tests execute global mutation and parameter shadowing. Arrays, floating point, host I/O and full WAT equivalence remain unfinished.

- `.venv/bin/pytest -q`: 85 passed with optional Wasmtime. WAT integer/Boolean functions now accept parameters, return values and recursion; factorial (120), Fibonacci (21), and a two-argument function compiled and ran. Functions accessing globals or printing inside functions are not supported; arrays, floats and host I/O remain unfinished.

- `.venv/bin/pytest -q`: 81 passed with optional `wasmtime` installed in `.venv`. Six WAT programs were compiled and executed, covering shadowing, reserved/Unicode names, for-continue, while-break and Boolean expressions. WAT functions, arrays, floats and host I/O remain incomplete. Without Wasmtime these execution tests skip explicitly.

- `.venv/bin/pytest -q`: 75 passed. WAT generation now includes Boolean variables, short-circuit `ebong`/`ba`, logical negation, and nested loop `thamo`/`choluk` labels. Tests inspect generated WAT; no installed WAT compiler/runtime was available for execution validation.

- `.venv/bin/pytest -q`: 74 passed. Scalar integer compound assignments and short-circuit Boolean expressions have execution tests across AST VM, O0/O2 TAC, GCC-native and experimental direct x86. WAT logical operators and full backend parity remain incomplete.

- `.venv/bin/pytest -q`: 72 passed. Experimental direct x86 allocates top-level variables in global storage and uses lexical bindings for block and parameter shadowing; a compiled ELF matches the AST VM when a function mutates a global. Floats and full scope/backend parity still require work.

- `.venv/bin/pytest -q`: 71 passed. TAC now distinguishes shadowed block/parameter names and function frames can read/update globals; optimized and unoptimized TAC match AST VM on these regression cases. Direct x86 scope/global parity is still unfinished.

- `.venv/bin/pytest -q`: 68 passed. GCC-native now emits top-level variables in global storage, initializes scalar globals in source order, and matches AST VM for a function updating a global alongside block shadowing. TAC and direct x86 scope/global parity remain unfinished.

- `.venv/bin/pytest -q`: 67 passed. AST VM block scopes now preserve shadowed variables and assignments resolve in enclosing scopes; functions can read/write global variables. TAC and native backends still need scope/global-variable parity tests and fixes.

- `.venv/bin/pytest -q`: 65 passed. IR temporary allocation avoids user-defined names; optimizer invalidates cached constants after compound assignment/input and avoids propagating mutable aliases. These fixes have TAC execution regression tests; optimizer completeness and overall backend parity remain unfinished.

- TAC interpreter now supports function parameters, per-call local frames, returns and recursion. Recursive factorial, Fibonacci and nested functions match the AST VM at O0 and O2; full supported example comparison is included in tests. Other language parity limitations remain.

- `.venv/bin/pytest -q`: 61 passed. The experimental TAC interpreter now supports fixed arrays and scalar input; original and optimized TAC were compared against AST VM output for array sum/max and input. Function calls and full language parity remain unfinished.

- `.venv/bin/pytest -q`: 59 passed, including 300 fixed-seed arithmetic programs comparing AST VM, unoptimized TAC, and optimized TAC. Experimental `--run-tac -O2` executes scalar TAC; functions, arrays, and input remain unsupported.

- `.venv/bin/pytest -q --cov=bhasha --cov-report=term`: 57 passed, 95% overall statement coverage. `make native-demo` built a GCC-native factorial ELF and printed `120`. CLI reports missing source files with code 1 and VM bounds errors with code 2.

- `.venv/bin/pytest -q`: 56 passed. GCC-native and WAT now capture each `cholo` upper bound once, consistent with the VM and direct x86; the GCC-native executable is compared against VM output. WAT was checked structurally, not executed, because no WAT compiler/runtime is installed.

- `.venv/bin/pytest -q`: 54 passed. CFG blocks stop at returns/function boundaries; TAC for-loop continue targets the increment and saves the loop bound once. Direct x86 also saves its for-loop bound once. GCC-native and WAT loop-bound parity still requires work.

- `.venv/bin/pytest -q`: 51 passed. Playground VM execution has a 100,000-step limit and reports invalid input, arithmetic errors, array bounds and recursion errors as runtime diagnostics. The ordinary CLI VM remains unrestricted by default.

- `.venv/bin/pytest -q`: 51 passed. Parser recovers from stray top-level `}` and missing return-type tokens; semantic analysis reports functions that may fall through without returning. Return analysis is conservative for loops.

- `.venv/bin/pytest -q`: 48 passed. Optimizer constant folding now follows integer division/remainder semantics, retains unused potentially trapping division/array reads, and does not rewrite assignment destinations or quoted print strings. The optimizer still produces inspection TAC; VM/native execute the AST, not optimized TAC.

- `.venv/bin/pytest -q`: 45 passed. Experimental direct x86 now emits UTF-8 string literals, scalar Boolean declarations, and unary negation/not; the generated executable is checked against VM output. Full language support is still incomplete.

- `.venv/bin/pytest -q`: 44 passed. `poro` accepts integer input in VM, GCC-native, and experimental direct x86; VM and GCC-native also accept float input. Playground accepts line-separated input and reports missing input without blocking. WAT input remains unsupported.

- `.venv/bin/pytest -q`: 43 passed. Integer division truncates toward zero in the VM, matching C and direct x86; signed remainder and Boolean output have cross-backend executable tests. Full backend equivalence remains unfinished.

- `.venv/bin/pytest -q`: 42 passed. The experimental `--direct-x86 -o` CLI path compiles recursive factorial and produces an ELF and `.s` file. Call sites align the stack before invoking functions. VM/direct division and boolean output do not yet agree; do not claim backend equivalence for those cases.

- Latest run: `.venv/bin/pytest -q`: 41 passed. VM print evaluates its expression once; direct x86 integer arrays are zero-initialized and stack frames sized for local storage. Direct x86 and WAT remain incomplete and require broader equivalence testing.

- Latest run: `.venv/bin/pytest -q`: 39 passed. Direct x86 for-loop `continue` now advances the loop counter; regression test executes the generated ELF.

- `pytest -q --cov=bhasha`: 34 passed, 94% total coverage; ten valid examples match on VM and native ELF; four erroneous examples have checked diagnostics.
- Native factorial (`-o /tmp/fact`) ran successfully and printed `120`.

## Decisions

- The compiler uses only Python's standard library at runtime.
- The VM is the portable reference backend; native/WAT emission is best-effort.

## Next step

Execute `FINAL_PHASE.md` in order, maintaining VM/GCC-native equivalence tests for every backend addition.
