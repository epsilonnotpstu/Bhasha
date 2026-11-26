from bhasha.cli import compile_text, main
from bhasha.semantic import analyze

def test_scope_tables_keep_shadowed_symbols_and_parents(tmp_path,capsys):
 source='dhoro purno x = 1; { dhoro huen x = shotto; dekhao x; } dekhao x;'
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 _,analyzer=analyze(tree);tables=analyzer.symbol_tables()
 assert tables[0]['kind']=='global' and tables[0]['symbols'][0]['type']=='int'
 assert tables[1]['parent']==0 and tables[1]['symbols'][0]['type']=='bool'
 file=tmp_path/'scopes.bh';file.write_text(source)
 assert main([str(file),'--symtab'])==0
 output=capsys.readouterr().out
 assert 'Scope 0 (global' in output and 'Scope 1 (block' in output and 'bool' in output

def test_called_function_is_marked_used():
 _,tree,diagnostics,_=compile_text('kaj f(): purno { ferot 1; } dekhao f();');assert not diagnostics
 _,analyzer=analyze(tree)
 assert analyzer.symbol_tables()[0]['symbols'][0]['used'] is True

def test_assignment_initializes_without_false_read_error():
 _,tree,diagnostics,_=compile_text('dhoro purno x; x = 3; dekhao x;')
 assert not diagnostics
 from bhasha.backend.vm import run
 assert run(tree)=='3\n'

def test_loop_variable_has_own_scope():
 _,_,diagnostics,_=compile_text('cholo i = 0 theke 2 { } dekhao i;')
 assert any('undeclared' in d.message for d in diagnostics)
 _,_,diagnostics,_=compile_text('cholo i = 0.5 theke 2 { }')
 assert any('for start must be int' in d.message for d in diagnostics)
