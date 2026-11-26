"""Optional real Wasmtime compilation and execution of generated WAT."""
import pytest
wasmtime=pytest.importorskip('wasmtime',reason='optional Wasmtime package is not installed')
from bhasha.cli import compile_text
from bhasha.backend.wasm_new import emit_wat

@pytest.mark.parametrize(('source','expected'),[
 ('dhoro purno x = 2; { dhoro purno x = 8; } dekhao x;',2),
 ('dhoro purno out = 7; dekhao out;',7),
 ('dhoro purno সংখ্যা = 4; dekhao সংখ্যা;',4),
 ('dhoro purno x = 0; cholo i = 0 theke 5 { jodi i == 2 { choluk; } x += i; } dekhao x;',8),
 ('dhoro purno x = 0; jotokkhon shotto { x += 1; jodi x == 3 { thamo; } } dekhao x;',3),
 ('jodi shotto ebong na mittha { dekhao 7; } nahole { dekhao 0; }',7),
 ('kaj fact(purno n): purno { jodi n <= 1 { ferot 1; } ferot n * fact(n - 1); } dekhao fact(5);',120),
 ('kaj fib(purno n): purno { jodi n <= 1 { ferot n; } ferot fib(n-1) + fib(n-2); } dekhao fib(8);',21),
 ('kaj add(purno a, purno b): purno { ferot a + b; } dekhao add(3,4);',7),
 ('dhoro purno x = 1; kaj bump(): purno { x += 1; ferot x; } dekhao bump(); dekhao x;',2),
 ('dhoro purno x = 9; kaj f(purno x): purno { ferot x + 1; } dekhao f(2); dekhao x;',9),
 ('dhoro purno i = 2; cholo i = i theke 4 { } dekhao i;',2),
 ('dhoro purno[3] a; a[0] = 2; a[1] = 3; dekhao a[0] + a[1] + a[2];',5),
 ('dhoro purno[3] a; kaj f(): purno { a[1] = 9; ferot a[1]; } dekhao f();',9),
 ('dhoro doshomik x = 5; dekhao x / 2;',2.5),
 ('dhoro doshomik x = 1.25; x += 1; x *= 2; dekhao x;',4.5),
 ('jodi 1.5 < 2 { dekhao 3.5; } nahole { dekhao 1.5; }',3.5),
 ('kaj half(doshomik x): doshomik { ferot x / 2; } dekhao half(5);',2.5),
 ('dhoro doshomik x = 2; kaj f(): doshomik { x += 0.5; ferot x; } dekhao f();',2.5),
 ('kaj f(): doshomik { ferot 5; } dekhao f() / 2;',2.5),
 ('kaj scale(purno n, doshomik x): doshomik { jodi n == 0 { ferot x; } ferot scale(n - 1, x / 2); } dekhao scale(2, 9);',2.25),
 ('dhoro doshomik[2] a; a[0] = 5; a[1] = 2; dekhao a[0] / a[1];',2.5),
 ('dhoro purno[1] a; dhoro doshomik[2] b; a[0] = 9; b[0] = 1.5; b[1] = 2; dekhao a[0] + b[0] + b[1];',12.5),
 ('dhoro doshomik[2] a; kaj f(): doshomik { a[1] = 2.5; ferot a[1]; } dekhao f();',2.5),
 ('kaj f(purno n): purno { dhoro purno[1] a; a[0] = n; jodi n <= 1 { ferot a[0]; } ferot a[0] + f(n-1); } dekhao f(4);',10),
 ('dhoro purno[1] a; a[0] = 7; { dhoro doshomik[2] a; a[0] = 1.5; } dekhao a[0];',7),
 ('kaj f(): doshomik { dhoro doshomik[2] a; a[0] = 2.5; ferot a[0]; } dekhao f();',2.5),
 ('dhoro purno x = 0; cholo i = 0 theke 3 { dhoro purno[1] a; x += a[0]; a[0] = 5; } dekhao x;',0),
 ('dhoro purno x = 0; cholo i = 0 theke 3 { dhoro purno a; x += a; a = 5; } dekhao x;',0),
 ('kaj f(): purno { dhoro purno[20000] a; a[19999] = 42; ferot a[19999]; } dekhao f();',42),
])
def test_wat_compiles_and_runs(source,expected):
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree));store=wasmtime.Store(engine)
 instance=wasmtime.Instance(store,module,[])
 assert instance.exports(store)['run'](store)==expected

