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
    return result, {"before":len(ir), "after":len(result), "constant_folds":folds, "simplified":len(removed), "removed":removed}
