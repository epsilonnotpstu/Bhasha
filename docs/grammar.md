# Bhasha grammar

```ebnf
program = { statement } ;
statement = declaration | assignment ";" | "dekhao" expression ";" | "ferot" expression ";" | block ;
block = "{" { statement } "}" ;
declaration = "dhoro" type [ "[" expression "]" ] IDENT [ "=" expression ] ";" ;
expression = unary { operator unary } ;
unary = [ "-" | "na" ] primary ;
primary = NUMBER | STRING | IDENT [ "(" [ expression { "," expression } ] ")" ] | "(" expression ")" ;
```

The recursive-descent parser uses precedence climbing for expression precedence. Declaration/array parsing is the only lookahead-sensitive area and is resolved by the `[` token.
