from pathlib import Path
from bhasha.cli import compile_text
from bhasha.backend.native_x86 import emit_native, emit_assembly
from bhasha.cfg_new import build_cfg
def test_cfg_has_block():
 _,_,d,ir=compile_text('dhoro purno x = 0; jotokkhon x < 2 { x += 1; }'); assert not d; assert len(build_cfg(ir).blocks) > 1
def test_cfg_return_and_function_boundaries_do_not_fall_through():
 cfg=build_cfg(['print 1','func f:','return 2','endfunc','print 3'])
 for a,b in cfg.edges:
  assert not cfg.blocks[a][-1].startswith('return ')
  assert cfg.blocks[a][-1]!='endfunc'
  assert not cfg.blocks[b][0].startswith('func ')
def test_for_continue_targets_increment():
 _,_,d,ir=compile_text('cholo i = 0 theke 5 { choluk; }');assert not d
 step=next(line[:-1] for line in ir if line.startswith('step') and line.endswith(':'))
 assert f'goto {step}' in ir
 assert ir[ir.index(step+':')+1]=='i += 1'
def test_native_elf(tmp_path):
 _,tree,d,_=compile_text('dekhao 7;'); assert not d
 exe=tmp_path/'seven'; emit_native(tree,exe); assert exe.exists()
def test_native_assembly(tmp_path):
 _,tree,d,_=compile_text('dekhao 7;'); assert not d
 asm=tmp_path/'seven.s'; emit_assembly(tree,asm); assert '.text' in asm.read_text()
def test_native_optimization_levels(tmp_path):
 import subprocess
 _,tree,d,_=compile_text('dekhao 7;');assert not d
 for level in (0,1,2):
  exe=tmp_path/f'seven{level}';emit_native(tree,exe,opt_level=level)
  assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout=='7\n'
def test_native_global_access_and_shadowing(tmp_path):
 import subprocess
 from bhasha.backend.vm import run
 source='dhoro purno x = 1; kaj f(): purno { x = x + 1; ferot x; } { dhoro purno x = 8; dekhao x; } dekhao f(); dekhao x;'
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 exe=tmp_path/'globals';emit_native(tree,exe)
 assert subprocess.run([str(exe)],capture_output=True,text=True,check=True,timeout=3).stdout==run(tree)=='8\n2\n2\n'
