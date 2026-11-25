from pathlib import Path
from bhasha.cli import compile_text
ROOT=Path(__file__).parents[1]
def test_error_examples_have_expected_diagnostic():
 for kind in ('lexical','syntax','semantic','type'):
  source=(ROOT/'examples'/f'error_{kind}.bh').read_text()
  expected=(ROOT/'examples'/f'error_{kind}.expected').read_text().strip()
  _,_,diagnostics,_=compile_text(source,f'error_{kind}.bh')
  assert diagnostics
  assert expected in diagnostics[0].message
  rendered=diagnostics[0].render(source)
  assert 'error:' in rendered and '^' in rendered
