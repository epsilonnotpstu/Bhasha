"""Hand-written Linux x86-64 backend for Bhasha's integer straight-line subset.

It deliberately has a narrow, explicit contract. Unsupported AST nodes raise
`DirectX86Error`, allowing the proven GCC backend to remain the fallback.
"""
from pathlib import Path
import subprocess
from ..ast_nodes import *
class DirectX86Error(ValueError): pass
class Emitter:
 def __init__(self):self.lines=['.intel_syntax noprefix','.global main','.extern printf','.section .rodata','fmt: .string "%ld\\n"','.text','main:','  push rbp','  mov rbp, rsp','  sub rsp, 128'];self.slots={};self.next=0;self.labels=0
 def label(self):self.labels+=1;return f'.L{self.labels}'
 def slot(self,name):
  if name not in self.slots:self.next+=8;self.slots[name]=self.next
  return f'[rbp-{self.slots[name]}]'
 def expr(self,n):
  if isinstance(n,Literal) and isinstance(n.value,int):self.lines.append(f'  mov rax, {n.value}')
  elif isinstance(n,Name):self.lines.append(f'  mov rax, QWORD PTR {self.slot(n.name)}')
  elif isinstance(n,Binary) and n.op in ('+','-','*','/','%','==','!=','<','>','<=','>='):
   self.expr(n.left);self.lines.append('  push rax');self.expr(n.right);self.lines.append('  pop rcx')
   if n.op=='+':self.lines.append('  add rax, rcx')
   elif n.op=='-':self.lines.append('  sub rcx, rax');self.lines.append('  mov rax, rcx')
   elif n.op=='*':self.lines.append('  imul rax, rcx')
   elif n.op in ('/','%'):
    self.lines.append('  mov r8, rax');self.lines.append('  mov rax, rcx');self.lines.append('  cqo');self.lines.append('  idiv r8')
    if n.op=='%':self.lines.append('  mov rax, rdx')
   else:
    self.lines.append('  cmp rcx, rax');self.lines.append('  mov eax, 0')
    self.lines.append({'==':'  sete al','!=':'  setne al','<':'  setl al','>':'  setg al','<=':'  setle al','>=':'  setge al'}[n.op])
  elif isinstance(n,Call) and not n.args:self.lines.append(f'  call fn_{n.callee}')
  else:raise DirectX86Error(f'direct x86 unsupported expression: {type(n).__name__}')
 def stmt(self,n):
  if isinstance(n,VarDecl) and not n.size and n.type_name in ('purno','পূর্ণ'):
   self.expr(n.value or Literal(value=0));self.lines.append(f'  mov QWORD PTR {self.slot(n.name)}, rax')
  elif isinstance(n,Assign) and isinstance(n.target,Name) and n.op=='=':
   self.expr(n.value);self.lines.append(f'  mov QWORD PTR {self.slot(n.target.name)}, rax')
  elif isinstance(n,Print):
   self.expr(n.value);self.lines+=['  mov rsi, rax','  lea rdi, [rip+fmt]','  xor eax, eax','  call printf']
  elif isinstance(n,If):
   alt,end=self.label(),self.label();self.expr(n.condition);self.lines+=['  test rax, rax',f'  jz {alt}'];self.stmt(n.then_branch);self.lines+= [f'  jmp {end}',f'{alt}:']
   if n.else_branch:self.stmt(n.else_branch)
   self.lines.append(f'{end}:')
  elif isinstance(n,Block):
   for s in n.statements:self.stmt(s)
  elif isinstance(n,While):
   start,end=self.label(),self.label();self.lines.append(f'{start}:');self.expr(n.condition);self.lines+=['  test rax, rax',f'  jz {end}'];self.stmt(n.body);self.lines+= [f'  jmp {start}',f'{end}:']
  elif isinstance(n,For):
   self.expr(n.start);self.lines.append(f'  mov QWORD PTR {self.slot(n.name)}, rax');start,end=self.label(),self.label();self.lines.append(f'{start}:');self.expr(Name(name=n.name));self.lines.append('  push rax');self.expr(n.end);self.lines+=['  pop rcx','  cmp rcx, rax',f'  jge {end}'];self.stmt(n.body);self.lines+= [f'  add QWORD PTR {self.slot(n.name)}, 1',f'  jmp {start}',f'{end}:']
  elif isinstance(n,Return):self.expr(n.value);self.lines+=['  leave','  ret']
  else:raise DirectX86Error(f'direct x86 unsupported statement: {type(n).__name__}')
 def generate(self,p):
  for s in p.statements:
   if not isinstance(s,Function):self.stmt(s)
  self.lines+=['  xor eax, eax','  leave','  ret']
  for f in p.statements:
   if isinstance(f,Function):
    if f.params:raise DirectX86Error('direct x86 function parameters are not implemented')
    self.slots={};self.next=0;self.lines+= [f'fn_{f.name}:','  push rbp','  mov rbp, rsp','  sub rsp, 128'];self.stmt(f.body)
  return '\n'.join(self.lines)+'\n'
def emit_direct(program,outfile):
 out=Path(outfile);asm=out.with_suffix('.s');asm.write_text(Emitter().generate(program),encoding='utf8');subprocess.run(['gcc','-no-pie',str(asm),'-o',str(out)],check=True);return asm
