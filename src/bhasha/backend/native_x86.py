"""Practical native backend: lower supported Bhasha AST constructs to C, then GCC ELF."""
from pathlib import Path
import json
import subprocess
from ..ast_nodes import *
from .input_runtime import INPUT_RUNTIME

class CEmitter:
 def __init__(self): self.lines=["#include <stdio.h>","#include <stdbool.h>","#include <stdlib.h>",INPUT_RUNTIME,'static long bh_checked_index(long i, long n) { if (i < 0 || i >= n) { fputs("runtime error: array index out of bounds\\n", stderr); exit(2); } return i; }'];self.indent=0;self.types={};self.loop_id=0;self.expr_id=0
 def emit(self,s):self.lines.append("  "*self.indent+s)
 def temporary(self):self.expr_id+=1;return f'__bh_expr_{self.expr_id}'
 def typ(self,t):return {"purno":"long","পূর্ণ":"long","doshomik":"double","দশমিক":"double","huen":"bool"}.get(t,"long")
 def expr(self,n):
  if isinstance(n,Literal):return 'true' if n.value is True else 'false' if n.value is False else json.dumps(n.value) if isinstance(n.value,str) else repr(n.value)
  if isinstance(n,Name):return n.name
  if isinstance(n,Index):
   if not isinstance(n.array,Name):raise ValueError('array index target must be a named array')
   name=self.expr(n.array);return f'{name}[bh_checked_index({self.expr(n.index)}, sizeof({name}) / sizeof({name}[0]))]'
  if isinstance(n,Unary):return f"({'!' if n.op in ('NOT','!') else n.op}{self.expr(n.operand)})"
  if isinstance(n,Binary):
   if n.op in ('AND','OR'):return f"({self.expr(n.left)} {'&&' if n.op=='AND' else '||'} {self.expr(n.right)})"
   left,right=self.temporary(),self.temporary()
   guard=f'if ({right} == 0) {{ fputs("runtime error: division by zero\\n", stderr); exit(2); }} ' if n.op in ('/','%') else ''
   return f'({{ __auto_type {left} = {self.expr(n.left)}; __auto_type {right} = {self.expr(n.right)}; {guard}{left} {n.op} {right}; }})'
  if isinstance(n,Call):
   names=[self.temporary() for _ in n.args]
   declarations=' '.join(f'__auto_type {name} = {self.expr(arg)};' for name,arg in zip(names,n.args))
   return f'({{ {declarations} {n.callee}({", ".join(names)}); }})'
  raise ValueError("unsupported expression")
 def stmt(self,n):
  if isinstance(n,Block):self.emit("{");self.indent+=1;[self.stmt(x) for x in n.statements];self.indent-=1;self.emit("}")
  elif isinstance(n,VarDecl):
   self.types[n.name]=n.type_name
   if n.size:self.emit(f"{self.typ(n.type_name)} {n.name}[{self.expr(n.size)}] = {{0}};")
   else:self.emit(f"{self.typ(n.type_name)} {n.name}"+(f" = {self.expr(n.value)}" if n.value else " = 0")+";")
  elif isinstance(n,Assign):
   if isinstance(n.target,Index) or n.op=='/=':
    value=self.temporary();guard=f'if ({value} == 0) {{ fputs("runtime error: division by zero\\n", stderr); exit(2); }} ' if n.op=='/=' else ''
    self.emit(f'{{ __auto_type {value} = {self.expr(n.value)}; {guard}{self.expr(n.target)} {n.op} {value}; }}')
   else:self.emit(f"{self.expr(n.target)} {n.op} {self.expr(n.value)};")
  elif isinstance(n,Read):
   reader='bh_read_float' if n.target.inferred_type=='float' else 'bh_read_int'
   self.emit(f'if (!{reader}(&{n.target.name})) {{ fputs("runtime error: invalid or missing input\\n", stderr); exit(2); }}')
  elif isinstance(n,Print):
   x=self.expr(n.value); ty=getattr(n.value,"inferred_type",None)
   self.emit(f'printf("%s\\n", {x});' if ty=="string" else f'printf("%s\\n", ({x}) ? "true" : "false");' if ty=="bool" else f'printf("%g\\n", (double)({x}));' if ty=="float" else f'printf("%ld\\n", (long)({x}));')
  elif isinstance(n,Return):self.emit(f"return {self.expr(n.value)};")
  elif isinstance(n,If):self.emit(f"if ({self.expr(n.condition)})");self.stmt(n.then_branch); self.emit("else");self.stmt(n.else_branch) if n.else_branch else self.emit(";")
  elif isinstance(n,While):self.emit(f"while ({self.expr(n.condition)})");self.stmt(n.body)
  elif isinstance(n,For):
   self.loop_id+=1;limit=f'__bhasha_limit_{self.loop_id}';start=f'__bhasha_start_{self.loop_id}'
   self.emit('{');self.indent+=1
   self.emit(f'long {start} = {self.expr(n.start)};');self.emit(f'long {n.name} = {start};')
   self.emit(f'long {limit} = {self.expr(n.end)};')
   self.emit(f'for (; {n.name} < {limit}; ++{n.name})');self.stmt(n.body)
   self.indent-=1;self.emit('}')
  elif isinstance(n,Break):self.emit("break;")
  elif isinstance(n,Continue):self.emit("continue;")
 def generate(self,p):
  funcs=[x for x in p.statements if isinstance(x,Function)]
  globals_=[x for x in p.statements if isinstance(x,VarDecl)]
  for v in globals_:
   if v.size:
    if not isinstance(v.size,Literal) or type(v.size.value) is not int:raise ValueError('global array size must be a fixed integer')
    self.emit(f'{self.typ(v.type_name)} {v.name}[{v.size.value}];')
   else:self.emit(f'{self.typ(v.type_name)} {v.name};')
  for f in funcs:self.emit(f"{self.typ(f.return_type)} {f.name}({', '.join(self.typ(t)+' '+n for n,t in f.params)});")
  for f in funcs:
   self.emit(f"{self.typ(f.return_type)} {f.name}({', '.join(self.typ(t)+' '+n for n,t in f.params)})");self.stmt(f.body)
  self.emit("int main(void) {");self.indent+=1
  for n in p.statements:
   if isinstance(n,VarDecl):
    if n.value:self.emit(f'{n.name} = {self.expr(n.value)};')
   elif not isinstance(n,Function):self.stmt(n)
  self.emit("return 0;");self.indent-=1;self.emit("}");return "\n".join(self.lines)+"\n"
def emit_native(program,outfile,opt_level=2):
 out=Path(outfile); c=out.with_suffix(".c");c.write_text(CEmitter().generate(program),encoding="utf8")
 if opt_level not in (0,1,2):raise ValueError('unsupported optimization level')
 subprocess.run(["gcc",f"-O{opt_level}","-std=c11",str(c),"-o",str(out)],check=True)
 return c
def emit_assembly(program, outfile,opt_level=2):
 """Emit GCC's System-V x86-64 assembly for the same generated C source."""
 out=Path(outfile); c=out.with_suffix(".c"); c.write_text(CEmitter().generate(program),encoding="utf8")
 if opt_level not in (0,1,2):raise ValueError('unsupported optimization level')
 subprocess.run(["gcc",f"-O{opt_level}","-S","-masm=intel",str(c),"-o",str(out)],check=True)
 return out
