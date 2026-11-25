"""Readable pseudo three-address-code listing for pipeline inspection."""
from .ast_nodes import *
class IRGen:
 def __init__(self): self.lines=[]; self.n=0; self.labels=0; self.breaks=[]; self.continues=[]
 def temp(self): self.n+=1; return f"t{self.n}"
 def label(self,prefix="L"): self.labels+=1; return f"{prefix}{self.labels}"
 def expr(self,n):
  if isinstance(n,Literal): return repr(n.value)
  if isinstance(n,Name): return n.name
  if isinstance(n,Binary):
   a,b=self.expr(n.left),self.expr(n.right); t=self.temp(); self.lines.append(f"{t} = {a} {n.op} {b}"); return t
  if isinstance(n,Unary): t=self.temp(); self.lines.append(f"{t} = {n.op} {self.expr(n.operand)}"); return t
  if isinstance(n,Call):
   a=[self.expr(x) for x in n.args]; self.lines.extend(f"param {x}" for x in a); t=self.temp(); self.lines.append(f"{t} = call {n.callee}, {len(a)}"); return t
  if isinstance(n,Index): return f"{self.expr(n.array)}[{self.expr(n.index)}]"
  return "?"
 def visit(self,n):
  if isinstance(n,Program): [self.visit(x) for x in n.statements]
  elif isinstance(n,Block): [self.visit(x) for x in n.statements]
  elif isinstance(n,VarDecl): self.lines.append(f"{n.name} = {self.expr(n.value)}" if n.value else f"decl {n.type_name} {n.name}")
  elif isinstance(n,Assign): self.lines.append(f"{self.expr(n.target)} {n.op} {self.expr(n.value)}")
  elif isinstance(n,Print): self.lines.append(f"print {self.expr(n.value)}")
  elif isinstance(n,Return): self.lines.append(f"return {self.expr(n.value)}")
  elif isinstance(n,Function): self.lines.append(f"func {n.name}:"); self.visit(n.body); self.lines.append("endfunc")
  elif isinstance(n,If):
   alt,end=self.label("else"),self.label("endif"); self.lines.append(f"ifFalse {self.expr(n.condition)} goto {alt}"); self.visit(n.then_branch); self.lines.append(f"goto {end}"); self.lines.append(f"{alt}:"); self.visit(n.else_branch); self.lines.append(f"{end}:")
  elif isinstance(n,While):
   start,end=self.label("while"),self.label("endwhile");self.lines.append(f"{start}:");self.lines.append(f"ifFalse {self.expr(n.condition)} goto {end}");self.breaks.append(end);self.continues.append(start);self.visit(n.body);self.continues.pop();self.breaks.pop();self.lines.append(f"goto {start}");self.lines.append(f"{end}:")
  elif isinstance(n,For):
   start,end=self.label("for"),self.label("endfor");self.lines.append(f"{n.name} = {self.expr(n.start)}");self.lines.append(f"{start}:");self.lines.append(f"ifFalse {n.name} < {self.expr(n.end)} goto {end}");self.breaks.append(end);self.continues.append(start);self.visit(n.body);self.continues.pop();self.breaks.pop();self.lines.append(f"{n.name} += 1");self.lines.append(f"goto {start}");self.lines.append(f"{end}:")
  elif isinstance(n,Break): self.lines.append(f"goto {self.breaks[-1]}")
  elif isinstance(n,Continue): self.lines.append(f"goto {self.continues[-1]}")
 def generate(self,p): self.visit(p); return self.lines
def generate(program): return IRGen().generate(program)
