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
