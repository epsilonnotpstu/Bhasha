"""Dataclass AST. Nodes retain a source token for clear diagnostics."""
from dataclasses import dataclass, field, asdict
from typing import Any
@dataclass
class Node: line:int=0; column:int=0; inferred_type:str|None=None
@dataclass
class Program(Node): statements:list[Any]=field(default_factory=list)
@dataclass
class Block(Node): statements:list[Any]=field(default_factory=list)
@dataclass
class VarDecl(Node): name:str=""; type_name:str=""; size:Any=None; value:Any=None
@dataclass
class Assign(Node): target:Any=None; op:str="="; value:Any=None
@dataclass
class If(Node): condition:Any=None; then_branch:Any=None; else_branch:Any=None
@dataclass
class While(Node): condition:Any=None; body:Any=None
@dataclass
class For(Node): name:str=""; start:Any=None; end:Any=None; body:Any=None
@dataclass
class Function(Node): name:str=""; params:list[Any]=field(default_factory=list); return_type:str=""; body:Any=None
@dataclass
class Return(Node): value:Any=None
@dataclass
class Print(Node): value:Any=None
@dataclass
class Read(Node): target:Any=None
@dataclass
class Break(Node): pass
@dataclass
class Continue(Node): pass
@dataclass
class Binary(Node): left:Any=None; op:str=""; right:Any=None
@dataclass
class Unary(Node): op:str=""; operand:Any=None
@dataclass
class Literal(Node): value:Any=None
@dataclass
class Name(Node): name:str=""
@dataclass
class Index(Node): array:Any=None; index:Any=None
@dataclass
class Call(Node): callee:str=""; args:list[Any]=field(default_factory=list)
def ast_json(n): return asdict(n)
