"""Run both TAC variants rather than comparing inspection text alone."""
import random
import pytest
from bhasha.cli import compile_text
from bhasha.backend.vm import run
from bhasha.backend.tac_vm import execute
from bhasha.optimizer import optimize

def test_fixed_seed_arithmetic_equivalence():
 randomizer=random.Random(1861)
 for _ in range(300):
  a=randomizer.randint(-100,100);b=randomizer.randint(1,30);c=randomizer.randint(0,20)
  source=f'dekhao ({a} + {b}) * {c};'
  _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
  optimized,_=optimize(ir)
  assert execute(ir)==execute(optimized)==run(tree)

def test_control_flow_equivalence():
 source='dhoro purno sum = 0; cholo i = 0 theke 5 { sum += i; } dekhao sum;'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='10\n'

def test_array_program_equivalence():
 from pathlib import Path
 source=(Path(__file__).parents[1]/'examples'/'array_sum_max.bh').read_text()
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='30\n12\n'

def test_float_array_widening_across_vm_tac_native(tmp_path):
 import subprocess
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.direct_x86 import emit_direct
 source='dhoro doshomik[2] a; a[0] = 5; a[1] = 2; dekhao a[0] / a[1];'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='2.5\n'
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='2.5\n'

def test_boolean_array_zero_initialization():
 _,tree,diagnostics,ir=compile_text('dhoro huen[2] a; dekhao a[0];');assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='false\n'

def test_tac_input_equivalence():
 from bhasha.backend.vm import VM
 _,tree,diagnostics,ir=compile_text('dhoro purno x; poro x; dekhao x + 1;');assert not diagnostics
 vm=VM(input_fn=lambda:'41');vm.exec(tree,vm.global_env)
 assert execute(ir,input_fn=lambda:'41')==execute(optimize(ir)[0],input_fn=lambda:'41')=='42\n'
 assert vm.output==['42']

@pytest.mark.parametrize('source',[
 'dhoro doshomik x = 5; dekhao x / 2;',
 'dhoro doshomik x = 2.5; x = 5; dekhao x / 2;',
 'kaj half(doshomik x): doshomik { ferot x / 2; } dekhao half(5);',
 'kaj f(): doshomik { ferot 5; } dekhao f() / 2;',
])
def test_float_widening_tac_matches_vm(source):
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='2.5\n'

def test_recursive_and_nested_calls_match_ast_vm():
 from pathlib import Path
 for name in ('factorial','fibonacci_recursive','function_heavy'):
  source=(Path(__file__).parents[1]/'examples'/f'{name}.bh').read_text()
  _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
  assert execute(ir)==execute(optimize(ir)[0])==run(tree)

def test_all_shipped_valid_examples_tac():
 from pathlib import Path
 root=Path(__file__).parents[1]/'examples'
 for expected in sorted(root.glob('*.expected')):
  if expected.stem.startswith('error_'):continue
  _,tree,diagnostics,ir=compile_text(expected.with_suffix('.bh').read_text());assert not diagnostics
  assert execute(ir)==execute(optimize(ir)[0])==run(tree)==expected.read_text()

@pytest.mark.parametrize('level',['-O0','-O1','-O2'])
def test_cli_tac_optimization_levels(level,tmp_path,capsys):
 from bhasha.cli import main
 source=tmp_path/'program.bh';source.write_text('dekhao (2 + 3) * 4;')
 assert main([str(source),'--run-tac',level])==0
 assert capsys.readouterr().out=='20\n'

def test_cli_tac_invalid_numeric_input(tmp_path,capsys,monkeypatch):
 from bhasha.cli import main
 source=tmp_path/'input.bh';source.write_text('dhoro purno x; poro x; dekhao x;')
 monkeypatch.setattr('builtins.input',lambda:'2abc')
 assert main([str(source),'--run-tac','-O2'])==2
 assert 'TAC runtime error:' in capsys.readouterr().err

def test_user_name_does_not_collide_with_temporaries():
 source='dhoro purno t1 = 2; t1 += 3; dekhao t1 * 2;'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='10\n'

def test_global_update_and_block_shadowing():
 source='dhoro purno x = 1; kaj f(): purno { x = x + 1; ferot x; } { dhoro purno x = 8; dekhao x; } dekhao f(); dekhao x;'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='8\n2\n2\n'

def test_parameter_shadowing_global():
 source='dhoro purno x = 9; kaj f(purno x): purno { ferot x + 1; } dekhao f(2); dekhao x;'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='3\n9\n'

def test_global_named_like_temp_is_preserved():
 source='dhoro purno t1 = 5; kaj f(): purno { ferot t1; } dekhao f();'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)=='5\n'

def test_loop_shadowing_matches_all_execution_backends(tmp_path):
 import subprocess
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.direct_x86 import emit_direct
 source='dhoro purno i = 2; cholo i = i theke 4 { dekhao i; } dekhao i;'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 expected='2\n3\n2\n'
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])==expected
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==expected

@pytest.mark.parametrize('expression,expected', [('x + bump()', '3\n'),('sum(x, bump())', '3\n')])
def test_operand_value_captured_before_later_call(expression,expected):
 source='dhoro purno x = 1; kaj bump(): purno { x = x + 1; ferot x; } kaj sum(purno a, purno b): purno { ferot a + b; } dekhao '+expression+';'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert execute(ir)==execute(optimize(ir)[0])==run(tree)==expected

@pytest.mark.parametrize('statement,expected',[
 ('dekhao x + bump();','3\n'),
 ('dekhao sum(x, bump());','3\n'),
 ('a[bump()] = x; dekhao a[2];','1\n'),
])
def test_side_effect_order_across_backends(tmp_path,statement,expected):
 import subprocess
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.direct_x86 import emit_direct
 source='dhoro purno x = 1; dhoro purno[3] a; kaj bump(): purno { x = x + 1; ferot x; } kaj sum(purno p, purno q): purno { ferot p + q; } '+statement
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])==expected
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==expected

@pytest.mark.parametrize('statement',['dekhao a[-1];','a[-1] = 7;','dekhao a[2];','a[2] = 7;'])
def test_array_bounds_match_vm_and_tac(statement):
 _,tree,diagnostics,ir=compile_text('dhoro purno[2] a; '+statement);assert not diagnostics
 for action in (lambda:run(tree),lambda:execute(ir),lambda:execute(optimize(ir)[0])):
  with pytest.raises(IndexError,match='out of bounds'):action()
def test_common_expression_with_function_mutation_matches_reference():
 from bhasha.cli import compile_text
 from bhasha.backend.vm import run
 from bhasha.backend.tac_vm import execute
 from bhasha.optimizer import optimize
 source='''dhoro purno x = 2; dhoro purno y = 3;
 kaj change(): purno { x = 7; ferot 0; }
 dekhao x + y; dekhao x + y; dekhao change(); dekhao x + y;'''
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 optimized,stats=optimize(ir)
 assert stats['common_subexpressions'] >= 1
 assert run(tree)==execute(ir)==execute(optimized)=='5\n5\n0\n10\n'
