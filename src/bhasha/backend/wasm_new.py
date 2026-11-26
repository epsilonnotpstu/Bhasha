"""WAT backend for the supported numeric subset of Bhasha.

The generated module exports `run() -> i32/f64`; its return is the final `dekhao`
value. This keeps the target dependency-free while remaining executable after
conversion with a standard WAT tool.
"""
from ..ast_nodes import *
import re
class WasmError(ValueError): pass
class Emitter:
 def __init__(self,host_io=False):self.locals=set();self.local_types={};self.lines=[];self.depth=0;self.loop=0;self.loops=[];self.scopes=[{}];self.local_id=0;self.functions={};self.signatures={};self.globals={};self.global_types={};self.arrays={};self.local_arrays={};self.frame_size=0;self.uses_stack=[False];self.in_function=False;self.output_type='i32';self.return_type='i32';self.host_io=host_io;self.strings=[];self.memory_offset=[0]
 def emit(self,s):self.lines.append('    '*self.depth+s)
 def resolve(self,name):
  for scope in reversed(self.scopes):
   if name in scope:return scope[name]
  if name in self.globals:return self.globals[name]
  raise WasmError(f'unknown local {name}')
 def access(self,name,op):
  for scope in reversed(self.scopes):
   if name in scope:return f'local.{op} ${scope[name]}'
  if name in self.globals:return f'global.{op} ${self.globals[name]}'
  raise WasmError(f'unknown variable {name}')
 def declare(self,name,typ='i32'):
  if name=='out' or name in self.locals or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name):
   self.local_id+=1;alias=f'.user{self.local_id}'
  else:alias=name
  self.scopes[-1][name]=alias;self.locals.add(alias);self.local_types[alias]=typ;return alias
 def numeric(self,node,typ):
  result=self.expr(node)
  if typ=='f64' and node.inferred_type=='int':result+=['f64.convert_i32_s']
  return result
 def expr(self,n):
  if isinstance(n,Literal) and isinstance(n.value,int):return [f'i32.const {int(n.value)}']
  if isinstance(n,Literal) and isinstance(n.value,float):return [f'f64.const {n.value!r}']
  if isinstance(n,Name):return [self.access(n.name,'get')]
  if isinstance(n,Index):return self.address(n)+[('f64' if n.inferred_type=='float' else 'i32')+'.load']
  if isinstance(n,Call):
   if n.callee not in self.functions:raise WasmError(f'unknown function {n.callee}')
   instructions=[]
   for arg,typ in zip(n.args,self.signatures[n.callee]):instructions.extend(self.numeric(arg,typ))
   return instructions+[f'call ${self.functions[n.callee]}']
  if isinstance(n,Unary) and n.op=='-':return self.expr(n.operand)+['f64.neg'] if n.inferred_type=='float' else ['i32.const 0']+self.expr(n.operand)+['i32.sub']
  if isinstance(n,Unary) and n.op in ('NOT','!'):return self.expr(n.operand)+['i32.eqz']
  if isinstance(n,Binary) and n.op=='AND':return self.expr(n.left)+['if (result i32)']+self.expr(n.right)+['else','i32.const 0','end']
  if isinstance(n,Binary) and n.op=='OR':return self.expr(n.left)+['if (result i32)','i32.const 1','else']+self.expr(n.right)+['end']
  if isinstance(n,Binary) and n.op in ('+','-','*','/','%','==','!=','<','>','<=','>='):
   if n.left.inferred_type=='float' or n.right.inferred_type=='float':
    op={'+':'add','-':'sub','*':'mul','/':'div','==':'eq','!=':'ne','<':'lt','>':'gt','<=':'le','>=':'ge'}.get(n.op)
    if op is None:raise WasmError('unsupported floating-point operation')
    return self.numeric(n.left,'f64')+self.numeric(n.right,'f64')+(['call $.float_div'] if op=='div' else [f'f64.{op}'])
   op={'+':'add','-':'sub','*':'mul','/':'div_s','%':'rem_s','==':'eq','!=':'ne','<':'lt_s','>':'gt_s','<=':'le_s','>=':'ge_s'}[n.op]
   return self.expr(n.left)+self.expr(n.right)+[f'i32.{op}']
  raise WasmError('WAT supports only integer variables and arithmetic')
 def address(self,index):
  if not isinstance(index.array,Name):raise WasmError('unsupported WAT array expression')
  name=index.array.name;alias=next((scope[name] for scope in reversed(self.scopes) if name in scope),None)
  if alias is not None:
   if alias not in self.local_arrays:raise WasmError('not a WAT array')
   base,size,width=self.local_arrays[alias];base_code=['local.get $.frame',f'i32.const {base}','i32.add']
  elif name in self.arrays:
   base,size,width=self.arrays[name];base_code=[f'i32.const {base}']
  else:raise WasmError('unknown WAT array')
  return base_code+self.expr(index.index)+[f'i32.const {size}','call $.array_index',f'i32.const {width}','i32.mul','i32.add']
 def add_expr(self,n,typ=None):
  for line in (self.numeric(n,typ) if typ else self.expr(n)):self.emit(line)
 def statement(self,n):
  if isinstance(n,Block):
   self.scopes.append({})
   for x in n.statements:self.statement(x)
   self.scopes.pop()
  elif isinstance(n,VarDecl):
   if n.type_name not in ('purno','পূর্ণ','huen','doshomik','দশমিক'):raise WasmError('unsupported WAT declaration')
   if n.size:
    if not isinstance(n.size,Literal) or type(n.size.value) is not int or n.size.value<=0:raise WasmError('WAT arrays require a positive constant integer size')
    width=8 if n.type_name in ('doshomik','দশমিক') else 4;self.frame_size=(self.frame_size+width-1)//width*width;base=self.frame_size;self.frame_size+=width*n.size.value
    if self.frame_size>=2**31:raise WasmError('WAT local array frame is too large')
    alias=self.declare(n.name);self.local_arrays[alias]=(base,n.size.value,width);self.uses_stack[0]=True
    self.emit('local.get $.frame');self.emit(f'i32.const {base}');self.emit('i32.add');self.emit('i32.const 0');self.emit(f'i32.const {width*n.size.value}');self.emit('memory.fill');return
   typ='f64' if n.type_name in ('doshomik','দশমিক') else 'i32';name=self.declare(n.name,typ)
   if n.value:self.add_expr(n.value,typ)
   else:self.emit(f'{typ}.const 0')
   self.emit(f'local.set ${name}')
  elif isinstance(n,Assign):
   if isinstance(n.target,Index):
    if n.op!='=':raise WasmError('WAT compound array assignment is not implemented')
    self.local_id+=1;temp=f'.store{self.local_id}';typ='f64' if n.target.inferred_type=='float' else 'i32';self.locals.add(temp);self.local_types[temp]=typ;self.add_expr(n.value,typ);self.emit(f'local.set ${temp}')
    for line in self.address(n.target):self.emit(line)
    self.emit(f'local.get ${temp}');self.emit(f'{typ}.store');return
   if not isinstance(n.target,Name):raise WasmError('invalid assignment target')
   typ='f64' if n.target.inferred_type=='float' else 'i32'
   if n.op=='=':self.add_expr(n.value,typ)
   elif n.op in ('+=','-=','*=','/='):
    self.emit(self.access(n.target.name,'get'));self.add_expr(n.value,typ)
    if typ=='f64':self.emit('call $.float_div' if n.op=='/=' else 'f64.'+{'+=':'add','-=':'sub','*=':'mul'}[n.op])
    else:self.emit('i32.'+{'+=':'add','-=':'sub','*=':'mul','/=':'div_s'}[n.op])
   else:raise WasmError('unsupported assignment')
   self.emit(self.access(n.target.name,'set'))
  elif isinstance(n,Print):
   if self.host_io:
    if isinstance(n.value,Literal) and isinstance(n.value.value,str):
     data=n.value.value.encode('utf8');offset=self.memory_offset[0];self.memory_offset[0]+=len(data);self.strings.append((offset,data));self.emit(f'i32.const {offset}');self.emit(f'i32.const {len(data)}');self.emit('call $.print_string')
    else:
     self.add_expr(n.value);typ={'float':'f64','bool':'bool','int':'i32'}.get(n.value.inferred_type)
     if typ is None:raise WasmError('unsupported WAT print type')
     self.emit(f'call $.print_{typ}')
   else:
    if self.in_function:raise WasmError('WAT printing inside functions requires host I/O')
    typ='f64' if n.value.inferred_type=='float' else 'i32'
    if typ!=self.output_type:raise WasmError('WAT run cannot return mixed output types')
    self.add_expr(n.value);self.emit('local.set $out')
  elif isinstance(n,Read):
   if not self.host_io:raise WasmError('WAT input requires host I/O')
   typ='f64' if n.target.inferred_type=='float' else 'i32';self.emit(f'call $.read_{typ}');self.emit(self.access(n.target.name,'set'))
  elif isinstance(n,Return):self.add_expr(n.value,self.return_type);self.emit('@@restore_frame@@');self.emit('return')
  elif isinstance(n,If):
   self.add_expr(n.condition);self.emit('if');self.depth+=1;self.statement(n.then_branch);self.depth-=1
   if n.else_branch:self.emit('else');self.depth+=1;self.statement(n.else_branch);self.depth-=1
   self.emit('end')
  elif isinstance(n,While):
   self.loop+=1;label=str(self.loop);self.emit(f'block $break{label}');self.depth+=1;self.emit(f'loop $loop{label}');self.depth+=1;self.add_expr(n.condition);self.emit('i32.eqz');self.emit(f'br_if $break{label}');self.loops.append((f'loop{label}',f'break{label}'));self.statement(n.body);self.loops.pop();self.emit(f'br $loop{label}');self.depth-=1;self.emit('end');self.depth-=1;self.emit('end')
  elif isinstance(n,For):
   self.add_expr(n.start);self.scopes.append({});name=self.declare(n.name);self.emit(f'local.set ${name}')
   self.loop+=1;label=str(self.loop);limit=f'.limit{label}';self.locals.add(limit);self.add_expr(n.end);self.emit(f'local.set ${limit}');self.emit(f'block $break{label}');self.depth+=1;self.emit(f'loop $loop{label}');self.depth+=1;self.emit(f'local.get ${name}');self.emit(f'local.get ${limit}');self.emit('i32.ge_s');self.emit(f'br_if $break{label}');self.emit(f'block $continue{label}');self.depth+=1;self.loops.append((f'continue{label}',f'break{label}'));self.statement(n.body);self.loops.pop();self.depth-=1;self.emit('end');self.emit(f'local.get ${name}');self.emit('i32.const 1');self.emit('i32.add');self.emit(f'local.set ${name}');self.emit(f'br $loop{label}');self.depth-=1;self.emit('end');self.depth-=1;self.emit('end');self.scopes.pop()
  elif isinstance(n,Break):
   if not self.loops:raise WasmError('break outside loop')
   self.emit(f'br ${self.loops[-1][1]}')
  elif isinstance(n,Continue):
   if not self.loops:raise WasmError('continue outside loop')
   self.emit(f'br ${self.loops[-1][0]}')
  else:raise WasmError(f'WAT does not support {type(n).__name__}')
 def generate(self,p):
  funcs=[s for s in p.statements if isinstance(s,Function)]
  self.functions={f.name:f'.fn{i}' for i,f in enumerate(funcs)}
  self.signatures={f.name:['f64' if typ in ('doshomik','দশমিক') else 'i32' for _,typ in f.params] for f in funcs}
  arrays_=[s for s in p.statements if isinstance(s,VarDecl) and s.size]
  offset=0
  for a in arrays_:
   if a.type_name not in ('purno','পূর্ণ','huen','doshomik','দশমিক') or not isinstance(a.size,Literal) or type(a.size.value) is not int or a.size.value<=0:raise WasmError('WAT arrays require a positive constant integer size')
   width=8 if a.type_name in ('doshomik','দশমিক') else 4
   offset=(offset+width-1)//width*width;self.arrays[a.name]=(offset,a.size.value,width);offset+=width*a.size.value
  self.memory_offset[0]=offset
  globals_=[s for s in p.statements if isinstance(s,VarDecl) and not s.size] if funcs else []
  for i,g in enumerate(globals_):
   if g.type_name not in ('purno','পূর্ণ','huen','doshomik','দশমিক') or g.size:raise WasmError('unsupported WAT global type')
   self.globals[g.name]=f'.global{i}';self.global_types[g.name]='f64' if g.type_name in ('doshomik','দশমিক') else 'i32'
  compiled=[]
  for f in funcs:
   if f.return_type not in ('purno','পূর্ণ','huen','doshomik','দশমিক') or any(t not in ('purno','পূর্ণ','huen','doshomik','দশমিক') for _,t in f.params):raise WasmError('unsupported WAT function signature')
   child=Emitter(self.host_io);child.functions=self.functions;child.signatures=self.signatures;child.globals=self.globals;child.global_types=self.global_types;child.arrays=self.arrays;child.strings=self.strings;child.memory_offset=self.memory_offset;child.uses_stack=self.uses_stack;child.in_function=True;child.return_type='f64' if f.return_type in ('doshomik','দশমিক') else 'i32';params=[child.declare(name,typ) for (name,_),typ in zip(f.params,self.signatures[f.name])]
   child.statement(f.body)
   local_names=sorted(child.locals-set(params))
   signature=' '.join(f'(param ${name} {child.local_types[name]})' for name in params)
   declarations=[f'    (local ${name} {child.local_types.get(name,"i32")})' for name in local_names]
   # out is required because the shared statement emitter handles dekhao.
   frame_decl=['    (local $.frame i32)'] if child.frame_size else []
   prologue=[f'    i32.const {child.frame_size}','    call $.alloc','    local.set $.frame'] if child.frame_size else []
   lines=[line.replace('@@restore_frame@@','local.get $.frame\n    global.set $.stack' if child.frame_size else 'nop') for line in child.lines]
   compiled.append('\n'.join([f'  (func ${self.functions[f.name]} {signature} (result {child.return_type})','    (local $out i32)']+frame_decl+declarations+prologue+lines+['    unreachable','  )']))
  # The minimal host contract returns only the final printed numeric value.
  def output_types(node):
   if isinstance(node,Function):return set()
   if isinstance(node,Print):return {'f64' if node.value.inferred_type=='float' else 'i32'}
   if isinstance(node,Node):
    from dataclasses import fields
    return set().union(*(output_types(getattr(node,f.name)) for f in fields(node)))
   if isinstance(node,list):return set().union(*(output_types(x) for x in node))
   return set()
  types=output_types(p) if not self.host_io else set()
  if len(types)>1:raise WasmError('WAT run cannot return mixed output types')
  self.output_type=next(iter(types),'i32')
  # Declarations are discovered while lowering, so buffer body then insert locals.
  for s in p.statements:
   if isinstance(s,VarDecl) and s in arrays_:
    base,size,width=self.arrays[s.name];self.emit(f'i32.const {base}');self.emit('i32.const 0');self.emit(f'i32.const {size*width}');self.emit('memory.fill')
   elif isinstance(s,VarDecl) and s in globals_:
    if s.value:self.add_expr(s.value,self.global_types[s.name])
    else:self.emit(f'{self.global_types[s.name]}.const 0')
    self.emit(f'global.set ${self.globals[s.name]}')
   elif not isinstance(s,Function):self.statement(s)
  body=self.lines;locals=[f'    (local $out {self.output_type})']+[f'    (local ${n} {self.local_types.get(n,"i32")})' for n in sorted(self.locals)]
  globals_wat=[f'  (global ${name} (mut {self.global_types[key]}) ({self.global_types[key]}.const 0))' for key,name in self.globals.items()]
  memory=[]
  if arrays_ or self.host_io or self.uses_stack[0]:
   pages=max(1,(max(offset,self.memory_offset[0])+65535)//65536)
   memory=[f'  (memory (export "memory") {pages})' if self.host_io else f'  (memory {pages})']
   if arrays_ or self.uses_stack[0]:memory+=['  (func $.array_index (param $index i32) (param $size i32) (result i32)','    local.get $index','    local.get $size','    i32.ge_u','    if','      unreachable','    end','    local.get $index','  )']
  data_segments=[f'  (data (i32.const {start}) "'+''.join(f'\\{byte:02x}' for byte in data)+'")' for start,data in self.strings]
  imports=[]
  if self.host_io:
   imports=['  (import "host" "print_i32" (func $.print_i32 (param i32)))','  (import "host" "print_bool" (func $.print_bool (param i32)))','  (import "host" "print_f64" (func $.print_f64 (param f64)))','  (import "host" "print_string" (func $.print_string (param i32 i32)))','  (import "host" "read_i32" (func $.read_i32 (result i32)))','  (import "host" "read_f64" (func $.read_f64 (result f64)))']
  helper=['  (func $.float_div (param $a f64) (param $b f64) (result f64)','    local.get $b','    f64.const 0','    f64.eq','    if','      unreachable','    end','    local.get $a','    local.get $b','    f64.div','  )']
  if self.uses_stack[0]:
   stack_base=(self.memory_offset[0]+7)//8*8;globals_wat.append(f'  (global $.stack (mut i32) (i32.const {stack_base}))')
   helper+=['  (func $.alloc (param $size i32) (result i32) (local $base i32) (local $end i32) (local $pages i32)', '    global.get $.stack','    local.tee $base','    local.get $size','    i32.add','    local.tee $end','    local.get $base','    i32.lt_u','    if','      unreachable','    end','    local.get $end','    i32.const 1','    i32.sub','    i32.const 16','    i32.shr_u','    i32.const 1','    i32.add','    local.tee $pages','    memory.size','    i32.gt_u','    if','      local.get $pages','      memory.size','      i32.sub','      memory.grow','      i32.const -1','      i32.eq','      if','        unreachable','      end','    end','    local.get $end','    global.set $.stack','    local.get $base','  )']
  frame_decl=['    (local $.frame i32)'] if self.frame_size else []
  prologue=[f'    i32.const {stack_base}','    global.set $.stack'] if self.uses_stack[0] else []
  if self.frame_size:prologue += [f'    i32.const {self.frame_size}','    call $.alloc','    local.set $.frame']
  return '(module\n'+'\n'.join(imports+memory+data_segments+globals_wat+helper+compiled+[f'  (func (export "run") (result {self.output_type})']+locals+frame_decl+prologue+body+['    local.get $out','  )',' )'])+'\n'
def emit_wat(program,host_io=False):return Emitter(host_io=host_io).generate(program)
