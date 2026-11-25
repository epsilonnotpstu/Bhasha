from bhasha.cli import main
def test_emit_all_creates_inspection_files(tmp_path):
 source=tmp_path/'p.bh';source.write_text('dekhao 3;')
 target=tmp_path/'artifacts'
 assert main([str(source),'--emit-all',str(target)]) == 0
 assert {x.name for x in target.iterdir()} == {'tokens.txt','ast.json','tac.txt','optimized-tac.txt','cfg.dot','program.wat'}
