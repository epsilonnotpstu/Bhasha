import pytest
from bhasha.lexer import lex
from bhasha.parser import parse
from bhasha.cli import compile_text, main
from bhasha.optimizer import optimize
from bhasha.backend.wasm_new import emit_wat, WasmError

def test_lexer_reports_bad_character():
 _, ds=lex('dhoro purno x = @;'); assert "invalid character" in ds[0].message
def test_lexer_reports_unterminated_string():
 _, ds=lex('dekhao "oops'); assert "unterminated string" in ds[0].message
def test_parser_reports_multiple_error_shape():
 tokens,_=lex('dhoro purno = 1; dekhao ;'); _,ds=parse(tokens); assert ds and ds[0].line == 1
def test_parser_recovers_after_stray_brace_and_reports_multiple_errors():
 tokens,_=lex('}\ndhoro purno = 1;\ndekhao ;\ndekhao 7;')
 tree,ds=parse(tokens,'bad.bh')
 assert [d.line for d in ds]==[1,2,3]
 assert "unexpected '}'" in ds[0].message and len(tree.statements)==1
 assert all('^' in d.render('}\ndhoro purno = 1;\ndekhao ;\ndekhao 7;') for d in ds)
def test_parser_missing_return_type_at_eof():
 tokens,_=lex('kaj f():');_,ds=parse(tokens)
 assert ds and 'return type' in ds[0].message
def test_semantic_undeclared_error():
 _,_,ds,_=compile_text('dekhao missing;'); assert "undeclared" in ds[0].message
def test_semantic_missing_return_and_complete_branches():
 _,_,ds,_=compile_text('kaj f(purno x): purno { jodi x > 0 { ferot x; } }')
 assert any('without returning' in d.message for d in ds)
 _,_,ds,_=compile_text('kaj f(purno x): purno { jodi x > 0 { ferot x; } nahole { ferot 0; } }')
 assert not ds
@pytest.mark.parametrize('source',['dekhao 2 ebong shotto;','dekhao na 7;','dekhao 2.5 % 2;','jodi 1 { dekhao 1; }','jotokkhon 2 { thamo; }','dekhao shotto < 3;'])
def test_semantic_rejects_invalid_operator_types(source):
 _,_,ds,_=compile_text(source);assert ds
def test_vm_integer_widening_preserves_float_division():
 from bhasha.backend.vm import run
 _,tree,ds,_=compile_text('dhoro doshomik x = 5; dekhao x / 2;');assert not ds
 assert run(tree)=='2.5\n'
def test_optimizer_folds_and_removes_dead_temp():
 out,stats=optimize(['t1 = 2 + 3','t2 = 9 * 1','print t1']); assert out==['print 5']; assert stats['dead_code']==2
def test_optimizer_propagates_constant_within_block():
 out,stats=optimize(['t1 = 4','t2 = t1 + 0','print t2']); assert out==['print 4']; assert stats['copy_propagations'] >= 1
def test_optimizer_dce_keeps_value_used_after_branch():
 ir=['t1 = 4','ifFalse c goto else1','print t1','goto end1','else1:','print t1','end1:']
 out,stats=optimize(ir); assert 't1 = 4' in out and stats['dead_code']==0
def test_optimizer_integer_division_and_remainder():
 out,_=optimize(['t1 = -17 / 5','t2 = -17 % 5','print t1','print t2'])
 assert out == ['print -3','print -2']
def test_optimizer_preserves_potential_traps():
 out,_=optimize(['t1 = 1 / 0','t2 = a[i]','print 1'])
 assert 't1 = 1 / 0' in out and 't2 = a[i]' in out
def test_optimizer_never_rewrites_destination_or_literal():
 out,_=optimize(['t1 = 1','t1 = 2','print "t1"','print t1'])
 assert '1 = 2' not in out and 'print "t1"' in out
