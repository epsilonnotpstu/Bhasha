"""Golden outputs prove VM and native ELF agree for shipped examples."""
import subprocess
from pathlib import Path
import pytest
from bhasha.cli import compile_text
from bhasha.backend.vm import run
from bhasha.backend.native_x86 import emit_native

ROOT=Path(__file__).parents[1]
EXAMPLES=['hello','arithmetic','factorial','loop','gcd','condition']
@pytest.mark.parametrize('name',EXAMPLES)
def test_vm_and_native_match_expected(name,tmp_path):
 source=(ROOT/'examples'/f'{name}.bh').read_text(encoding='utf8')
 expected=(ROOT/'examples'/f'{name}.expected').read_text(encoding='utf8')
 _,tree,diagnostics,_=compile_text(source,str(ROOT/'examples'/f'{name}.bh'))
 assert not diagnostics
 assert run(tree)==expected
 executable=tmp_path/name
 emit_native(tree,executable)
 assert subprocess.run([str(executable)],capture_output=True,text=True,check=True).stdout==expected
