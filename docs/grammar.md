# Bhasha grammar

```ebnf
program = { statement } ;
statement = declaration | block | expression [ assignment_op expression ] ";"
          | "jodi" expression statement [ "nahole" statement ]
          | "jotokkhon" expression statement
          | "cholo" IDENT "=" expression "theke" expression statement
          | "kaj" IDENT "(" [ parameter { "," parameter } ] ")" ":" type block
          | "ferot" expression ";" | "dekhao" expression ";"
          | "poro" primary ";" | "thamo" ";" | "choluk" ";" ;
parameter = type IDENT ;
block = "{" { statement } "}" ;
declaration = "dhoro" type [ "[" expression "]" ] IDENT [ "=" expression ] ";" ;
type = "purno" | "doshomik" | "huen" ;
assignment_op = "=" | "+=" | "-=" | "*=" | "/=" ;
expression = unary { operator unary } ; (* parsed using the precedence table *)
unary = { "-" | "na" | "!" } primary ;
primary = NUMBER | FLOAT_LIT | STRING | "shotto" | "mittha"
        | IDENT [ "(" [ expression { "," expression } ] ")" | "[" expression "]" ]
        | "(" expression ")" ;
```

The parser uses precedence climbing. From lowest to highest precedence: `ba`, `ebong`, `== !=`, `< > <= >=`, `+ -`, `* / %`, unary; binary operators are left-associative. An identifier followed by `(`, `[` or neither is resolved using the next token. The optional `nahole` attaches to the nearest `jodi` (the classic dangling-else ambiguity), so the complete grammar is not claimed to be strictly LL(1).

`python3 tools/first_follow.py` computes FIRST/FOLLOW by fixed point for the statement and precedence-level expression BNF in that file. The complete generated table is in [first_follow.md](first_follow.md); `ε` means the empty production. The table describes that BNF, while the implementation uses precedence climbing rather than these explicit expression productions.

Run `PYTHONPATH=src python3 tools/dfa_demo.py` to generate `docs/dfa.dot` and, when Graphviz is available, `docs/dfa.svg`.
