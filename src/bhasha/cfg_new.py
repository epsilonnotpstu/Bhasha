"""Basic-block leader algorithm and CFG DOT export for label TAC."""
from dataclasses import dataclass
import re
LABEL=re.compile(r"^([A-Za-z_]\w*):$")
GOTO=re.compile(r"^(?:ifFalse .+ )?goto ([A-Za-z_]\w*)$")
@dataclass
class CFG:
 blocks:list[list[str]]; edges:list[tuple[int,int]]
 def dot(self):
  rows=["digraph CFG {","  node [shape=box fontname=monospace];"]
  for i,b in enumerate(self.blocks): rows.append(f'  B{i} [label="B{i}:\\l'+"\\l".join(b).replace('"','\\"')+'\\l"];')
  rows.extend(f"  B{a} -> B{b};" for a,b in self.edges)
  return "\n".join(rows+["}"])
def build_cfg(ir):
 if not ir:return CFG([['(empty)']],[])
 leaders={0};labels={}
 for i,line in enumerate(ir):
  m=LABEL.match(line)
  if m:leaders.add(i);labels[m.group(1)]=i
  if line.startswith('func '):leaders.add(i)
  if (GOTO.match(line) or line.startswith('return ') or line=='endfunc') and i+1<len(ir):leaders.add(i+1)
 for line in ir:
  m=GOTO.match(line)
  if m and m.group(1) in labels:leaders.add(labels[m.group(1)])
 starts=sorted(leaders);ends=starts[1:]+[len(ir)];blocks=[ir[a:b] for a,b in zip(starts,ends)];index={s:i for i,s in enumerate(starts)};edges=[]
 for i,(start,end) in enumerate(zip(starts,ends)):
  m=GOTO.match(ir[end-1])
  if m:edges.append((i,index[labels[m.group(1)]]))
  terminator=ir[end-1]
  if (not m or terminator.startswith('ifFalse')) and not terminator.startswith('return ') and terminator!='endfunc' and i+1<len(blocks) and not blocks[i+1][0].startswith('func '):edges.append((i,i+1))
 return CFG(blocks,edges)
