from bhasha.cli import compile_text,main
from bhasha.semantic import analyze

def test_uninitialized_and_unused_are_warnings(tmp_path,capsys):
 source='dhoro purno x; dhoro purno unused = 4; dekhao x;'
 _,tree,errors,ir=compile_text(source);assert not errors and ir
 _,analyzer=analyze(tree,'test.bh')
 assert any('uninitialized' in d.message and d.kind=='warning' for d in analyzer.warnings)
 assert any('unused variable' in d.message and d.kind=='warning' for d in analyzer.warnings)
 file=tmp_path/'warning.bh';file.write_text(source)
 assert main([str(file),'--run'])==0
 result=capsys.readouterr();assert result.out=='0\n' and 'warning:' in result.err

def test_unused_shadowed_variables_report_correct_scope():
 _,tree,errors,_=compile_text('dhoro purno x = 1; { dhoro purno x = 2; dekhao x; }')
 assert not errors
 _,analyzer=analyze(tree)
 assert sum("unused variable 'x'" in warning.message for warning in analyzer.warnings)==1

def warnings_for(source):
 _,tree,errors,_=compile_text(source);assert not errors
 _,analyzer=analyze(tree)
 return [d.message for d in analyzer.warnings if 'uninitialized' in d.message]

def test_branch_initialization_requires_both_paths():
 assert warnings_for('dhoro purno x; jodi shotto { x = 1; } dekhao x;')
 assert not warnings_for('dhoro purno x; jodi shotto { x = 1; } nahole { x = 2; } dekhao x;')
 assert warnings_for('dhoro purno x; jodi shotto { x = 1; } nahole { dekhao x; }')

def test_loop_body_and_uninvoked_function_do_not_initialize_outer():
 assert warnings_for('dhoro purno x; jotokkhon mittha { x = 1; } dekhao x;')
 assert warnings_for('dhoro purno x; cholo i = 0 theke 0 { x = 1; } dekhao x;')
 assert warnings_for('dhoro purno x; kaj f(): purno { x = 1; ferot 0; } dekhao x;')
