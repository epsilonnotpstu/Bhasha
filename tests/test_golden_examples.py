"""Golden outputs prove VM and native ELF agree for shipped examples."""
import subprocess
import shutil
from pathlib import Path
import pytest
from bhasha.cli import compile_text
from bhasha.backend.vm import run
from bhasha.backend.native_x86 import emit_native
from bhasha.backend.direct_x86 import emit_direct
from bhasha.backend.tac_vm import execute
from bhasha.optimizer import optimize

ROOT=Path(__file__).parents[1]
EXAMPLES=['hello','arithmetic','factorial','loop','gcd','condition','fibonacci_iterative','fibonacci_recursive','array_sum_max','function_heavy','optimization_demo']
@pytest.mark.parametrize('name',EXAMPLES)
def test_vm_and_tac_match_expected(name):
 source=(ROOT/'examples'/f'{name}.bh').read_text(encoding='utf8')
 expected=(ROOT/'examples'/f'{name}.expected').read_text(encoding='utf8')
 _,tree,diagnostics,ir=compile_text(source,str(ROOT/'examples'/f'{name}.bh'))
 assert not diagnostics
 assert run(tree)==expected
 assert execute(ir)==expected
 assert execute(optimize(ir)[0])==expected

@pytest.mark.skipif(shutil.which('gcc') is None,reason='gcc missing: native ELF toolchain unavailable')
@pytest.mark.parametrize('name',EXAMPLES)
@pytest.mark.parametrize('backend,level', [('gcc',0),('gcc',2),('direct',0),('direct',2)])
def test_native_golden_examples(name,backend,level,tmp_path):
 source=(ROOT/'examples'/f'{name}.bh').read_text(encoding='utf8')
 expected=(ROOT/'examples'/f'{name}.expected').read_text(encoding='utf8')
 _,tree,diagnostics,_=compile_text(source);assert not diagnostics
 executable=tmp_path/name
 if backend=='gcc':emit_native(tree,executable,opt_level=level)
 else:emit_direct(tree,executable)  # direct assembly currently has no optimization levels
 assert subprocess.run([str(executable)],capture_output=True,text=True,check=True,timeout=5).stdout==expected
