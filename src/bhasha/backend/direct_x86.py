"""Hand-written Linux x86-64 backend for Bhasha's integer straight-line subset.

It deliberately has a narrow, explicit contract. Unsupported AST nodes raise
`DirectX86Error`, allowing the proven GCC backend to remain the fallback.
"""
from pathlib import Path
import subprocess
import struct
import tempfile
from ..ast_nodes import *
from .input_runtime import INPUT_RUNTIME
class DirectX86Error(ValueError): pass
class Emitter:
 def __init__(self):self.lines=['.intel_syntax noprefix','.global main','.extern printf','.section .rodata','fmt: .string "%ld\\n"','.text','main:','  push rbp','  mov rbp, rsp','  sub rsp, 128'];self.slots={};self.arrays={};self.next=0;self.labels=0;self.loops=[];self.strings=[];self.scopes=[{}];self.globals={};self.global_data=[];self.array_sizes={};self.global_array_sizes={};self.signatures={};self.function_labels={};self.return_type=None
 def label(self):self.labels+=1;return f'.L{self.labels}'
 def call(self,target):
  # r12 is callee-saved under the System V ABI. Preserve the original stack
  # while rounding down for calls made inside nested expressions.
  self.lines+=['  push r12','  mov r12, rsp','  and rsp, -16',f'  call {target}','  mov rsp, r12','  pop r12']
 def slot(self,name,declare=False):
  if not declare:
   for scope in reversed(self.scopes):
    if name in scope:return scope[name]
  if declare and len(self.scopes)==1 and name in self.globals:return self.globals[name]
  self.next+=8;slot=f'[rbp-{self.next}]';self.scopes[-1][name]=slot;return slot
 def checked_array_address(self,node):
  address=self.slot(node.array.name)
  if address not in self.array_sizes:raise DirectX86Error('array size unavailable')
  self.expr(node.index);self.lines += [f'  cmp rax, {self.array_sizes[address]}','  jae .Lbounds_error',f'  lea rcx, {address}']
 def float_expr(self,node):
  self.expr(node)
  if node.inferred_type=='int':self.lines+=['  cvtsi2sd xmm0, rax','  movq rax, xmm0']
 def expr(self,n):
  if isinstance(n,Literal) and isinstance(n.value,int):self.lines.append(f'  mov rax, {int(n.value)}')
  elif isinstance(n,Literal) and isinstance(n.value,float):
   bits=struct.unpack('<Q',struct.pack('<d',n.value))[0];self.lines.append(f'  mov rax, {bits}')
  elif isinstance(n,Literal) and isinstance(n.value,str):
   label=f'.Lstring{len(self.strings)}';self.strings.append((label,n.value));self.lines.append(f'  lea rax, [rip+{label}]')
  elif isinstance(n,Unary) and n.op in ('-','NOT','!'):
   self.expr(n.operand)
   if n.op=='-' and n.inferred_type=='float':self.lines+=['  mov rcx, 0x8000000000000000','  xor rax, rcx']
   elif n.op=='-':self.lines.append('  neg rax')
   else:self.lines+=['  test rax, rax','  sete al','  movzx rax, al']
  elif isinstance(n,Name):self.lines.append(f'  mov rax, QWORD PTR {self.slot(n.name)}')
  elif isinstance(n,Index) and isinstance(n.array,Name):
   self.checked_array_address(n);self.lines.append('  mov rax, QWORD PTR [rcx+rax*8]')
  elif isinstance(n,Binary) and n.op in ('AND','OR'):
   end=self.label();self.expr(n.left);self.lines+=['  test rax, rax',f'  {"jz" if n.op=="AND" else "jnz"} {end}'];self.expr(n.right);self.lines.append(f'{end}:')
  elif isinstance(n,Binary) and n.inferred_type=='float' and n.op in ('+','-','*','/'):
   self.float_expr(n.left);self.lines.append('  push rax');self.float_expr(n.right);self.lines+=['  movq xmm1, rax','  pop rax','  movq xmm0, rax']
   if n.op=='/':
    nonzero=self.label();self.lines+=['  pxor xmm2, xmm2','  ucomisd xmm1, xmm2',f'  jp {nonzero}','  je .Ldivision_error',f'{nonzero}:']
   self.lines.append('  '+{'+':'addsd','-':'subsd','*':'mulsd','/':'divsd'}[n.op]+' xmm0, xmm1');self.lines.append('  movq rax, xmm0')
  elif isinstance(n,Binary) and n.op in ('==','!=','<','>','<=','>=') and (n.left.inferred_type=='float' or n.right.inferred_type=='float'):
   self.float_expr(n.left);self.lines.append('  push rax');self.float_expr(n.right);self.lines+=['  movq xmm1, rax','  pop rax','  movq xmm0, rax','  ucomisd xmm0, xmm1','  mov eax, 0']
   self.lines.append('  '+{'==':'sete','!=':'setne','<':'setb','>':'seta','<=':'setbe','>=':'setae'}[n.op]+' al')
   if n.op in ('==','<','<='):self.lines+=['  setnp dl','  and al, dl']
   elif n.op=='!=':self.lines+=['  setp dl','  or al, dl']
  elif isinstance(n,Binary) and n.op in ('+','-','*','/','%','==','!=','<','>','<=','>='):
   if n.left.inferred_type=='float' or n.right.inferred_type=='float':raise DirectX86Error('unsupported direct x86 float operation')
   self.expr(n.left);self.lines.append('  push rax');self.expr(n.right);self.lines.append('  pop rcx')
   if n.op=='+':self.lines.append('  add rax, rcx')
   elif n.op=='-':self.lines.append('  sub rcx, rax');self.lines.append('  mov rax, rcx')
   elif n.op=='*':self.lines.append('  imul rax, rcx')
   elif n.op in ('/','%'):
    self.lines+=['  test rax, rax','  jz .Ldivision_error','  mov r8, rax','  mov rax, rcx','  cqo','  idiv r8']
    if n.op=='%':self.lines.append('  mov rax, rdx')
   else:
    self.lines.append('  cmp rcx, rax');self.lines.append('  mov eax, 0')
    self.lines.append({'==':'  sete al','!=':'  setne al','<':'  setl al','>':'  setg al','<=':'  setle al','>=':'  setge al'}[n.op])
  elif isinstance(n,Call):
   types=self.signatures[n.callee];int_regs=['rdi','rsi','rdx','rcx','r8','r9'];ii=0;fi=0;registers=[]
   for arg,typ in zip(n.args,types):
    if typ in ('doshomik','দশমিক'):
     self.float_expr(arg);registers.append(('float',f'xmm{fi}' if fi<8 else None));fi+=1
    else:
     self.expr(arg);registers.append(('int',int_regs[ii] if ii<6 else None));ii+=1
    self.lines.append('  push rax')
   stack_count=sum(reg is None for _,reg in registers);stack_size=((stack_count*8+15)//16)*16
   self.lines+=['  push r12','  mov r12, rsp','  and rsp, -16']
   if stack_size:self.lines.append(f'  sub rsp, {stack_size}')
   stack_index=0
   for i,(typ,reg) in enumerate(registers):
    self.lines.append(f'  mov rax, QWORD PTR [r12+{8+8*(len(registers)-1-i)}]')
    if reg is None:self.lines.append(f'  mov QWORD PTR [rsp+{stack_index*8}], rax');stack_index+=1
    elif typ=='float':self.lines.append(f'  movq {reg}, rax')
    else:self.lines.append(f'  mov {reg}, rax')
   self.lines+= [f'  call {self.function_labels[n.callee]}','  mov rsp, r12','  pop r12']
   if registers:self.lines.append(f'  add rsp, {len(registers)*8}')
   if n.inferred_type=='float':self.lines.append('  movq rax, xmm0')
  else:raise DirectX86Error(f'direct x86 unsupported expression: {type(n).__name__}')
 def stmt(self,n):
  if isinstance(n,VarDecl) and n.size and n.type_name in ('purno','পূর্ণ','doshomik','দশমিক','huen') and isinstance(n.size,Literal):
   size=int(n.size.value)
   if size<=0:raise DirectX86Error('array size must be positive')
   if len(self.scopes)==1 and n.name in self.globals:address=self.globals[n.name]
   else:
    self.next+=8*size;address=f'[rbp-{self.next}]';self.scopes[-1][n.name]=address
   self.array_sizes[address]=size
   self.lines.append(f'  lea rcx, {address}')
   for i in range(size):self.lines.append(f'  mov QWORD PTR [rcx+{i*8}], 0')
  elif isinstance(n,VarDecl) and not n.size and n.type_name in ('purno','পূর্ণ','huen','doshomik','দশমিক'):
   address=self.slot(n.name,declare=True)
   if n.type_name in ('doshomik','দশমিক') and n.value:self.float_expr(n.value)
   else:self.expr(n.value or Literal(value=0))
   self.lines.append(f'  mov QWORD PTR {address}, rax')
  elif isinstance(n,Assign) and isinstance(n.target,Name) and n.op in ('=','+=','-=','*=','/='):
   value=n.value if n.op=='=' else Binary(inferred_type=n.target.inferred_type,left=n.target,op=n.op[0],right=n.value)
   if n.target.inferred_type=='float':self.float_expr(value)
   else:self.expr(value)
   self.lines.append(f'  mov QWORD PTR {self.slot(n.target.name)}, rax')
  elif isinstance(n,Assign) and isinstance(n.target,Index) and isinstance(n.target.array,Name) and n.op=='=':
   if n.target.inferred_type=='float':self.float_expr(n.value)
   else:self.expr(n.value)
   self.lines.append('  push rax');self.checked_array_address(n.target);self.lines+=['  pop rdx','  mov QWORD PTR [rcx+rax*8], rdx']
  elif isinstance(n,Print):
   self.expr(n.value)
   if n.value.inferred_type=='bool':
    self.lines+=['  test rax, rax','  lea rsi, [rip+bool_false]','  lea rcx, [rip+bool_true]','  cmovne rsi, rcx','  lea rdi, [rip+fmt_string]','  xor eax, eax']
   elif n.value.inferred_type=='string':self.lines+=['  mov rsi, rax','  lea rdi, [rip+fmt_string]','  xor eax, eax']
   elif n.value.inferred_type=='float':self.lines+=['  movq xmm0, rax','  lea rdi, [rip+fmt_float]','  mov eax, 1']
   else:self.lines+=['  mov rsi, rax','  lea rdi, [rip+fmt]','  xor eax, eax']
   self.call('printf')
  elif isinstance(n,Read) and isinstance(n.target,Name) and n.target.inferred_type in ('int','float'):
   reader='bh_read_float' if n.target.inferred_type=='float' else 'bh_read_int'
   self.lines.append(f'  lea rdi, {self.slot(n.target.name)}');self.call(reader);self.lines+=['  cmp eax, 1','  jne .Linput_error']
  elif isinstance(n,If):
   alt,end=self.label(),self.label();self.expr(n.condition);self.lines+=['  test rax, rax',f'  jz {alt}'];self.stmt(n.then_branch);self.lines+= [f'  jmp {end}',f'{alt}:']
   if n.else_branch:self.stmt(n.else_branch)
   self.lines.append(f'{end}:')
  elif isinstance(n,Block):
   self.scopes.append({})
   for s in n.statements:self.stmt(s)
   self.scopes.pop()
  elif isinstance(n,While):
   start,end=self.label(),self.label();self.lines.append(f'{start}:');self.expr(n.condition);self.lines+=['  test rax, rax',f'  jz {end}'];self.loops.append((start,end));self.stmt(n.body);self.loops.pop();self.lines+= [f'  jmp {start}',f'{end}:']
  elif isinstance(n,For):
   self.expr(n.start);self.scopes.append({});self.lines.append(f'  mov QWORD PTR {self.slot(n.name,declare=True)}, rax');start,step,end=self.label(),self.label(),self.label();limit=self.slot(f'@limit{self.labels}');self.expr(n.end);self.lines.append(f'  mov QWORD PTR {limit}, rax');self.lines.append(f'{start}:');self.lines.append(f'  mov rax, QWORD PTR {self.slot(n.name)}');self.lines.append(f'  cmp rax, QWORD PTR {limit}');self.lines.append(f'  jge {end}');self.loops.append((step,end));self.stmt(n.body);self.loops.pop();self.lines+= [f'{step}:',f'  add QWORD PTR {self.slot(n.name)}, 1',f'  jmp {start}',f'{end}:'];self.scopes.pop()
  elif isinstance(n,Break):self.lines.append(f'  jmp {self.loops[-1][1]}')
  elif isinstance(n,Continue):self.lines.append(f'  jmp {self.loops[-1][0]}')
  elif isinstance(n,Return):
   if self.return_type in ('doshomik','দশমিক'):self.float_expr(n.value);self.lines.append('  movq xmm0, rax')
   else:self.expr(n.value)
   self.lines+=['  leave','  ret']
  else:raise DirectX86Error(f'direct x86 unsupported statement: {type(n).__name__}')
 def generate(self,p):
  self.signatures={f.name:[typ for _,typ in f.params] for f in p.statements if isinstance(f,Function)}
  self.function_labels={f.name:f'bh_fn_{i}' for i,f in enumerate(x for x in p.statements if isinstance(x,Function))}
  for i,node in enumerate(x for x in p.statements if isinstance(x,VarDecl)):
   if node.size and (not isinstance(node.size,Literal) or type(node.size.value) is not int or node.size.value<=0):raise DirectX86Error('global array size must be a positive integer literal')
   size=8*(node.size.value if node.size else 1);label=f'bh_global_{i}';self.globals[node.name]=f'[rip+{label}]';self.scopes[0][node.name]=self.globals[node.name]
   if node.size:self.global_array_sizes[self.globals[node.name]]=node.size.value;self.array_sizes[self.globals[node.name]]=node.size.value
   self.global_data.append((label,size))
  for s in p.statements:
   if not isinstance(s,Function):self.stmt(s)
  self.lines[9]=f'  sub rsp, {max(16, (self.next+15)//16*16)}'
  self.lines+=['  xor eax, eax','  leave','  ret']
  for f in p.statements:
   if isinstance(f,Function):
    self.return_type=f.return_type
    self.slots={};self.arrays={};self.array_sizes=self.global_array_sizes.copy();self.next=0;self.scopes=[self.globals,{}];self.lines+= [f'{self.function_labels[f.name]}:','  push rbp','  mov rbp, rsp','  sub rsp, 128'];frame_line=len(self.lines)-1
    ii=fi=stack_index=0
    for name,typ in f.params:
     address=self.slot(name,declare=True)
     if typ in ('doshomik','দশমিক'):
      if fi<8:self.lines.append(f'  movq QWORD PTR {address}, xmm{fi}')
      else:self.lines.extend([f'  mov rax, QWORD PTR [rbp+{16+stack_index*8}]',f'  mov QWORD PTR {address}, rax']);stack_index+=1
      fi+=1
     else:
      if ii<6:self.lines.append(f'  mov QWORD PTR {address}, '+['rdi','rsi','rdx','rcx','r8','r9'][ii])
      else:self.lines.extend([f'  mov rax, QWORD PTR [rbp+{16+stack_index*8}]',f'  mov QWORD PTR {address}, rax']);stack_index+=1
      ii+=1
    self.stmt(f.body)
    self.lines[frame_line]=f'  sub rsp, {max(16, (self.next+15)//16*16)}'
  self.lines+=['.Lbounds_error:','  lea rsi, [rip+bounds_message]','  mov edx, bounds_message_end - bounds_message','  jmp .Lruntime_error','.Linput_error:','  lea rsi, [rip+input_message]','  mov edx, input_message_end - input_message','  jmp .Lruntime_error','.Ldivision_error:','  lea rsi, [rip+division_message]','  mov edx, division_message_end - division_message','.Lruntime_error:','  mov eax, 1','  mov edi, 2','  syscall','  mov edi, 2','  and rsp, -16','  call exit','.section .rodata','bounds_message: .ascii "runtime error: array index out of bounds\\n"','bounds_message_end:','input_message: .ascii "runtime error: invalid or missing input\\n"','input_message_end:','division_message: .ascii "runtime error: division by zero\\n"','division_message_end:','fmt_string: .string "%s\\n"','fmt_float: .string "%g\\n"','fmt_read: .string "%ld"','fmt_read_float: .string "%lf"','bool_true: .string "true"','bool_false: .string "false"','.section .note.GNU-stack,"",@progbits']
  if self.strings:
   self.lines.append('.section .rodata')
   for label,value in self.strings:self.lines.extend([label+':','  .byte '+', '.join(str(b) for b in value.encode('utf-8')+b'\0')])
  if self.global_data:
   self.lines.append('.section .bss')
   for label,size in self.global_data:self.lines.extend([label+':',f'  .zero {size}'])
  return '\n'.join(self.lines)+'\n'
def emit_direct(program,outfile):
 out=Path(outfile);asm=out.with_suffix('.s');asm.write_text(Emitter().generate(program),encoding='utf8')
 with tempfile.TemporaryDirectory(prefix='bhasha-runtime-') as directory:
  runtime=Path(directory)/'input.c';runtime.write_text(INPUT_RUNTIME,encoding='utf8')
  subprocess.run(['gcc','-no-pie',str(asm),str(runtime),'-o',str(out)],check=True)
 return asm
