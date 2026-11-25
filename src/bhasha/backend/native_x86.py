"""Practical native backend: lower supported Bhasha AST constructs to C, then GCC ELF."""
from pathlib import Path
import subprocess
from ..ast_nodes import *

class CEmitter:
 def __init__(self): self.lines=["#include <stdio.h>","#include <stdbool.h>"];self.indent=0;self.types={}
 def emit(self,s):self.lines.append("  "*self.indent+s)
 def typ(self,t):return {"purno":"long","পূর্ণ":"long","doshomik":"double","দশমিক":"double","huen":"bool"}.get(t,"long")
 def expr(self,n):
  if isinstance(n,Literal):return 'true' if n.value is True else 'false' if n.value is False else repr(n.value)
  if isinstance(n,Name):return n.name
  if isinstance(n,Index):return f"{self.expr(n.array)}[{self.expr(n.index)}]"
  if isinstance(n,Unary):return f"({'!' if n.op in ('NOT','!') else n.op}{self.expr(n.operand)})"
  if isinstance(n,Binary):return f"({self.expr(n.left)} {'&&' if n.op=='AND' else '||' if n.op=='OR' else n.op} {self.expr(n.right)})"
  if isinstance(n,Call):return f"{n.callee}({', '.join(self.expr(a) for a in n.args)})"
  raise ValueError("unsupported expression")
 def stmt(self,n):
  if isinstance(n,Block):self.emit("{");self.indent+=1;[self.stmt(x) for x in n.statements];self.indent-=1;self.emit("}")
  elif isinstance(n,VarDecl):
   self.types[n.name]=n.type_name
   if n.size:self.emit(f"{self.typ(n.type_name)} {n.name}[{self.expr(n.size)}] = {{0}};")
   else:self.emit(f"{self.typ(n.type_name)} {n.name}"+(f" = {self.expr(n.value)}" if n.value else " = 0")+";")
  elif isinstance(n,Assign):self.emit(f"{self.expr(n.target)} {n.op} {self.expr(n.value)};")
  elif isinstance(n,Print):
   x=self.expr(n.value); ty=getattr(n.value,"inferred_type",None)
   self.emit(f'printf("%s\\n", {x});' if ty=="string" else f'printf("%s\\n", ({x}) ? "true" : "false");' if ty=="bool" else f'printf("%g\\n", (double)({x}));' if ty=="float" else f'printf("%ld\\n", (long)({x}));')
  elif isinstance(n,Return):self.emit(f"return {self.expr(n.value)};")
  elif isinstance(n,If):self.emit(f"if ({self.expr(n.condition)})");self.stmt(n.then_branch); self.emit("else");self.stmt(n.else_branch) if n.else_branch else self.emit(";")
  elif isinstance(n,While):self.emit(f"while ({self.expr(n.condition)})");self.stmt(n.body)
  elif isinstance(n,For):self.emit(f"for (long {n.name} = {self.expr(n.start)}; {n.name} < {self.expr(n.end)}; ++{n.name})");self.stmt(n.body)
  elif isinstance(n,Break):self.emit("break;")
  elif isinstance(n,Continue):self.emit("continue;")
 def generate(self,p):
  funcs=[x for x in p.statements if isinstance(x,Function)]
  for f in funcs:self.emit(f"{self.typ(f.return_type)} {f.name}({', '.join(self.typ(t)+' '+n for n,t in f.params)});")
  for f in funcs:
   self.emit(f"{self.typ(f.return_type)} {f.name}({', '.join(self.typ(t)+' '+n for n,t in f.params)})");self.stmt(f.body)
  self.emit("int main(void) {");self.indent+=1
  for n in p.statements:
   if not isinstance(n,Function):self.stmt(n)
  self.emit("return 0;");self.indent-=1;self.emit("}");return "\n".join(self.lines)+"\n"
def emit_native(program,outfile):
 out=Path(outfile); c=out.with_suffix(".c");c.write_text(CEmitter().generate(program),encoding="utf8")
 subprocess.run(["gcc","-O2","-std=c11",str(c),"-o",str(out)],check=True)
 return c
def emit_assembly(program, outfile):
 """Emit GCC's System-V x86-64 assembly for the same generated C source."""
 out=Path(outfile); c=out.with_suffix(".c"); c.write_text(CEmitter().generate(program),encoding="utf8")
 subprocess.run(["gcc","-O2","-S","-masm=intel",str(c),"-o",str(out)],check=True)
 return out
