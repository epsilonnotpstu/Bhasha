"""Check fixed-point propagation across nullable grammar symbols."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('first_follow',Path(__file__).parents[1]/'tools'/'first_follow.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_nullable_first_and_follow():
 grammar={'S':[('A','B')], 'A':[('a',),()], 'B':[('b',),()]}
 first,follow=module.compute(grammar,'S')
 assert first['S']=={'a','b',module.EPSILON}
 assert follow['A']=={'b','EOF'} and follow['B']=={'EOF'}

def test_grammar_results_change_when_rules_change():
 first,follow=module.compute({'S':[('item',)],'item':[('z',)]},'S')
 assert first['S']=={'z'} and follow['item']=={'EOF'}

def test_documented_table_matches_generated_output():
 text=(Path(__file__).parents[1]/'docs'/'first_follow.md').read_text(encoding='utf8')
 assert module.table() in text

def test_expression_precedence_first_follow():
 first,follow=module.compute(module.GRAMMAR,'program')
 assert {'NUMBER','FLOAT_LIT','IDENT','(','NOT','-'} <= first['expression']
 assert {';',')',']',',','TO'} <= follow['expression']
 assert {'*','/','%'} <= first['multiplicative_tail']