@pytest.mark.parametrize('statement',['dekhao a[-1];','a[-1] = 7;','dekhao a[2];','a[2] = 7;'])
def test_wat_array_out_of_bounds_traps(statement):
 _,tree,diagnostics,_=compile_text('dhoro purno[2] a; '+statement);assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree));store=wasmtime.Store(engine)
 instance=wasmtime.Instance(store,module,[])
 with pytest.raises(wasmtime.Trap):instance.exports(store)['run'](store)

def test_wat_float_division_by_zero_traps():
 _,tree,diagnostics,_=compile_text('dekhao 1.5 / 0.0;');assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree));store=wasmtime.Store(engine)
 instance=wasmtime.Instance(store,module,[])
 with pytest.raises(wasmtime.Trap):instance.exports(store)['run'](store)

@pytest.mark.parametrize('index',['-1','2'])
def test_local_array_out_of_bounds_traps(index):
 source=f'kaj f(): purno {{ dhoro purno[2] a; ferot a[{index}]; }} dekhao f();'
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree));store=wasmtime.Store(engine)
 instance=wasmtime.Instance(store,module,[])
 with pytest.raises(wasmtime.Trap):instance.exports(store)['run'](store)

def test_run_can_be_retried_after_local_array_trap():
 source='kaj f(): purno { dhoro purno[2] a; ferot a[2]; } dekhao f();'
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree));store=wasmtime.Store(engine)
 instance=wasmtime.Instance(store,module,[])
 for _ in range(2):
  with pytest.raises(wasmtime.Trap):instance.exports(store)['run'](store)

def test_run_reinitializes_uninitialized_globals():
 source='dhoro purno x; kaj f(): purno { x += 1; ferot x; } dekhao f();'
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree));store=wasmtime.Store(engine)
 run=wasmtime.Instance(store,module,[]).exports(store)['run']
 assert run(store)==1
 assert run(store)==1

def test_host_io_supports_mixed_output_input_functions_and_arrays():
 source='''dhoro purno[2] a; dhoro purno x; poro x; a[0] = x;
 kaj show(purno n): purno { dhoro purno[1] local; local[0] = n; dekhao "বাংলা"; dekhao local[0]; ferot local[0]; }
 dekhao show(a[0]); dekhao shotto; dhoro doshomik y; poro y; dekhao y;'''
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 engine=wasmtime.Engine();module=wasmtime.Module(engine,emit_wat(tree,host_io=True));store=wasmtime.Store(engine)
 i32=wasmtime.ValType.i32();f64=wasmtime.ValType.f64();output=[]
 def show_string(caller,ptr,length):
  output.append(bytes(caller.get('memory').read(caller,ptr,ptr+length)).decode('utf8'))
 imports=[
  wasmtime.Func(store,wasmtime.FuncType([i32],[]),lambda value:output.append(str(value))),
  wasmtime.Func(store,wasmtime.FuncType([i32],[]),lambda value:output.append('true' if value else 'false')),
  wasmtime.Func(store,wasmtime.FuncType([f64],[]),lambda value:output.append(str(value))),
  wasmtime.Func(store,wasmtime.FuncType([i32,i32],[]),show_string,access_caller=True),
  wasmtime.Func(store,wasmtime.FuncType([],[i32]),lambda:5),
  wasmtime.Func(store,wasmtime.FuncType([],[f64]),lambda:2.5),
 ]
 instance=wasmtime.Instance(store,module,imports)
 assert instance.exports(store)['run'](store)==0
 assert output==['বাংলা','5','5','true','2.5']
