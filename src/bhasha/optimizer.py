"""Small, safe optimisation pass over printable TAC.

It removes only identity operations; this makes the pass demonstrable without
changing source-program semantics.
"""
import re
IDENTITY = re.compile(r"^(t\d+) = (\S+) ([+*]) (0|1)$")
CONSTANT = re.compile(r"^(t\d+) = (-?\d+(?:\.\d+)?) ([+*/%-]) (-?\d+(?:\.\d+)?)$")
def optimize(ir: list[str]):
    result=[]; removed=[]; folds=0
    for line in ir:
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
    # Backward local liveness: an unused temporary definition with no call is
    # pure, so it can be removed without observable behavioural change.
    live=set(); dce=[]; kept=[]
    assignment=re.compile(r"^(t\d+) = (.*)$")
    word=re.compile(r"\bt\d+\b")
    for line in reversed(result):
        m=assignment.match(line)
        uses=set(word.findall(m.group(2) if m else line))
        if m and m.group(1) not in live and "call " not in m.group(2):
            dce.append(line); continue
        if m: live.discard(m.group(1))
        live.update(uses); kept.append(line)
    result=list(reversed(kept))
    return result, {"before":len(ir), "after":len(result), "constant_folds":folds, "simplified":len(removed), "dead_code":len(dce), "removed":removed+dce}
