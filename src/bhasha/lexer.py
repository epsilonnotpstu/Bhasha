"""A hand-written, Unicode-aware state-machine scanner."""
from dataclasses import dataclass
from .diagnostics import Diagnostic

KEYWORDS = {
 "dhoro":"DECLARE", "ধরো":"DECLARE", "purno":"INT", "পূর্ণ":"INT",
 "doshomik":"FLOAT", "দশমিক":"FLOAT", "huen":"BOOL", "shotto":"TRUE", "সত্য":"TRUE", "mittha":"FALSE", "মিথ্যা":"FALSE",
 "jodi":"IF", "যদি":"IF", "nahole":"ELSE", "নাহলে":"ELSE", "jotokkhon":"WHILE", "যতক্ষণ":"WHILE",
 "cholo":"FOR", "চলো":"FOR", "theke":"TO", "thamo":"BREAK", "থামো":"BREAK", "choluk":"CONTINUE", "চলুক":"CONTINUE",
 "kaj":"FUNC", "কাজ":"FUNC", "ferot":"RETURN", "ফেরত":"RETURN", "dekhao":"PRINT", "দেখাও":"PRINT", "poro":"READ", "পড়ো":"READ",
 "ebong":"AND", "ba":"OR", "na":"NOT"
}
@dataclass(frozen=True)
class Token:
    type: str; lexeme: str; line: int; column: int

class Lexer:
    def __init__(self, text: str, source: str = "<input>"):
        self.text, self.source, self.i, self.line, self.col = text, source, 0, 1, 1
        self.diagnostics: list[Diagnostic] = []
    def peek(self, n=0): return self.text[self.i+n] if self.i+n < len(self.text) else "\0"
    def advance(self):
        c=self.peek(); self.i+=1
        if c=="\n": self.line,self.col=self.line+1,1
        else: self.col+=1
        return c
    def error(self,msg,l,c): self.diagnostics.append(Diagnostic(msg,l,c,self.source))
    def scan(self) -> list[Token]:
        out=[]
        while self.peek() != "\0":
            c=self.peek()
            if c.isspace(): self.advance(); continue
            l,col=self.line,self.col
            if c=="/" and self.peek(1)=="/":
                while self.peek() not in "\n\0": self.advance()
                continue
            if c=="/" and self.peek(1)=="*":
                self.advance(); self.advance()
                while self.peek() != "\0" and not (self.peek()=="*" and self.peek(1)=="/"): self.advance()
                if self.peek()=="\0": self.error("unterminated block comment",l,col)
                else: self.advance(); self.advance()
                continue
            if c=='"':
                self.advance(); value=""
                while self.peek() not in ('"','\0','\n'):
                    if self.peek()=="\\":
                        self.advance(); value += {"n":"\n","t":"\t","\\":"\\",'"':'"'}.get(self.advance(), "")
                    else: value += self.advance()
                if self.peek()!='"': self.error("unterminated string",l,col)
                else: self.advance(); out.append(Token("STRING",value,l,col))
                continue
            if c.isdigit():
                s=self.advance()
                while self.peek().isdigit(): s+=self.advance()
                typ="NUMBER"
                if self.peek()=="." and self.peek(1).isdigit():
                    typ="FLOAT_LIT"; s+=self.advance()
                    while self.peek().isdigit():s+=self.advance()
                out.append(Token(typ,s,l,col)); continue
            if c=="_" or c.isalpha() or ord(c)>127:
                s=self.advance()
                while self.peek()=="_" or self.peek().isalnum() or ord(self.peek())>127: s+=self.advance()
                out.append(Token(KEYWORDS.get(s,"IDENT"),s,l,col)); continue
            two=c+self.peek(1)
            if two in ("==","!=","<=",">=","+=","-=","*=","/="):
                self.advance();self.advance();out.append(Token(two,two,l,col));continue
            if c in "+-*/%<>=!;,:(){}[]": self.advance();out.append(Token(c,c,l,col));continue
            self.error(f"invalid character {c!r}",l,col); self.advance()
        out.append(Token("EOF","",self.line,self.col)); return out

def lex(text: str, source="<input>"):
    scanner=Lexer(text,source); return scanner.scan(),scanner.diagnostics
