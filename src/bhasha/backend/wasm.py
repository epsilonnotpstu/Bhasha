"""Minimal WebAssembly text backend for constant arithmetic programs.

The emitted module exports `run`, returning the last printed integer. It is a
small optional teaching target; unsupported AST constructs are reported rather
than silently miscompiled.
"""
from ..ast_nodes import *
class WasmError(ValueError): pass
def _expr(n):
 if isinstance(n,Literal) and isinstance(n.value,int):return f"i32.const {n.value}"
 if isinstance(n,Binary) and n.op in ("+","-","*","/","%"):
  op={"+":"add","-":"sub","*":"mul","/":"div_s","%":"rem_s"}[n.op]
  return f"{_expr(n.left)}\n    {_expr(n.right)}\n    i32.{op}"
 raise WasmError("WAT backend currently supports integer literal arithmetic only")
def emit_wat(program):
 prints=[s for s in program.statements if isinstance(s,Print)]
 if len(prints)!=1 or any(not isinstance(s,Print) for s in program.statements):
  raise WasmError("WAT backend currently accepts a single dekhao expression")
 return "(module\n  (func (export \"run\") (result i32)\n    "+_expr(prints[0].value)+"\n  )\n)\n"
