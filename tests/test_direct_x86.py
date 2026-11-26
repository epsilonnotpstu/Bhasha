import subprocess
import pytest
from bhasha.cli import compile_text
from bhasha.backend.direct_x86 import emit_direct

@pytest.mark.parametrize('statement',['dekhao a[-1];','a[-1] = 7;','dekhao a[2];','a[2] = 7;'])
def test_native_array_bounds_fail_safely(tmp_path,statement):
 from bhasha.backend.native_x86 import emit_native
 _,tree,ds,_=compile_text('dhoro purno[2] a; '+statement);assert not ds
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=3)
  assert result.returncode==2
  assert 'array index out of bounds' in result.stderr

@pytest.mark.parametrize('source',[
 'dekhao 1 / 0;', 'dekhao 1 % 0;', 'dekhao 1.5 / 0.0;',
 'dhoro purno x = 5; x /= 0; dekhao x;',
 'dhoro doshomik x = 5.0; x /= 0.0; dekhao x;',
])
def test_division_by_zero_is_runtime_error_across_backends(tmp_path,source):
 from bhasha.backend.vm import run
 from bhasha.backend.tac_vm import execute
 from bhasha.backend.native_x86 import emit_native
 from bhasha.optimizer import optimize
 _,tree,ds,ir=compile_text(source);assert not ds
 for action in (lambda:run(tree),lambda:execute(ir),lambda:execute(optimize(ir)[0])):
  with pytest.raises(ZeroDivisionError):action()
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=3)
  assert result.returncode==2 and 'division by zero' in result.stderr

@pytest.mark.parametrize('ending',['dekhao 1 / 0;','dhoro purno[2] a; dekhao a[2];','dhoro purno n; poro n;'])
def test_output_before_runtime_error_is_preserved(tmp_path,ending,capsys):
 from bhasha.cli import main
 from bhasha.backend.native_x86 import emit_native
 source='dekhao "before"; '+ending
 file=tmp_path/'error.bh';file.write_text(source)
 _,tree,ds,_=compile_text(source);assert not ds
 for args in (['--run'],['--run-tac']):
  with pytest.MonkeyPatch.context() as monkeypatch:
   monkeypatch.setattr('builtins.input',lambda: (_ for _ in ()).throw(EOFError()))
   assert main([str(file),*args])==2
  output=capsys.readouterr();assert output.out=='before\n' and 'error' in output.err
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  result=subprocess.run([str(exe)],input='',capture_output=True,text=True,timeout=3)
  assert result.returncode==2 and result.stdout=='before\n' and 'runtime error' in result.stderr

def test_direct_for_continue_advances(tmp_path):
 source='dhoro purno s = 0; cholo i = 0 theke 5 { jodi i == 2 { choluk; } s = s + i; } dekhao s;'
 _,tree,ds,_=compile_text(source); assert not ds
 exe=tmp_path/'loop'; emit_direct(tree,exe)
 result=subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3)
 assert result.stdout=='8\n'

def test_direct_for_limit_is_evaluated_once(tmp_path):
 source='dhoro purno limit = 3; dhoro purno count = 0; cholo i = 0 theke limit { count = count + 1; limit = 0; } dekhao count;'
 _,tree,ds,_=compile_text(source);assert not ds
 exe=tmp_path/'limit';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='3\n'

def test_native_for_limit_matches_vm(tmp_path):
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.vm import run
 source='dhoro purno limit = 3; dhoro purno count = 0; cholo i = 0 theke limit { count = count + 1; limit = 0; } dekhao count;'
 _,tree,ds,_=compile_text(source);assert not ds
 exe=tmp_path/'limit';emit_native(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==run(tree)=='3\n'

def test_direct_large_array_is_zero_initialized(tmp_path):
 _,tree,ds,_=compile_text('dhoro purno[20] a; a[19] = 7; dekhao a[0] + a[19];')
 assert not ds
 exe=tmp_path/'array';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='7\n'
def test_direct_x86_integer_program(tmp_path):
 _,tree,ds,_=compile_text('dhoro purno x = 7; dhoro purno y = 3; dekhao x * y + 1;')
 assert not ds; exe=tmp_path/'direct';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True).stdout=='22\n'
def test_direct_x86_division_and_modulo(tmp_path):
 _,tree,ds,_=compile_text('dekhao 17 / 5; dekhao 17 % 5;')
 assert not ds;exe=tmp_path/'div';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True).stdout=='3\n2\n'