def test_optimizer_does_not_propagate_mutable_alias():
 from bhasha.backend.tac_vm import execute
 ir=['decl purno t1','read t1','t2 = t1','t1 = 8','print t2']
 assert execute(ir,input_fn=lambda:'3')==execute(optimize(ir)[0],input_fn=lambda:'3')=='3\n'

def test_local_common_subexpression_elimination():
 from bhasha.backend.tac_vm import execute
 ir=['read a','read b','t1 = a + b','print t1','t2 = a + b','print t2']
 out,stats=optimize(ir)
 assert stats['common_subexpressions']==1
 assert sum('a + b' in line for line in out)==1
 def run(lines):
  values=iter(['4','5']);return execute(lines,input_fn=lambda:next(values))
 assert run(ir)==run(out)=='9\n9\n'

@pytest.mark.parametrize('mutation',['a = 8','a += 1','read a','t1 = 10','ifFalse False goto next','t3 = call mutate, 0'])
def test_local_common_expression_invalidated_by_mutation(mutation):
 ir=['t1 = a + b',mutation,'t2 = a + b','print t1','print t2']
 if mutation.startswith('ifFalse '):ir.append('next:')
 out,stats=optimize(ir)
 assert stats['common_subexpressions']==0
def test_wat_for_constant_arithmetic():
 _,tree,ds,_=compile_text('dekhao 2 + 3;'); assert not ds; wat=emit_wat(tree); assert 'i32.add' in wat and '(export "run")' in wat
def test_wat_rejects_variables():
 _,tree,ds,_=compile_text('dhoro purno x = 2; x += 3; dekhao x * 4;'); assert not ds
 wat=emit_wat(tree); assert 'local.set $x' in wat and 'i32.mul' in wat
def test_wat_emits_float():
 _,tree,ds,_=compile_text('dekhao 2.5;'); assert not ds
 assert 'f64.const 2.5' in emit_wat(tree)
def test_wat_rejects_print_inside_function():
 _,tree,ds,_=compile_text('kaj f(): purno { dekhao 1; ferot 2; } dekhao f();');assert not ds
 with pytest.raises(WasmError,match='host I/O'):emit_wat(tree)
def test_wat_emits_if_and_loop_blocks():
 source='dhoro purno x = 0; jotokkhon x < 2 { x += 1; } jodi x == 2 { dekhao x; } nahole { dekhao 0; }'
 _,tree,ds,_=compile_text(source); assert not ds
 wat=emit_wat(tree)
 assert 'block $break1' in wat and 'loop $loop1' in wat and 'br_if $break1' in wat and '\nif\n' in wat
def test_wat_for_captures_loop_bound_once():
 _,tree,ds,_=compile_text('dhoro purno n = 3; cholo i = 0 theke n { n = 0; } dekhao n;');assert not ds
 wat=emit_wat(tree)
 assert wat.count('local.get $n')==2
 assert wat.index('local.set $.limit1') < wat.index('loop $loop1')
def test_wat_boolean_and_loop_control_structure():
 source='dhoro huen b = shotto; cholo i = 0 theke 5 { jodi b ebong na mittha { choluk; } thamo; } dekhao b;'
 _,tree,ds,_=compile_text(source);assert not ds
 wat=emit_wat(tree)
 assert 'if (result i32)' in wat and 'i32.eqz' in wat
 assert 'block $continue1' in wat and 'br $continue1' in wat and 'br $break1' in wat
def test_cli_error_code(tmp_path, capsys):
 f=tmp_path/'bad.bh';f.write_text('dekhao unknown;'); assert main([str(f),'--run']) == 1; assert 'undeclared' in capsys.readouterr().err
def test_cli_missing_file_and_runtime_bounds(tmp_path,capsys):
 assert main([str(tmp_path/'missing.bh'),'--run']) == 1
 assert 'source error:' in capsys.readouterr().err
 f=tmp_path/'bounds.bh';f.write_text('dhoro purno[2] a; dekhao a[3];')
 assert main([str(f),'--run']) == 2
 assert 'runtime error:' in capsys.readouterr().err
