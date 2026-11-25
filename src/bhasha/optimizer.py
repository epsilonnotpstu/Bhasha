"""Small, safe optimisation pass over printable TAC.

It removes only identity operations; this makes the pass demonstrable without
changing source-program semantics.
"""
import re
IDENTITY = re.compile(r"^(t\d+) = (\S+) ([+*]) (0|1)$")
def optimize(ir: list[str]):
    result=[]; removed=[]
    for line in ir:
        m=IDENTITY.match(line)
        if m and ((m.group(3)=="+" and m.group(4)=="0") or (m.group(3)=="*" and m.group(4)=="1")):
            result.append(f"{m.group(1)} = {m.group(2)}"); removed.append(line)
        else: result.append(line)
    return result, {"before":len(ir), "after":len(result), "simplified":len(removed), "removed":removed}
