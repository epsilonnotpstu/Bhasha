import pytest
from bhasha.lexer import lex
from bhasha.parser import parse
from bhasha.cli import compile_text, main
from bhasha.optimizer import optimize
from bhasha.backend.wasm import emit_wat, WasmError

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
def test_wat_for_constant_arithmetic():
 _,tree,ds,_=compile_text('dekhao 2 + 3;'); assert not ds; wat=emit_wat(tree); assert 'i32.add' in wat and '(export "run")' in wat
def test_wat_rejects_variables():
 _,tree,ds,_=compile_text('dhoro purno x = 2; dekhao x;'); assert not ds
 with pytest.raises(WasmError): emit_wat(tree)
def test_cli_error_code(tmp_path, capsys):
 f=tmp_path/'bad.bh';f.write_text('dekhao unknown;'); assert main([str(f),'--run']) == 1; assert 'undeclared' in capsys.readouterr().err
