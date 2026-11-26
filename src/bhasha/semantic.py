"""Scoped static type checker for Bhasha."""
from dataclasses import dataclass,asdict
from .ast_nodes import *
from .diagnostics import Diagnostic
TYPE={"purno":"int","পূর্ণ":"int","doshomik":"float","দশমিক":"float","huen":"bool"}
def definitely_returns(node):
 """Conservatively recognise blocks returning on every conditional path."""
 if isinstance(node,Return):return True
 if isinstance(node,Block):return any(definitely_returns(item) for item in node.statements)
 if isinstance(node,If):return node.else_branch is not None and definitely_returns(node.then_branch) and definitely_returns(node.else_branch)
 return False
@dataclass
class Symbol: name:str; type:str; initialized:bool=False; used:bool=False; params:list|None=None; return_type:str|None=None; line:int=0; column:int=0
class Analyzer:
 def __init__(self,source="<input>"):
  self.source=source;root={};self.scopes=[root];self.scope_ids=[0];self.scope_records=[{'id':0,'parent':None,'kind':'global','symbols':root}];self.diagnostics=[];self.warnings=[];self.loop=0;self.returns=[]
 def enter_scope(self,kind):
  scope={};scope_id=len(self.scope_records);self.scope_records.append({'id':scope_id,'parent':self.scope_ids[-1],'kind':kind,'symbols':scope});self.scopes.append(scope);self.scope_ids.append(scope_id)
 def leave_scope(self):self.scopes.pop();self.scope_ids.pop()
 def symbol_tables(self):
  return [{'id':record['id'],'parent':record['parent'],'kind':record['kind'],'symbols':[asdict(symbol) for symbol in record['symbols'].values()]} for record in self.scope_records]
 def error(self,n,msg):self.diagnostics.append(Diagnostic(msg,n.line,n.column,self.source))
 def warn(self,n,msg):self.warnings.append(Diagnostic(msg,n.line,n.column,self.source,kind='warning'))
 def initialization_snapshot(self):
  return [(symbol,symbol.initialized) for scope in self.scopes for symbol in scope.values()]
 def restore_initialization(self,snapshot):
  for symbol,state in snapshot:symbol.initialized=state
 def declare(self,n,name,typ,**kw):
  if name in self.scopes[-1]:self.error(n,f"redeclaration of '{name}'")
  else:self.scopes[-1][name]=Symbol(name,typ,line=n.line,column=n.column,**kw)
 def find(self,n,name):
  for s in reversed(self.scopes):
   if name in s:return s[name]
  self.error(n,f"undeclared name '{name}'");return Symbol(name,"error")
 def compatible(self,a,b):return a==b or (a=="float" and b=="int") or "error" in (a,b)
 def expr(self,n):
  if isinstance(n,Literal):t="bool" if isinstance(n.value,bool) else "int" if isinstance(n.value,int) else "float" if isinstance(n.value,float) else "string"
  elif isinstance(n,Name):
   s=self.find(n,n.name);s.used=True;t=s.type
   if not s.initialized and s.type not in ("function","error"):self.warn(n,f"use of uninitialized '{n.name}'")
  elif isinstance(n,Index):
   a=self.expr(n.array);i=self.expr(n.index);t=a.removeprefix("array:") if a.startswith("array:") else "error"
   if i!="int":self.error(n,"array index must be int")
  elif isinstance(n,Unary):
   operand=self.expr(n.operand)
   if n.op in ("NOT","!"):
    if operand not in ('bool','error'):self.error(n,'logical not requires bool')
    t='bool'
   else:
    if operand not in ('int','float','error'):self.error(n,'unary minus requires a number')
    t=operand
  elif isinstance(n,Binary):
   a,b=self.expr(n.left),self.expr(n.right)
   if n.op in ('AND','OR'):
    if a not in ('bool','error') or b not in ('bool','error'):self.error(n,'logical operators require bool operands')
    t='bool'
   elif n.op in ('<','>','<=','>='):
    if a not in ('int','float','error') or b not in ('int','float','error'):self.error(n,'ordering requires numeric operands')
    t='bool'
   elif n.op in ('==','!='):
    if a!='error' and b!='error' and not (a==b or {a,b}<={'int','float'}):self.error(n,'equality operands have incompatible types')
    t='bool'
   elif n.op=='%' and (a!='int' or b!='int'):
    if 'error' not in (a,b):self.error(n,'remainder requires integer operands')
    t='error'
   elif a in ("int","float") and b in ("int","float"):t="float" if "float" in (a,b) else "int"
   else:self.error(n,"invalid operands");t="error"
  elif isinstance(n,Call):
   s=self.find(n,n.callee);s.used=True;t=s.return_type or s.type
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
   self.enter_scope('block');[self.visit(x) for x in n.statements];self.leave_scope()
  elif isinstance(n,VarDecl):
   ty=TYPE.get(n.type_name,n.type_name);ty="array:"+ty if n.size else ty;self.declare(n,n.name,ty,initialized=n.value is not None or n.size is not None)
   if n.size and self.expr(n.size)!="int":self.error(n,"array size must be int")
   if n.value and not self.compatible(ty,self.expr(n.value)):self.error(n,"type mismatch in initializer")
  elif isinstance(n,Assign):
   if isinstance(n.target,Name) and n.op=='=':
    symbol=self.find(n.target,n.target.name);target=symbol.type;n.target.inferred_type=target
    if target=='function':self.error(n,'cannot assign to a function')
   else:target=self.expr(n.target)
   v=self.expr(n.value)
   if not self.compatible(target,v):self.error(n,"type mismatch in assignment")
   if isinstance(n.target,Name) and target not in ('error','function'):
    for scope in reversed(self.scopes):
     if n.target.name in scope:scope[n.target.name].initialized=True;break
  elif isinstance(n,(Print,)):self.expr(n.value)
  elif isinstance(n,Read):
   if isinstance(n.target,Name):
    symbol=self.find(n.target,n.target.name);n.target.inferred_type=symbol.type;symbol.initialized=True
    if symbol.type not in ('int','float'):self.error(n,'input target must be int or float')
   else:self.error(n,'input target must be a scalar variable')
  elif isinstance(n,If):
   if self.expr(n.condition) not in ('bool','error'):self.error(n,'if condition must be bool')
   before=self.initialization_snapshot();self.visit(n.then_branch);then_states=[symbol.initialized for symbol,_ in before]
   self.restore_initialization(before)
   if n.else_branch:self.visit(n.else_branch)
   else_states=[symbol.initialized for symbol,_ in before]
   for (symbol,_),yes,no in zip(before,then_states,else_states):symbol.initialized=yes and no
  elif isinstance(n,While):
   if self.expr(n.condition) not in ('bool','error'):self.error(n,'while condition must be bool')
   before=self.initialization_snapshot();self.loop+=1;self.visit(n.body);self.loop-=1;self.restore_initialization(before)
  elif isinstance(n,For):
   if self.expr(n.start) not in ('int','error'):self.error(n,'for start must be int')
   self.enter_scope('for');self.declare(n,n.name,'int',initialized=True)
   if self.expr(n.end) not in ('int','error'):self.error(n,'for end must be int')
   before=self.initialization_snapshot();self.loop+=1;self.visit(n.body);self.loop-=1;self.restore_initialization(before);self.leave_scope()
  elif isinstance(n,(Break,Continue)):
   if not self.loop:self.error(n,"break/continue outside loop")
  elif isinstance(n,Return):
   got=self.expr(n.value);want=self.returns[-1] if self.returns else None
   if not want:self.error(n,"return outside function")
   elif not self.compatible(want,got):self.error(n,"return type mismatch")
  elif isinstance(n,Function):
   before=self.initialization_snapshot();self.enter_scope(f'function {n.name}');[self.declare(n,a,TYPE.get(t,t),initialized=True) for a,t in n.params];self.returns.append(TYPE.get(n.return_type,n.return_type));self.visit(n.body);self.returns.pop();self.leave_scope();self.restore_initialization(before)
   if not definitely_returns(n.body):self.error(n,f"function '{n.name}' may exit without returning a value")
 def analyze(self,p):
  self.visit(p)
  for record in self.scope_records:
   for symbol in record['symbols'].values():
    if not symbol.used and symbol.type!='function':self.warnings.append(Diagnostic(f"unused variable '{symbol.name}'",symbol.line,symbol.column,self.source,kind='warning'))
  return self.diagnostics
def analyze(program,source="<input>"):a=Analyzer(source);return a.analyze(program),a