def test_direct_x86_comparisons(tmp_path):
 _,tree,ds,_=compile_text('dekhao 2 < 3; dekhao 4 == 4; dekhao 5 != 5;')
 assert not ds;exe=tmp_path/'cmp';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True).stdout=='true\ntrue\nfalse\n'
def test_direct_x86_recursive_function(tmp_path):
 source='kaj fact(purno n): purno { jodi n <= 1 { ferot 1; } ferot n * fact(n - 1); } dekhao fact(5);'
 _,tree,ds,_=compile_text(source); assert not ds;exe=tmp_path/'fact';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True).stdout=='120\n'

def test_direct_cli_factorial(tmp_path):
 from bhasha.cli import main
 from pathlib import Path
 example=Path(__file__).parents[1]/'examples'/'factorial.bh'
 exe=tmp_path/'fact'
 assert main([str(example),'--direct-x86','-o',str(exe)]) == 0
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='120\n'
 assert exe.with_suffix('.s').exists()

def test_integer_division_and_booleans_match_backends(tmp_path):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 source='dekhao 17 / 5; dekhao (0 - 17) / 5; dekhao (0 - 17) % 5; dekhao 2 < 3; dekhao mittha;'
 _,tree,ds,_=compile_text(source);assert not ds
 expected='3\n-3\n-2\ntrue\nfalse\n';assert run(tree)==expected
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==expected

def test_integer_input_three_backends(tmp_path):
 from bhasha.backend.vm import VM
 from bhasha.backend.native_x86 import emit_native
 _,tree,ds,ir=compile_text('dhoro purno x; poro x; dekhao x + 1;')
 assert not ds and 'read x' in ir
 vm=VM(input_fn=lambda:'41');vm.exec(tree,vm.global_env);assert vm.output==['42']
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],input='41\n',capture_output=True,text=True,check=True,timeout=3).stdout=='42\n'

@pytest.mark.parametrize(('typ','input_text'), [('purno','abc\n'),('purno',''),('purno','12abc\n'),('purno','2 3\n'),('doshomik','abc\n'),('doshomik',''),('doshomik','1.5bad\n'),('doshomik','0x1p2\n')])
def test_native_invalid_input_returns_runtime_error(tmp_path,typ,input_text):
 from bhasha.backend.native_x86 import emit_native
 _,tree,ds,_=compile_text(f'dhoro {typ} x; poro x; dekhao x;');assert not ds
 from bhasha.backend.vm import VM
 with pytest.raises(ValueError):VM(input_fn=lambda:input_text).exec(tree,{})
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  result=subprocess.run([str(exe)],input=input_text,capture_output=True,text=True,timeout=3)
  assert result.returncode==2 and 'invalid or missing input' in result.stderr

def test_multiple_input_lines_match_backends(tmp_path):
 from bhasha.backend.vm import VM
 from bhasha.backend.native_x86 import emit_native
 source='dhoro purno x; dhoro doshomik y; poro x; poro y; dekhao x + y;'
 _,tree,ds,_=compile_text(source);assert not ds
 values=iter(['  -4  ','  +6.5e0  ']);vm=VM(input_fn=lambda:next(values));vm.exec(tree,vm.global_env)
 assert vm.output==['2.5']
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],input='  -4  \n  +6.5e0  \n',capture_output=True,text=True,check=True,timeout=3).stdout=='2.5\n'

def test_direct_string_boolean_and_unary(tmp_path):
 from bhasha.backend.vm import run
 source='dhoro huen b = shotto; dekhao "বাংলা %s"; dekhao na b; dekhao -7;'
 _,tree,ds,_=compile_text(source);assert not ds
 exe=tmp_path/'strings';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout == run(tree)

def test_direct_global_and_shadowing(tmp_path):
 from bhasha.backend.vm import run
 source='dhoro purno x = 1; kaj f(purno x): purno { ferot x + 1; } kaj g(): purno { x = x + 1; ferot x; } { dhoro purno x = 8; dekhao x; } dekhao f(2); dekhao g(); dekhao x;'
 _,tree,ds,_=compile_text(source);assert not ds
 exe=tmp_path/'globals';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==run(tree)=='8\n3\n2\n2\n'

def test_compound_integer_assignment_matches_all_backends(tmp_path):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.tac_vm import execute
 from bhasha.optimizer import optimize
 source='dhoro purno x = 17; x += 3; x -= 2; x *= 2; x /= 5; dekhao x;'
 _,tree,ds,ir=compile_text(source);assert not ds
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])=='7\n'
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='7\n'

