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
def test_semantic_undeclared_error():
 _,_,ds,_=compile_text('dekhao missing;'); assert "undeclared" in ds[0].message
def test_optimizer_folds_and_removes_dead_temp():
 out,stats=optimize(['t1 = 2 + 3','t2 = 9 * 1','print t1']); assert out==['t1 = 5','print t1']; assert stats['dead_code']==1
def test_optimizer_propagates_constant_within_block():
 out,stats=optimize(['t1 = 4','t2 = t1 + 0','print t2']); assert out==['t2 = 4','print t2']; assert stats['copy_propagations'] >= 1
def test_optimizer_dce_keeps_value_used_after_branch():
 ir=['t1 = 4','ifFalse c goto else1','print t1','goto end1','else1:','print t1','end1:']
 out,stats=optimize(ir); assert 't1 = 4' in out and stats['dead_code']==0
def test_wat_for_constant_arithmetic():
 _,tree,ds,_=compile_text('dekhao 2 + 3;'); assert not ds; wat=emit_wat(tree); assert 'i32.add' in wat and '(export "run")' in wat
def test_wat_rejects_variables():
 _,tree,ds,_=compile_text('dhoro purno x = 2; x += 3; dekhao x * 4;'); assert not ds
 wat=emit_wat(tree); assert 'local.set $x' in wat and 'i32.mul' in wat
def test_wat_rejects_float():
 _,tree,ds,_=compile_text('dekhao 2.5;'); assert not ds
 with pytest.raises(WasmError): emit_wat(tree)
def test_wat_emits_if_and_loop_blocks():
 source='dhoro purno x = 0; jotokkhon x < 2 { x += 1; } jodi x == 2 { dekhao x; } nahole { dekhao 0; }'
 _,tree,ds,_=compile_text(source); assert not ds
 wat=emit_wat(tree)
 assert 'block $break1' in wat and 'loop $loop1' in wat and 'br_if $break1' in wat and '\nif\n' in wat
def test_cli_error_code(tmp_path, capsys):
 f=tmp_path/'bad.bh';f.write_text('dekhao unknown;'); assert main([str(f),'--run']) == 1; assert 'undeclared' in capsys.readouterr().err
