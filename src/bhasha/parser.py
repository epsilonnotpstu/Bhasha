"""LL-friendly recursive descent parser with panic-mode recovery."""
from .ast_nodes import *
from .diagnostics import Diagnostic
class Parser:
 def __init__(self,tokens,source="<input>"):
  self.tokens,self.source,self.i,self.diagnostics=tokens,source,0,[]
 def cur(self): return self.tokens[self.i]
 def match(self,*types):
  if self.cur().type in types: t=self.cur();self.i+=1;return t
  return None
 def need(self,typ,msg=None):
  t=self.match(typ)
  if t:return t
  self.err(msg or f"expected '{typ}'"); raise SyntaxError
 def err(self,msg):
  t=self.cur(); self.diagnostics.append(Diagnostic(msg,t.line,t.column,self.source))
 def sync(self):
  while self.cur().type not in ("EOF",";","}"):self.i+=1
  if self.cur().type==";":self.i+=1
 def parse(self):
  ss=[]
  while self.cur().type!="EOF":
   if self.cur().type=="}":
    self.err("unexpected '}'");self.i+=1;continue
   try:ss.append(self.statement())
   except SyntaxError:self.sync()
  return Program(statements=ss)
 def statement(self):
  t=self.cur(); typ=t.type
  if typ=="{":return self.block()
  if typ=="DECLARE":return self.decl()
  if typ=="IF":return self.if_stmt()
  if typ=="WHILE":return self.while_stmt()
  if typ=="FOR":return self.for_stmt()
  if typ=="FUNC":return self.function()
  if typ=="RETURN":self.i+=1;v=self.expr();self.need(";");return Return(t.line,t.column,value=v)
  if typ=="PRINT":self.i+=1;v=self.expr();self.need(";");return Print(t.line,t.column,value=v)
  if typ=="READ":self.i+=1;v=self.primary();self.need(";");return Read(t.line,t.column,target=v)
  if typ=="BREAK":self.i+=1;self.need(";");return Break(t.line,t.column)
  if typ=="CONTINUE":self.i+=1;self.need(";");return Continue(t.line,t.column)
  e=self.expr()
  if isinstance(e,(Name,Index)) and self.cur().type in ("=","+=","-=","*=","/="):
   op=self.cur();self.i+=1;v=self.expr();self.need(";");return Assign(op.line,op.column,target=e,op=op.type,value=v)
  self.need(";", "expected assignment or ';'");return e
 def block(self):
  t=self.need("{");ss=[]
  while self.cur().type not in ("}","EOF"):
   try:ss.append(self.statement())
   except SyntaxError:self.sync()
  self.need("}","expected '}'");return Block(t.line,t.column,statements=ss)
 def decl(self):
  t=self.need("DECLARE"); ty=self.cur()
  if ty.type not in ("INT","FLOAT","BOOL"):self.err("expected a type after dhoro");raise SyntaxError
  self.i+=1;size=None
  if self.match("["): size=self.expr();self.need("]")
  name=self.need("IDENT","expected variable name"); val=None
  if self.match("="):val=self.expr()
  self.need(";");return VarDecl(t.line,t.column,name=name.lexeme,type_name=ty.lexeme,size=size,value=val)
 def if_stmt(self):
  t=self.need("IF");c=self.expr();a=self.statement();b=None
  if self.match("ELSE"):
   b=self.if_stmt() if self.cur().type=="IF" else self.statement()
  return If(t.line,t.column,condition=c,then_branch=a,else_branch=b)
 def while_stmt(self):
  t=self.need("WHILE");return While(t.line,t.column,condition=self.expr(),body=self.statement())
 def for_stmt(self):
  t=self.need("FOR"); n=self.need("IDENT");self.need("=");a=self.expr();self.need("TO");b=self.expr();return For(t.line,t.column,name=n.lexeme,start=a,end=b,body=self.statement())
 def function(self):
  t=self.need("FUNC");n=self.need("IDENT");self.need("(");ps=[]
  if self.cur().type!=")":
   while True:
    ty=self.cur();
    if ty.type not in ("INT","FLOAT","BOOL"):self.err("expected parameter type");raise SyntaxError
    self.i+=1; pn=self.need("IDENT");ps.append((pn.lexeme,ty.lexeme))
    if not self.match(","):break
  self.need(")");self.need(":","expected ':' before return type");rt=self.cur()
  if rt.type not in ("INT","FLOAT","BOOL"):self.err("expected return type");raise SyntaxError
  self.i+=1
  return Function(t.line,t.column,name=n.lexeme,params=ps,return_type=rt.lexeme,body=self.block())
 def expr(self,minp=0):
  e=self.unary();prec={"OR":1,"AND":2,"==":3,"!=":3,"<":4,">":4,"<=":4,">=":4,"+":5,"-":5,"*":6,"/":6,"%":6}
  while prec.get(self.cur().type,0)>=minp and self.cur().type in prec:
   op=self.cur();p=prec[op.type];self.i+=1;e=Binary(op.line,op.column,left=e,op=op.type,right=self.expr(p+1))
  return e
 def unary(self):
  if self.cur().type in ("-","NOT","!"):
   t=self.cur();self.i+=1;return Unary(t.line,t.column,op=t.type,operand=self.unary())
  return self.primary()
 def primary(self):
  t=self.cur()
  if self.match("NUMBER"):return Literal(t.line,t.column,value=int(t.lexeme))
  if self.match("FLOAT_LIT"):return Literal(t.line,t.column,value=float(t.lexeme))
  if self.match("STRING"):return Literal(t.line,t.column,value=t.lexeme)
  if self.match("TRUE"):return Literal(t.line,t.column,value=True)
  if self.match("FALSE"):return Literal(t.line,t.column,value=False)
  if self.match("("):e=self.expr();self.need(")");return e
  if self.match("IDENT"):
   if self.match("("):
    a=[]
    if self.cur().type!=")":
     while True:
      a.append(self.expr())
      if not self.match(","):break
    self.need(")");return Call(t.line,t.column,callee=t.lexeme,args=a)
   e=Name(t.line,t.column,name=t.lexeme)
   if self.match("["): e=Index(t.line,t.column,array=e,index=self.expr());self.need("]")
   return e
  self.err("expected expression");raise SyntaxError
def parse(tokens,source="<input>"):
 p=Parser(tokens,source);return p.parse(),p.diagnostics
