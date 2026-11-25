"""Hand-written Linux x86-64 backend for Bhasha's integer straight-line subset.

It deliberately has a narrow, explicit contract. Unsupported AST nodes raise
`DirectX86Error`, allowing the proven GCC backend to remain the fallback.
"""
from pathlib import Path
import subprocess
from ..ast_nodes import *
class DirectX86Error(ValueError): pass
class Emitter:
 def __init__(self):self.lines=['.intel_syntax noprefix','.global main','.extern printf','.section .rodata','fmt: .string "%ld\\n"','.text','main:','  push rbp','  mov rbp, rsp','  sub rsp, 128'];self.slots={};self.next=0
 def slot(self,name):
  if name not in self.slots:self.next+=8;self.slots[name]=self.next
  return f'[rbp-{self.slots[name]}]'
 def expr(self,n):
  if isinstance(n,Literal) and isinstance(n.value,int):self.lines.append(f'  mov rax, {n.value}')
  elif isinstance(n,Name):self.lines.append(f'  mov rax, QWORD PTR {self.slot(n.name)}')
  elif isinstance(n,Binary) and n.op in ('+','-','*'):
   self.expr(n.left);self.lines.append('  push rax');self.expr(n.right);self.lines.append('  pop rcx')
   if n.op=='+':self.lines.append('  add rax, rcx')
   elif n.op=='-':self.lines.append('  sub rcx, rax');self.lines.append('  mov rax, rcx')
   else:self.lines.append('  imul rax, rcx')
  else:raise DirectX86Error(f'direct x86 unsupported expression: {type(n).__name__}')
 def stmt(self,n):
  if isinstance(n,VarDecl) and not n.size and n.type_name in ('purno','পূর্ণ'):
   self.expr(n.value or Literal(value=0));self.lines.append(f'  mov QWORD PTR {self.slot(n.name)}, rax')
  elif isinstance(n,Assign) and isinstance(n.target,Name) and n.op=='=':
   self.expr(n.value);self.lines.append(f'  mov QWORD PTR {self.slot(n.target.name)}, rax')
  elif isinstance(n,Print):
   self.expr(n.value);self.lines+=['  mov rsi, rax','  lea rdi, [rip+fmt]','  xor eax, eax','  call printf']
  else:raise DirectX86Error(f'direct x86 unsupported statement: {type(n).__name__}')
 def generate(self,p):
  for s in p.statements:self.stmt(s)
  self.lines+=['  xor eax, eax','  leave','  ret'];return '\n'.join(self.lines)+'\n'
def emit_direct(program,outfile):
 out=Path(outfile);asm=out.with_suffix('.s');asm.write_text(Emitter().generate(program),encoding='utf8');subprocess.run(['gcc','-no-pie',str(asm),'-o',str(out)],check=True);return asm
