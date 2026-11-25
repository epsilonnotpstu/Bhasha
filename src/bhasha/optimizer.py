"""Small, safe optimisation pass over printable TAC.

It removes only identity operations; this makes the pass demonstrable without
changing source-program semantics.
"""
import re
from .cfg_new import build_cfg
IDENTITY = re.compile(r"^(t\d+) = (\S+) ([+*]) (0|1)$")
CONSTANT = re.compile(r"^(t\d+) = (-?\d+(?:\.\d+)?) ([+*/%-]) (-?\d+(?:\.\d+)?)$")
ASSIGN = re.compile(r"^(t\d+) = (.+)$")
TEMP = re.compile(r"\bt\d+\b")
def optimize(ir: list[str]):
    # Local propagation is reset at labels/branches, which makes it safe at
    # control-flow joins without needing SSA or a global reaching-definitions pass.
    propagated=[]; values={}; copies=0
    for line in ir:
        if line.endswith(':') or line.startswith(('goto ', 'ifFalse ', 'func ', 'endfunc')):
            values={}; propagated.append(line); continue
        rewritten=TEMP.sub(lambda m: values.get(m.group(0), m.group(0)), line)
        match=ASSIGN.match(rewritten)
        if match:
            rhs=match.group(2)
            if re.fullmatch(r"-?\d+(?:\.\d+)?|True|False", rhs): values[match.group(1)]=rhs
            elif re.fullmatch(r"t\d+", rhs): values[match.group(1)]=values.get(rhs,rhs)
            else: values.pop(match.group(1),None)
        if rewritten != line: copies += 1
        propagated.append(rewritten)
    result=[]; removed=[]; folds=0
    for line in propagated:
        constant=CONSTANT.match(line)
        if constant:
            try:
                value=eval(f"{constant.group(2)} {constant.group(3)} {constant.group(4)}", {"__builtins__": {}}, {})
                result.append(f"{constant.group(1)} = {value}"); folds += 1; continue
            except (ArithmeticError, SyntaxError): pass
        m=IDENTITY.match(line)
        if m and ((m.group(3)=="+" and m.group(4)=="0") or (m.group(3)=="*" and m.group(4)=="1")):
            result.append(f"{m.group(1)} = {m.group(2)}"); removed.append(line)
        else: result.append(line)
    # Backward liveness fixed point over CFG blocks. Equations:
    # OUT[B] = union(IN[S]) and IN[B] = USE[B] union (OUT[B] - DEF[B]).
    # An unused temporary definition whose RHS has no call is observationally pure.
    cfg=build_cfg(result); block_defs=[]; block_uses=[]
    assignment=re.compile(r"^(t\d+) = (.*)$")
    word=re.compile(r"\bt\d+\b")
    for block in cfg.blocks:
        defs=set(); uses=set()
        for line in block:
            m=assignment.match(line); line_uses=set(word.findall(m.group(2) if m else line))
            uses.update(line_uses-defs)
            if m:defs.add(m.group(1))
        block_defs.append(defs);block_uses.append(uses)
    successors={i:set() for i in range(len(cfg.blocks))}
    for a,b in cfg.edges:successors[a].add(b)
    live_in=[set() for _ in cfg.blocks];live_out=[set() for _ in cfg.blocks]
    changed=True
    while changed:
        changed=False
        for i in range(len(cfg.blocks)-1,-1,-1):
            out=set().union(*(live_in[s] for s in successors[i])) if successors[i] else set()
            incoming=block_uses[i] | (out-block_defs[i])
            if out!=live_out[i] or incoming!=live_in[i]:live_out[i]=out;live_in[i]=incoming;changed=True
    dce=[]; kept_blocks=[]
    for i,block in enumerate(cfg.blocks):
        live=set(live_out[i]);kept=[]
        for line in reversed(block):
            m=assignment.match(line); uses=set(word.findall(m.group(2) if m else line))
            if m and m.group(1) not in live and "call " not in m.group(2):dce.append(line);continue
            if m:live.discard(m.group(1))
            live.update(uses);kept.append(line)
        kept_blocks.append(list(reversed(kept)))
    result=[line for block in kept_blocks for line in block]
    return result, {"before":len(ir), "after":len(result), "constant_folds":folds, "copy_propagations":copies, "simplified":len(removed), "dead_code":len(dce), "removed":removed+dce}
