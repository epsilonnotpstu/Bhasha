"""Conservative local TAC optimisations and CFG-based liveness elimination."""
import re
import operator
from .cfg_new import build_cfg
IDENTITY = re.compile(r"^(t\d+) = (\S+) ([+*]) (0|1)$")
CONSTANT = re.compile(r"^(t\d+) = (-?\d+(?:\.\d+)?) ([+*/%-]) (-?\d+(?:\.\d+)?)$")
ASSIGN = re.compile(r"^(t\d+) = (.+)$")
TEMP = re.compile(r"\bt\d+\b")
def _optimize_once(ir: list[str]):
    global_names={line[7:] for line in ir if line.startswith('global ')}
    # Local propagation is reset at labels/branches, which makes it safe at
    # control-flow joins without needing SSA or a global reaching-definitions pass.
    propagated=[]; values={}; copies=0
    for line in ir:
        # Named variables can resemble temporaries (e.g. t1). Any mutation
        # outside a plain assignment invalidates cached values and aliases.
        if re.match(r'^\w+ (?:\+=|-=|\*=|/=) ',line) or line.startswith('read '):
            values.clear()
        if line.endswith(':') or line.startswith(('goto ', 'ifFalse ', 'func ', 'endfunc')):
            values={}; propagated.append(line); continue
        original=ASSIGN.match(line)
        if original and original.group(1) not in global_names:
            rewritten=original.group(1)+' = '+TEMP.sub(lambda m: values.get(m.group(0), m.group(0)), original.group(2))
        elif line.startswith(('print ', 'param ', 'return ')):
            # Do not rewrite inside string literals or array syntax.
            op, _, arg=line.partition(' ')
            rewritten=op+' '+values.get(arg,arg)
        else:rewritten=line
        match=ASSIGN.match(rewritten)
        if match and match.group(1) not in global_names:
            rhs=match.group(2)
            if re.fullmatch(r"-?\d+(?:\.\d+)?|True|False", rhs): values[match.group(1)]=rhs
            elif re.fullmatch(r"t\d+", rhs) and rhs in values: values[match.group(1)]=values[rhs]
            else: values.pop(match.group(1),None)
        if rewritten != line: copies += 1
        propagated.append(rewritten)
    # Reuse pure binary expressions within one straight-line region. Any
    # non-temporary mutation or call invalidates the table conservatively.
    expression=re.compile(r'^(t\d+) = ([^\s\[\](),]+) (\+|-|\*|==|!=|<|>|<=|>=) ([^\s\[\](),]+)$')
    available={};common=0;cse=[]
    for line in propagated:
        if line.endswith(':') or line.startswith(('goto ', 'ifFalse ', 'func ', 'endfunc', 'read ', 'decl ', 'array ', 'global ')) or 'call ' in line:
            available.clear()
        match=ASSIGN.match(line)
        if match and match.group(1) not in global_names:
            dest=match.group(1)
            available={key:value for key,value in available.items() if dest not in (key[0],key[2],value)}
            binary=expression.fullmatch(line)
            if binary:
                key=(binary.group(2),binary.group(3),binary.group(4))
                if key in available:
                    line=f'{dest} = {available[key]}';common+=1
                elif dest not in (key[0],key[2]):available[key]=dest
        elif re.match(r'^\S+(?:\[.*\])? (?:=|\+=|-=|\*=|/=) ',line):available.clear()
        cse.append(line)
    result=[]; removed=[]; folds=0
    for line in cse:
        constant=CONSTANT.match(line)
        if constant:
            try:
                a_text,op,b_text=constant.group(2),constant.group(3),constant.group(4)
                a=float(a_text) if '.' in a_text else int(a_text)
                b=float(b_text) if '.' in b_text else int(b_text)
                if op in ('/','%') and type(a) is int and type(b) is int:
                    quotient=abs(a)//abs(b)
                    if (a<0)!=(b<0):quotient=-quotient
                    value=quotient if op=='/' else a-quotient*b
                else:value={'+':operator.add,'-':operator.sub,'*':operator.mul,'/':operator.truediv,'%':operator.mod}[op](a,b)
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
            # Division, remainder, calls, and array reads may trap or have side
            # effects; preserve them even when the result is unused.
            if m and m.group(1) not in global_names and m.group(1) not in live and not any(x in m.group(2) for x in ('call ', '/', '%', '[')):dce.append(line);continue
            if m:live.discard(m.group(1))
            live.update(uses);kept.append(line)
        kept_blocks.append(list(reversed(kept)))
    result=[line for block in kept_blocks for line in block]
    return result, {"before":len(ir), "after":len(result), "constant_folds":folds, "copy_propagations":copies, "common_subexpressions":common, "simplified":len(removed), "dead_code":len(dce), "removed":removed+dce}

def optimize(ir: list[str]):
    """Run local passes and liveness DCE until the listing stops changing."""
    current=ir[:]
    totals={"before":len(ir),"after":len(ir),"constant_folds":0,"copy_propagations":0,"common_subexpressions":0,"simplified":0,"dead_code":0,"removed":[]}
    while True:
        updated,stats=_optimize_once(current)
        for name in ('constant_folds','copy_propagations','common_subexpressions','simplified','dead_code'):totals[name]+=stats[name]
        totals['removed'].extend(stats['removed'])
        if updated==current:
            totals['after']=len(updated);return updated,totals
        current=updated
