"""Scoped static type checker for Bhasha."""
from dataclasses import dataclass
from .ast_nodes import *
from .diagnostics import Diagnostic
TYPE={"purno":"int","পূর্ণ":"int","doshomik":"float","দশমিক":"float","huen":"bool"}
@dataclass
class Symbol: name:str; type:str; initialized:bool=False; used:bool=False; params:list|None=None; return_type:str|None=None
class Analyzer:
 def __init__(self,source="<input>"):self.source=source;self.scopes=[{}];self.diagnostics=[];self.loop=0;self.returns=[]
 def error(self,n,msg):self.diagnostics.append(Diagnostic(msg,n.line,n.column,self.source))
 def declare(self,n,name,typ,**kw):
  if name in self.scopes[-1]:self.error(n,f"redeclaration of '{name}'")
  else:self.scopes[-1][name]=Symbol(name,typ,**kw)
 def find(self,n,name):
  for s in reversed(self.scopes):
   if name in s:return s[name]
  self.error(n,f"undeclared name '{name}'");return Symbol(name,"error")
 def compatible(self,a,b):return a==b or (a=="float" and b=="int") or "error" in (a,b)
 def expr(self,n):
  if isinstance(n,Literal):t="bool" if isinstance(n.value,bool) else "int" if isinstance(n.value,int) else "float" if isinstance(n.value,float) else "string"
  elif isinstance(n,Name):
   s=self.find(n,n.name);s.used=True;t=s.type
   if not s.initialized and s.type!="function":self.error(n,f"use of uninitialized '{n.name}'")
  elif isinstance(n,Index):
   a=self.expr(n.array);i=self.expr(n.index);t=a.removeprefix("array:") if a.startswith("array:") else "error"
   if i!="int":self.error(n,"array index must be int")
  elif isinstance(n,Unary):t=self.expr(n.operand);t="bool" if n.op in ("NOT","!") else t
  elif isinstance(n,Binary):
   a,b=self.expr(n.left),self.expr(n.right)
   if n.op in ("==","!=","<",">","<=",">=","AND","OR"):t="bool"
   elif a in ("int","float") and b in ("int","float"):t="float" if "float" in (a,b) else "int"
   else:self.error(n,"invalid operands");t="error"
  elif isinstance(n,Call):
   s=self.find(n,n.callee);t=s.return_type or s.type
   if s.type!="function":self.error(n,f"'{n.callee}' is not a function");t="error"
   elif len(n.args)!=len(s.params or []):self.error(n,"wrong argument count")
   else:
    for a,p in zip(n.args,s.params):
     if not self.compatible(p,self.expr(a)):self.error(n,"wrong argument type")
  else:t="error"
  n.inferred_type=t;return t
 def visit(self,n):
  if isinstance(n,Program):
   for x in n.statements:
    if isinstance(x,Function):
     result=TYPE.get(x.return_type,x.return_type)
     self.declare(x,x.name,"function",initialized=True,params=[TYPE.get(p[1],p[1]) for p in x.params],return_type=result)
     x.inferred_type=result
   for x in n.statements:self.visit(x)
  elif isinstance(n,Block):
   self.scopes.append({});[self.visit(x) for x in n.statements];self.scopes.pop()
  elif isinstance(n,VarDecl):
   ty=TYPE.get(n.type_name,n.type_name);ty="array:"+ty if n.size else ty;self.declare(n,n.name,ty,initialized=n.value is not None)
   if n.size and self.expr(n.size)!="int":self.error(n,"array size must be int")
   if n.value and not self.compatible(ty,self.expr(n.value)):self.error(n,"type mismatch in initializer")
  elif isinstance(n,Assign):
   target=self.expr(n.target);v=self.expr(n.value)
   if not self.compatible(target,v):self.error(n,"type mismatch in assignment")
   if isinstance(n.target,Name):self.find(n.target,n.target.name).initialized=True
  elif isinstance(n,(Print,)):self.expr(n.value)
  elif isinstance(n,Read):self.expr(n.target)
  elif isinstance(n,If):self.expr(n.condition);self.visit(n.then_branch);self.visit(n.else_branch) if n.else_branch else None
  elif isinstance(n,While):self.expr(n.condition);self.loop+=1;self.visit(n.body);self.loop-=1
  elif isinstance(n,For):self.declare(n,n.name,"int",initialized=True);self.expr(n.start);self.expr(n.end);self.loop+=1;self.visit(n.body);self.loop-=1
  elif isinstance(n,(Break,Continue)):
   if not self.loop:self.error(n,"break/continue outside loop")
  elif isinstance(n,Return):
   got=self.expr(n.value);want=self.returns[-1] if self.returns else None
   if not want:self.error(n,"return outside function")
   elif not self.compatible(want,got):self.error(n,"return type mismatch")
  elif isinstance(n,Function):
   self.scopes.append({});[self.declare(n,a,TYPE.get(t,t),initialized=True) for a,t in n.params];self.returns.append(TYPE.get(n.return_type,n.return_type));self.visit(n.body);self.returns.pop();self.scopes.pop()
 def analyze(self,p):self.visit(p);return self.diagnostics
def analyze(program,source="<input>"):a=Analyzer(source);return a.analyze(program),a
