from bhasha.lexer import lex
from bhasha.parser import parse
from bhasha.semantic import analyze
from bhasha.backend.vm import run
def build(s):
 t,d=lex(s); assert not d
 p,d=parse(t); assert not d
 d,_=analyze(p); assert not d
 return p
def test_unicode_and_comments():
 t,d=lex('// x\nধরো পূর্ণ x = 1;'); assert not d; assert t[0].type=='DECLARE'
def test_arithmetic_vm(): assert run(build('dhoro purno x = 2; dekhao x + 3;'))=='5\n'
def test_recursion(): assert run(build('kaj f(purno n): purno { jodi n <= 1 { ferot 1; } ferot n*f(n-1); } dekhao f(5);'))=='120\n'

def test_nested_scope_shadowing_and_outer_assignment():
 source='dhoro purno x = 1; { dhoro purno x = 2; x = 3; dekhao x; } { x = 4; } dekhao x;'
 assert run(build(source))=='3\n4\n'

def test_function_can_access_and_update_global():
 source='dhoro purno x = 1; kaj f(): purno { x = x + 1; ferot x; } dekhao f(); dekhao x;'
 assert run(build(source))=='2\n2\n'

def test_print_evaluates_expression_once():
 from bhasha.backend.vm import VM
 from bhasha.ast_nodes import Print, Literal
 vm=VM(); calls=[]
 vm.eval=lambda node, env: calls.append(node) or 42
 vm.exec(Print(value=Literal(value=1)), {})
 assert len(calls)==1 and vm.output==['42']
