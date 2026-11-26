"""Readable pseudo three-address-code listing for pipeline inspection."""
from .ast_nodes import *
from dataclasses import fields, is_dataclass
class IRGen:
 def __init__(self): self.lines=[]; self.n=0; self.labels=0; self.breaks=[]; self.continues=[];self.reserved=set();self.scopes=[{}];self.scope_id=0;self.signatures={};self.return_type=None
 def temp(self):
  while True:
   self.n+=1;name=f"t{self.n}"
   if name not in self.reserved:return name
 def reserve_names(self,node):
  if isinstance(node,(Name,VarDecl,For,Function)):self.reserved.add(node.name)
  if isinstance(node,Function):self.reserved.update(name for name,_ in node.params)
  if is_dataclass(node):
   for field in fields(node):self.reserve_names(getattr(node,field.name))
  elif isinstance(node,(list,tuple)):
   for child in node:self.reserve_names(child)
 def label(self,prefix="L"): self.labels+=1; return f"{prefix}{self.labels}"
 def widen(self,operand,source_type,target_type):
  if source_type=='int' and target_type in ('float','doshomik','দশমিক'):
   temp=self.temp();self.lines.append(f'{temp} = float {operand}');return temp
  return operand
 def contains_call(self,node):
  if isinstance(node,Call):return True
  if is_dataclass(node):return any(self.contains_call(getattr(node,f.name)) for f in fields(node))
  if isinstance(node,(list,tuple)):return any(self.contains_call(item) for item in node)
  return False
 def snapshot(self,operand):
  temp=self.temp();self.lines.append(f'{temp} = {operand}');return temp
 def resolve(self,name):
  for scope in reversed(self.scopes):
   if name in scope:return scope[name]
  return name
 def declare(self,name):
  if any(name in scope for scope in self.scopes[:-1]):
   while True:
    self.scope_id+=1;alias=f'__bh_scope_{self.scope_id}'
    if alias not in self.reserved:self.reserved.add(alias);break
  else:alias=name
  self.scopes[-1][name]=alias;return alias
 def expr(self,n):
  if isinstance(n,Literal): return repr(n.value)
  if isinstance(n,Name): return self.resolve(n.name)
  if isinstance(n,Binary) and n.op in ('AND','OR'):
   left=self.expr(n.left);result=self.temp();branch=self.label('logic');end=self.label('endlogic')
   self.lines.append(f'ifFalse {left} goto {branch}')
   if n.op=='OR':
    self.lines.append(f'{result} = True');self.lines.append(f'goto {end}');self.lines.append(f'{branch}:');right=self.expr(n.right);self.lines.append(f'{result} = {right}')
   else:
    right=self.expr(n.right);self.lines.append(f'{result} = {right}');self.lines.append(f'goto {end}');self.lines.append(f'{branch}:');self.lines.append(f'{result} = False')
   self.lines.append(f'{end}:');return result
  if isinstance(n,Binary):
   a=self.expr(n.left)
   if isinstance(n.left,(Name,Index)) and self.contains_call(n.right):a=self.snapshot(a)
   b=self.expr(n.right); t=self.temp(); self.lines.append(f"{t} = {a} {n.op} {b}"); return t
  if isinstance(n,Unary): t=self.temp(); self.lines.append(f"{t} = {n.op} {self.expr(n.operand)}"); return t
  if isinstance(n,Call):
   params=self.signatures.get(n.callee,[]);a=[]
   for i,x in enumerate(n.args):
    arg=self.widen(self.expr(x),x.inferred_type,params[i] if i<len(params) else None)
    if isinstance(x,(Name,Index)) and any(self.contains_call(later) for later in n.args[i+1:]):arg=self.snapshot(arg)
    a.append(arg)
   self.lines.extend(f"param {x}" for x in a); t=self.temp(); self.lines.append(f"{t} = call {n.callee}, {len(a)}"); return t
  if isinstance(n,Index): return f"{self.expr(n.array)}[{self.expr(n.index)}]"
  return "?"
 def visit(self,n):
  if isinstance(n,Program):
   self.signatures={x.name:[typ for _,typ in x.params] for x in n.statements if isinstance(x,Function)}
   [self.visit(x) for x in n.statements]
  elif isinstance(n,Block):
   self.scopes.append({});[self.visit(x) for x in n.statements];self.scopes.pop()
  elif isinstance(n,VarDecl):
   name=self.declare(n.name)
   if len(self.scopes)==1:self.lines.append(f'global {name}')
   if n.size:self.lines.append(f"array {n.type_name} {name} {self.expr(n.size)}")
   else:self.lines.append(f"{name} = {self.widen(self.expr(n.value),n.value.inferred_type,n.type_name)}" if n.value else f"decl {n.type_name} {name}")
  elif isinstance(n,Assign):
   value=self.widen(self.expr(n.value),n.value.inferred_type,n.target.inferred_type)
   if isinstance(n.target,Index) and isinstance(n.value,(Name,Index)) and self.contains_call(n.target.index):value=self.snapshot(value)
   target=self.expr(n.target);self.lines.append(f"{target} {n.op} {value}")
  elif isinstance(n,Print): self.lines.append(f"print {self.expr(n.value)}")
  elif isinstance(n,Read): self.lines.append(f"read {self.expr(n.target)}")
  elif isinstance(n,Return): self.lines.append(f"return {self.widen(self.expr(n.value),n.value.inferred_type,self.return_type)}")
  elif isinstance(n,Function):
   self.scopes.append({});params=[self.declare(name) for name,_ in n.params]
   self.lines.append(f"func {n.name}({', '.join(params)}):");self.return_type=n.return_type;self.visit(n.body);self.return_type=None;self.lines.append("endfunc");self.scopes.pop()
  elif isinstance(n,If):
   alt,end=self.label("else"),self.label("endif"); self.lines.append(f"ifFalse {self.expr(n.condition)} goto {alt}"); self.visit(n.then_branch); self.lines.append(f"goto {end}"); self.lines.append(f"{alt}:"); self.visit(n.else_branch); self.lines.append(f"{end}:")
  elif isinstance(n,While):
   start,end=self.label("while"),self.label("endwhile");self.lines.append(f"{start}:");self.lines.append(f"ifFalse {self.expr(n.condition)} goto {end}");self.breaks.append(end);self.continues.append(start);self.visit(n.body);self.continues.pop();self.breaks.pop();self.lines.append(f"goto {start}");self.lines.append(f"{end}:")
  elif isinstance(n,For):
   initial=self.expr(n.start);self.scopes.append({});name=self.declare(n.name);start,step,end=self.label("for"),self.label("step"),self.label("endfor");self.lines.append(f"{name} = {initial}");limit=self.expr(n.end);saved=self.temp();self.lines.append(f"{saved} = {limit}");self.lines.append(f"{start}:");self.lines.append(f"ifFalse {name} < {saved} goto {end}");self.breaks.append(end);self.continues.append(step);self.visit(n.body);self.continues.pop();self.breaks.pop();self.lines.append(f"{step}:");self.lines.append(f"{name} += 1");self.lines.append(f"goto {start}");self.lines.append(f"{end}:");self.scopes.pop()
  elif isinstance(n,Break): self.lines.append(f"goto {self.breaks[-1]}")
  elif isinstance(n,Continue): self.lines.append(f"goto {self.continues[-1]}")
 def generate(self,p): self.reserve_names(p);self.visit(p); return self.lines
def generate(program): return IRGen().generate(program)
