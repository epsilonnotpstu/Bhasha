"""Measure TAC optimizer statistics for valid examples, output Markdown."""
from pathlib import Path
from bhasha.cli import compile_text
from bhasha.optimizer import optimize
from bhasha.backend.tac_vm import execute
from bhasha.backend.vm import run

def report(root: Path) -> str:
    rows=['| Example | Before | After | Folded | Simplified | Dead |',
          '|---|---:|---:|---:|---:|---:|']
    for expected in sorted((root/'examples').glob('*.expected')):
        if expected.stem.startswith('error_'):continue
        source=expected.with_suffix('.bh').read_text(encoding='utf8')
        _,tree,diagnostics,ir=compile_text(source,str(expected.with_suffix('.bh')))
        if diagnostics:raise ValueError(f'{expected.stem}: compile failed: {diagnostics}')
        optimized,stats=optimize(ir)
        golden=expected.read_text(encoding='utf8')
        if execute(ir)!=golden or execute(optimized)!=golden or run(tree)!=golden:
            raise ValueError(f'{expected.stem}: output mismatch')
        rows.append(f"| {expected.stem} | {stats['before']} | {stats['after']} | {stats['constant_folds']} | {stats['simplified']} | {stats['dead_code']} |")
    return '\n'.join(rows)

if __name__=='__main__':print(report(Path(__file__).resolve().parents[1]))
