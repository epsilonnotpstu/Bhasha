"""Bangla identifiers include combining marks, not just Unicode letters."""
import subprocess
from bhasha.cli import compile_text
from bhasha.backend.vm import run
from bhasha.backend.tac_vm import execute
from bhasha.backend.native_x86 import emit_native
from bhasha.backend.direct_x86 import emit_direct
from bhasha.optimizer import optimize

def test_bangla_identifiers_across_backends(tmp_path):
 source='ধরো পূর্ণ সংখ্যা = 4; কাজ দ্বিগুণ(পূর্ণ মান): পূর্ণ { ফেরত মান * 2; } দেখাও দ্বিগুণ(সংখ্যা);'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])=='8\n'
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='8\n'

def test_bangla_array_name_and_index(tmp_path):
 source='ধরো পূর্ণ[2] সংখ্যা; সংখ্যা[0] = 4; সংখ্যা[1] = 3; দেখাও সংখ্যা[0] + সংখ্যা[1];'
 _,tree,diagnostics,ir=compile_text(source);assert not diagnostics
 assert run(tree)==execute(ir)==execute(optimize(ir)[0])=='7\n'
 for emitter,name in ((emit_native,'native'),(emit_direct,'direct')):
  exe=tmp_path/name;emitter(tree,exe)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='7\n'
