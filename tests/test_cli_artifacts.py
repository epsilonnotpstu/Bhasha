from bhasha.cli import main
def test_emit_all_creates_inspection_files(tmp_path):
 source=tmp_path/'p.bh';source.write_text('dekhao 3;')
 target=tmp_path/'artifacts'
 assert main([str(source),'--emit-all',str(target)]) == 0
 assert {x.name for x in target.iterdir()} == {'tokens.txt','ast.json','symtab.json','tac.txt','optimized-tac.txt','cfg.dot','program.wat'}

def test_wat_host_cli_emits_imports_for_input_and_output(tmp_path,capsys):
 source=tmp_path/'p.bh';source.write_text('dhoro purno x; poro x; dekhao x;')
 assert main([str(source),'--wat-host']) == 0
 output=capsys.readouterr().out
 assert '(import "host" "read_i32"' in output
 assert '(import "host" "print_i32"' in output
 assert '(export "memory")' in output
