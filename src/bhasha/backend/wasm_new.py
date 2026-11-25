"""WAT backend for the integer imperative subset of Bhasha.

The generated module exports `run() -> i32`; its return is the final `dekhao`
value. This keeps the target dependency-free while remaining executable after
conversion with a standard WAT tool.
"""
from ..ast_nodes import *
class WasmError(ValueError): pass
class Emitter:
 def __init__(self):self.locals=set();self.lines=[];self.depth=0;self.loop=0
 def emit(self,s):self.lines.append('    '*self.depth+s)
 def expr(self,n):
  if isinstance(n,Literal) and isinstance(n.value,int):return [f'i32.const {n.value}']
  if isinstance(n,Name):return [f'local.get ${n.name}']
  if isinstance(n,Unary) and n.op=='-':return ['i32.const 0']+self.expr(n.operand)+['i32.sub']
  if isinstance(n,Binary) and n.op in ('+','-','*','/','%','==','!=','<','>','<=','>='):
   op={'+':'add','-':'sub','*':'mul','/':'div_s','%':'rem_s','==':'eq','!=':'ne','<':'lt_s','>':'gt_s','<=':'le_s','>=':'ge_s'}[n.op]
   return self.expr(n.left)+self.expr(n.right)+[f'i32.{op}']
  raise WasmError('WAT supports only integer variables and arithmetic')
 def add_expr(self,n):
  for line in self.expr(n):self.emit(line)
 def statement(self,n):
  if isinstance(n,Block):
   for x in n.statements:self.statement(x)
  elif isinstance(n,VarDecl):
   if n.type_name not in ('purno','পূর্ণ') or n.size:raise WasmError('WAT supports scalar purno declarations only')
   self.locals.add(n.name)
   if n.value:self.add_expr(n.value);self.emit(f'local.set ${n.name}')
  elif isinstance(n,Assign):
   if not isinstance(n.target,Name):raise WasmError('WAT array assignment is not implemented')
   if n.op=='=':self.add_expr(n.value)
   elif n.op in ('+=','-=','*=','/='):
    self.emit(f'local.get ${n.target.name}');self.add_expr(n.value);self.emit('i32.'+{'+=':'add','-=':'sub','*=':'mul','/=':'div_s'}[n.op])
   else:raise WasmError('unsupported assignment')
   self.emit(f'local.set ${n.target.name}')
  elif isinstance(n,Print):self.add_expr(n.value);self.emit('local.set $out')
  elif isinstance(n,If):
   self.add_expr(n.condition);self.emit('if');self.depth+=1;self.statement(n.then_branch);self.depth-=1
   if n.else_branch:self.emit('else');self.depth+=1;self.statement(n.else_branch);self.depth-=1
   self.emit('end')
  elif isinstance(n,While):
   self.loop+=1;label=str(self.loop);self.emit(f'block $break{label}');self.depth+=1;self.emit(f'loop $loop{label}');self.depth+=1;self.add_expr(n.condition);self.emit('i32.eqz');self.emit(f'br_if $break{label}');self.statement(n.body);self.emit(f'br $loop{label}');self.depth-=1;self.emit('end');self.depth-=1;self.emit('end')
  elif isinstance(n,For):
   self.locals.add(n.name);self.add_expr(n.start);self.emit(f'local.set ${n.name}')
   self.loop+=1;label=str(self.loop);self.emit(f'block $break{label}');self.depth+=1;self.emit(f'loop $loop{label}');self.depth+=1;self.emit(f'local.get ${n.name}');self.add_expr(n.end);self.emit('i32.ge_s');self.emit(f'br_if $break{label}');self.statement(n.body);self.emit(f'local.get ${n.name}');self.emit('i32.const 1');self.emit('i32.add');self.emit(f'local.set ${n.name}');self.emit(f'br $loop{label}');self.depth-=1;self.emit('end');self.depth-=1;self.emit('end')
  else:raise WasmError(f'WAT does not support {type(n).__name__}')
 def generate(self,p):
  # Declarations are discovered while lowering, so buffer body then insert locals.
  for s in p.statements:self.statement(s)
  body=self.lines;locals=['    (local $out i32)']+[f'    (local ${n} i32)' for n in sorted(self.locals)]
  return '(module\n  (func (export "run") (result i32)\n'+'\n'.join(locals+body+['    local.get $out','  )',' )'])+'\n'
def emit_wat(program):return Emitter().generate(program)
