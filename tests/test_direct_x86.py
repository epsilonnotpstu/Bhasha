import subprocess
from bhasha.cli import compile_text
from bhasha.backend.direct_x86 import emit_direct
def test_direct_x86_integer_program(tmp_path):
 _,tree,ds,_=compile_text('dhoro purno x = 7; dhoro purno y = 3; dekhao x * y + 1;')
 assert not ds; exe=tmp_path/'direct';emit_direct(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True).stdout=='22\n'
