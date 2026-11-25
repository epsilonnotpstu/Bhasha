"""Reference AST interpreter; mirrors Bhasha semantics portably."""
from ..ast_nodes import *
class ReturnSignal(Exception):
 def __init__(self,v):self.v=v
class BreakSignal(Exception):pass
class ContinueSignal(Exception):pass
class VM:
 def __init__(self,output=None):self.global_env={};self.output=output or [];self.functions={}
 def eval(self,n,env):
  if isinstance(n,Literal):return n.value
  if isinstance(n,Name):return env[n.name]
  if isinstance(n,Index):return self.eval(n.array,env)[self.eval(n.index,env)]
  if isinstance(n,Unary):
   v=self.eval(n.operand,env);return -v if n.op=="-" else not v
  if isinstance(n,Binary):
   a,b=self.eval(n.left,env),self.eval(n.right,env);return {"+":lambda:a+b,"-":lambda:a-b,"*":lambda:a*b,"/":lambda:a/b,"%":lambda:a%b,"==":lambda:a==b,"!=":lambda:a!=b,"<":lambda:a<b,">":lambda:a>b,"<=":lambda:a<=b,">=":lambda:a>=b,"AND":lambda:a and b,"OR":lambda:a or b}[n.op]()
  if isinstance(n,Call):
   f=self.functions[n.callee];e={k:self.eval(v,env) for (k,_),v in zip(f.params,n.args)}
   try:self.exec(f.body,e)
   except ReturnSignal as r:return r.v
  raise RuntimeError("bad expression")
 def exec(self,n,env):
  if n is None:return
  if isinstance(n,Program):
   for x in n.statements:
    if isinstance(x,Function):self.functions[x.name]=x
   for x in n.statements:
    if not isinstance(x,Function):self.exec(x,env)
  elif isinstance(n,Block):
   for x in n.statements:self.exec(x,env)
  elif isinstance(n,VarDecl):env[n.name]=[0]*self.eval(n.size,env) if n.size else (self.eval(n.value,env) if n.value else 0)
  elif isinstance(n,Assign):
   v=self.eval(n.value,env)
   if isinstance(n.target,Name): env[n.target.name]=v if n.op=="=" else {"+=":lambda:env[n.target.name]+v,"-=":lambda:env[n.target.name]-v,"*=":lambda:env[n.target.name]*v,"/=":lambda:env[n.target.name]/v}[n.op]()
   else:self.eval(n.target.array,env)[self.eval(n.target.index,env)]=v
  elif isinstance(n,Print):self.output.append(str(self.eval(n.value,env)).lower() if isinstance(self.eval(n.value,env),bool) else str(self.eval(n.value,env)))
  elif isinstance(n,If):self.exec(n.then_branch if self.eval(n.condition,env) else n.else_branch,env)
  elif isinstance(n,While):
   while self.eval(n.condition,env):
    try:self.exec(n.body,env)
    except BreakSignal:break
    except ContinueSignal:continue
  elif isinstance(n,For):
   env[n.name]=self.eval(n.start,env);end=self.eval(n.end,env)
   while env[n.name]<end:
    try:self.exec(n.body,env)
    except BreakSignal:break
    except ContinueSignal:pass
    env[n.name]+=1
  elif isinstance(n,Return):raise ReturnSignal(self.eval(n.value,env))
  elif isinstance(n,Break):raise BreakSignal
  elif isinstance(n,Continue):raise ContinueSignal
def run(program):v=VM();v.exec(program,v.global_env);return "\n".join(v.output)+("\n" if v.output else "")
