"""Reference AST interpreter; mirrors Bhasha semantics portably."""
from ..ast_nodes import *
from collections import ChainMap
import re
import math
import sys
from decimal import Decimal
class ReturnSignal(Exception):
 def __init__(self,v):self.v=v
class BreakSignal(Exception):pass
class ContinueSignal(Exception):pass
def checked_index(array,index):
 if not 0<=index<len(array):raise IndexError(f'array index {index} out of bounds for length {len(array)}')
 return index
def format_value(value):
 if isinstance(value,bool):return str(value).lower()
 if isinstance(value,float):return format(value,'.6g')
 return str(value)
def parse_numeric_input(text,is_float):
 text=text.strip(' \t\r\n\v\f')
 pattern=r'[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)' if is_float else r'[+-]?[0-9]+'
 if len(text)>4094 or not re.fullmatch(pattern,text):raise ValueError('invalid or missing input')
 if is_float:
  result=float(text)
  if not math.isfinite(result) or (abs(result)<sys.float_info.min and Decimal(text)!=0):raise ValueError('input out of range')
  return result
 result=int(text)
 if not -(1<<63)<=result<(1<<63):raise ValueError('input out of range')
 return result
class VM:
 def __init__(self,output=None,input_fn=input,max_steps=None,output_fn=None):self.global_env={};self.output=output if output is not None else [];self.functions={};self.input_fn=input_fn;self.max_steps=max_steps;self.steps=0;self.output_fn=output_fn
 def tick(self):
  self.steps+=1
  if self.max_steps is not None and self.steps>self.max_steps:raise RuntimeError('execution step limit exceeded')
 def assign(self,env,name,value):
  scopes=env.maps if isinstance(env,ChainMap) else [env]
  for scope in scopes:
   if name in scope:scope[name]=value;return
  raise NameError(f'unknown variable {name}')
 def eval(self,n,env):
  self.tick()
  if isinstance(n,Literal):return n.value
  if isinstance(n,Name):return env[n.name]
  if isinstance(n,Index):
   array=self.eval(n.array,env);index=self.eval(n.index,env);return array[checked_index(array,index)]
  if isinstance(n,Unary):
   v=self.eval(n.operand,env);return -v if n.op=="-" else not v
  if isinstance(n,Binary):
   a=self.eval(n.left,env)
   if n.op=='AND' and not a:return False
   if n.op=='OR' and a:return True
   b=self.eval(n.right,env)
   def quotient():
    q=abs(a)//abs(b)
    return -q if (a<0) != (b<0) else q
   return {"+":lambda:a+b,"-":lambda:a-b,"*":lambda:a*b,"/":lambda:quotient() if type(a) is int and type(b) is int else a/b,"%":lambda:a-quotient()*b,"==":lambda:a==b,"!=":lambda:a!=b,"<":lambda:a<b,">":lambda:a>b,"<=":lambda:a<=b,">=":lambda:a>=b,"AND":lambda:a and b,"OR":lambda:a or b}[n.op]()
  if isinstance(n,Call):
   f=self.functions[n.callee];args={k:(float(result) if typ in ('doshomik','দশমিক') else result) for (k,typ),v in zip(f.params,n.args) for result in [self.eval(v,env)]};e=ChainMap(args,self.global_env)
   try:self.exec(f.body,e)
   except ReturnSignal as r:return float(r.v) if f.return_type in ('doshomik','দশমিক') else r.v
  raise RuntimeError("bad expression")
 def exec(self,n,env):
  if n is None:return
  self.tick()
  if isinstance(n,Program):
   for x in n.statements:
    if isinstance(x,Function):self.functions[x.name]=x
   for x in n.statements:
    if not isinstance(x,Function):self.exec(x,env)
  elif isinstance(n,Block):
   child=env.new_child() if isinstance(env,ChainMap) else ChainMap({},env)
   for x in n.statements:self.exec(x,child)
  elif isinstance(n,VarDecl):
   zero=0.0 if n.type_name in ('doshomik','দশমিক') else False if n.type_name=='huen' else 0
   value=[zero]*self.eval(n.size,env) if n.size else (self.eval(n.value,env) if n.value else zero)
   if not n.size and n.type_name in ('doshomik','দশমিক'):value=float(value)
   env[n.name]=value
  elif isinstance(n,Assign):
   v=self.eval(n.value,env)
   if isinstance(n.target,Name):
    old=env[n.target.name]
    def divide():
     if type(old) is int and type(v) is int:
      q=abs(old)//abs(v);return -q if (old<0)!=(v<0) else q
     return old/v
    result=v if n.op=="=" else {"+=":lambda:old+v,"-=":lambda:old-v,"*=":lambda:old*v,"/=":divide}[n.op]()
    if n.target.inferred_type=='float':result=float(result)
    self.assign(env,n.target.name,result)
   else:
    array=self.eval(n.target.array,env);index=self.eval(n.target.index,env);array[checked_index(array,index)]=float(v) if n.target.inferred_type=='float' else v
  elif isinstance(n,Print):
   value=self.eval(n.value,env)
   text=format_value(value);self.output.append(text)
   if self.output_fn is not None:self.output_fn(text)
  elif isinstance(n,Read):
   value=self.input_fn()
   self.assign(env,n.target.name,parse_numeric_input(value,n.target.inferred_type=='float'))
  elif isinstance(n,If):self.exec(n.then_branch if self.eval(n.condition,env) else n.else_branch,env)
  elif isinstance(n,While):
   while self.eval(n.condition,env):
    try:self.exec(n.body,env)
    except BreakSignal:break
    except ContinueSignal:continue
  elif isinstance(n,For):
   start=self.eval(n.start,env);loop_env=env.new_child() if isinstance(env,ChainMap) else ChainMap({},env);loop_env[n.name]=start;end=self.eval(n.end,loop_env)
   while loop_env[n.name]<end:
    try:self.exec(n.body,loop_env)
    except BreakSignal:break
    except ContinueSignal:pass
    self.assign(loop_env,n.name,loop_env[n.name]+1)
  elif isinstance(n,Return):raise ReturnSignal(self.eval(n.value,env))
  elif isinstance(n,Break):raise BreakSignal
  elif isinstance(n,Continue):raise ContinueSignal
def run(program):v=VM();v.exec(program,v.global_env);return "\n".join(v.output)+("\n" if v.output else "")
