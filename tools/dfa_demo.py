"""Emit a small identifier/number DFA in DOT; render SVG when Graphviz exists."""
from pathlib import Path
import shutil, subprocess
DOT='''digraph DFA {
  rankdir=LR; node [shape=circle]; start [shape=point]; start -> id;
  id [label="identifier\\nletter/_"]; id -> id [label="letter/digit/_"];
  start -> integer [label="digit"]; integer [shape=doublecircle,label="integer"];
  integer -> integer [label="digit"]; integer -> dot [label="."];
  dot -> fraction [label="digit"]; fraction [shape=doublecircle,label="float"]; fraction -> fraction [label="digit"];
}'''
def main():
 out=Path('docs')/'dfa.dot';out.write_text(DOT,encoding='utf8');print(out)
 if shutil.which('dot'):
  svg=out.with_suffix('.svg');subprocess.run(['dot','-Tsvg',str(out),'-o',str(svg)],check=True);print(svg)
if __name__=='__main__':main()
