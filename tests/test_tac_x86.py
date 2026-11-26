"""Execute the explicit integer TAC-to-assembly subset against the VM."""
import subprocess

import pytest

from bhasha.backend.tac_x86 import TacX86Error, emit_tac_x86
from bhasha.backend.vm import run
from bhasha.cli import compile_text, main
from bhasha.optimizer import optimize


@pytest.mark.parametrize('source', [
    'dekhao 7 * 3 + 1; dekhao -17 / 5; dekhao -17 % 5;',
    'kaj fact(purno n): purno { jodi n <= 1 { ferot 1; } ferot n * fact(n - 1); } dekhao fact(5);',
    'dhoro purno s = 0; cholo i = 0 theke 5 { jodi i == 2 { choluk; } s += i; } dekhao s;',
    'dhoro purno x = 1; kaj f(purno n): purno { x += n; ferot x; } dekhao f(3); dekhao x;',
    'kaj f(purno a,purno b,purno c,purno d,purno e,purno f): purno { ferot a+b+c+d+e+f; } dekhao f(1,2,3,4,5,6);',
    'kaj f(purno a,purno b,purno c,purno d,purno e,purno f,purno g,purno h,purno i): purno { ferot a+g+h+i; } dekhao f(1,2,3,4,5,6,7,8,9);',
    'dhoro purno সংখ্যা = 7; { dhoro purno সংখ্যা = 2; dekhao সংখ্যা; } dekhao সংখ্যা;',
])
@pytest.mark.parametrize('optimized', [False, True])
def test_tac_x86_matches_vm(tmp_path, source, optimized):
    _, tree, diagnostics, ir = compile_text(source)
    assert not diagnostics
    exe = tmp_path / 'program'
    emit_tac_x86(tree, optimize(ir)[0] if optimized else ir, exe)
    result = subprocess.run([str(exe)], capture_output=True, text=True, check=True, timeout=3)
    assert result.stdout == run(tree)


@pytest.mark.parametrize('source', [
    'dekhao 2.5;', 'dekhao "hello";', 'dekhao shotto;',
    'dhoro purno[2] a; dekhao a[0];',
])
def test_tac_x86_rejects_unsupported_features(tmp_path, source):
    _, tree, diagnostics, ir = compile_text(source)
    assert not diagnostics
    with pytest.raises(TacX86Error): emit_tac_x86(tree, ir, tmp_path / 'program')


def test_tac_x86_cli_and_runtime_error(tmp_path, capsys):
    source = tmp_path / 'program.bh'; source.write_text('dekhao 5; dekhao 1 / 0;')
    exe = tmp_path / 'program'
    assert main([str(source), '--tac-x86', '-o', str(exe)]) == 0
    capsys.readouterr()
    result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=3)
    assert result.returncode == 2
    assert result.stdout == '5\n'
    assert 'division by zero' in result.stderr


@pytest.mark.parametrize(('data','status','output'), [('41\n',0,'42\n'),('bad\n',2,''),('',2,'')])
def test_tac_x86_integer_input(tmp_path, data, status, output):
    _, tree, diagnostics, ir = compile_text('dhoro purno x; poro x; dekhao x + 1;')
    assert not diagnostics
    exe=tmp_path/'input';emit_tac_x86(tree,ir,exe)
    result=subprocess.run([str(exe)],input=data,capture_output=True,text=True,timeout=3)
    assert result.returncode == status and result.stdout == output
    if status: assert 'invalid or missing input' in result.stderr
