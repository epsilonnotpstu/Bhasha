from pathlib import Path
from bhasha.cli import compile_text
from bhasha.backend.native_x86 import emit_native
from bhasha.cfg_new import build_cfg
def test_cfg_has_block():
 _,_,d,ir=compile_text('dhoro purno x = 0; jotokkhon x < 2 { x += 1; }'); assert not d; assert len(build_cfg(ir).blocks) > 1
def test_native_elf(tmp_path):
 _,tree,d,_=compile_text('dekhao 7;'); assert not d
 exe=tmp_path/'seven'; emit_native(tree,exe); assert exe.exists()