def test_logical_short_circuit_across_backends(tmp_path):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.tac_vm import execute
 from bhasha.optimizer import optimize
 source='dhoro purno x = 0; kaj bump(): huen { x += 1; ferot shotto; } dekhao mittha ebong bump(); dekhao shotto ba bump(); dekhao x;'
 _,tree,ds,ir=compile_text(source);assert not ds
 expected='false\ntrue\n0\n'
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])==expected
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==expected

@pytest.mark.parametrize('source',[
 'dhoro doshomik x = 5; dekhao x / 2;',
 'dhoro doshomik x = 1.25; x = x + 1; dekhao x;',
 'dekhao -1.25 * 2;',
])
def test_direct_float_arithmetic_matches_vm(tmp_path,source):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 _,tree,ds,_=compile_text(source);assert not ds
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==run(tree)

def test_float_format_and_comparisons_across_backends(tmp_path):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.tac_vm import execute
 from bhasha.optimizer import optimize
 source='dekhao -1.5 * 2; dekhao 1.23456789; dekhao 2.5 > 2; dekhao 2.0 == 2; dekhao 1.5 >= 2;'
 _,tree,ds,ir=compile_text(source);assert not ds
 expected='-3\n1.23457\ntrue\ntrue\nfalse\n'
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])==expected
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==expected

def test_float_input_and_compound_assignment(tmp_path):
 from bhasha.backend.vm import VM
 from bhasha.backend.native_x86 import emit_native
 from bhasha.backend.tac_vm import execute
 from bhasha.optimizer import optimize
 source='dhoro doshomik x; poro x; x += 2; x *= 2; x -= 1; x /= 2; dekhao x;'
 _,tree,ds,ir=compile_text(source);assert not ds
 vm=VM(input_fn=lambda:'3.5');vm.exec(tree,vm.global_env)
 assert vm.output==['5']
 assert execute(ir,input_fn=lambda:'3.5')==execute(optimize(ir)[0],input_fn=lambda:'3.5')=='5\n'
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],input='3.5\n',capture_output=True,text=True,check=True,timeout=3).stdout=='5\n'

def test_direct_local_float_array_and_bounds(tmp_path):
 source='{ dhoro doshomik[2] a; a[0] = 5; a[1] = 2; dekhao a[0] / a[1]; }'
 _,tree,ds,_=compile_text(source);assert not ds
 exe=tmp_path/'local_float_array';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='2.5\n'
 _,tree,ds,_=compile_text('dhoro doshomik[2] a; a[-1] = 1.5;');assert not ds
 emit_direct(tree,exe);result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=3)
 assert result.returncode==2 and 'out of bounds' in result.stderr

@pytest.mark.parametrize('source',[
 'kaj half(doshomik x): doshomik { ferot x / 2; } dekhao half(5);',
 'kaj mix(purno a, doshomik b, purno c, doshomik d): doshomik { ferot a + b + c + d; } dekhao mix(1, 2.5, 3, 4.5);',
 'kaj half(doshomik x): doshomik { ferot x / 2; } dekhao half(half(9));',
 'kaj f(): doshomik { ferot 5; } dekhao f() / 2;',
 'kaj scale(purno n, doshomik x): doshomik { jodi n == 0 { ferot x; } ferot scale(n - 1, x / 2); } dekhao scale(2, 9);',
])
def test_direct_float_function_abi_matches_vm(tmp_path,source):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 _,tree,ds,_=compile_text(source);assert not ds
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==run(tree)

@pytest.mark.parametrize('source',[
 'kaj f(purno a,purno b,purno c,purno d,purno e,purno f,purno g,purno h): purno { ferot a + g + h; } dekhao f(1,2,3,4,5,6,7,8);',
 'kaj f(doshomik a,doshomik b,doshomik c,doshomik d,doshomik e,doshomik f,doshomik g,doshomik h,doshomik i): doshomik { ferot a + i; } dekhao f(1,2,3,4,5,6,7,8,9);',
 'kaj f(purno a,purno b,purno c,purno d,purno e,purno f,purno g,doshomik h,doshomik i,doshomik j,doshomik k,doshomik l,doshomik m,doshomik n,doshomik o,doshomik p): doshomik { ferot g + p; } dekhao f(1,2,3,4,5,6,7,1,2,3,4,5,6,7,8,9);',
])
def test_direct_stack_arguments_match_vm_and_c(tmp_path,source):
 from bhasha.backend.vm import run
 from bhasha.backend.native_x86 import emit_native
 _,tree,ds,_=compile_text(source);assert not ds
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==run(tree)
