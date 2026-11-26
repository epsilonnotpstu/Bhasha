from pathlib import Path
import importlib.util

spec=importlib.util.spec_from_file_location('optimization_report',Path(__file__).parents[1]/'tools'/'optimization_report.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
report=module.report

def test_report_contains_measured_optimization_example():
    table=report(Path(__file__).parents[1])
    assert '| optimization_demo |' in table
    row=next(row for row in table.splitlines() if row.startswith('| optimization_demo |'))
    cells=[cell.strip() for cell in row.strip('|').split('|')]
    assert int(cells[1])>int(cells[2])
