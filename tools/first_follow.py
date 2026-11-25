"""Print FIRST/FOLLOW sets for the small LL-friendly teaching grammar."""
GRAMMAR={
 "program":["statement*"], "statement":["declaration","assignment ;","dekhao expression ;","ferot expression ;","block"],
 "block":["{ statement* }"], "declaration":["dhoro type IDENT initializer ;"],
 "expression":["unary operator*"], "unary":["- unary","na unary","primary"],
 "primary":["NUMBER","STRING","IDENT","( expression )"]}
FIRST={"program":{"dhoro","IDENT","dekhao","ferot","{"},"statement":{"dhoro","IDENT","dekhao","ferot","{"},"block":{"{"},"declaration":{"dhoro"},"expression":{"-","na","NUMBER","STRING","IDENT","("},"unary":{"-","na","NUMBER","STRING","IDENT","("},"primary":{"NUMBER","STRING","IDENT","("}}
FOLLOW={"program":{"EOF"},"statement":{"dhoro","IDENT","dekhao","ferot","}","EOF"},"block":{"dhoro","IDENT","dekhao","ferot","}","EOF"},"declaration":{"dhoro","IDENT","dekhao","ferot","}","EOF"},"expression":{";",")","]","}"},"unary":{";",")","]","}","+","-","*","/"},"primary":{";",")","]","}","+","-","*","/"}}
if __name__=="__main__":
 for nonterminal in GRAMMAR: print(f"{nonterminal:12} FIRST = {{{', '.join(sorted(FIRST[nonterminal]))}}}  FOLLOW = {{{', '.join(sorted(FOLLOW[nonterminal]))}}}")
