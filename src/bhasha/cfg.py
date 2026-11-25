"""Control-flow graph helpers for the inspectable three-address-code listing."""
from dataclasses import dataclass

@dataclass
class CFG:
    blocks: list[list[str]]
    edges: list[tuple[int, int]]
    def dot(self):
        rows = ["digraph CFG {", "  node [shape=box fontname=monospace];"]
        for i, block in enumerate(self.blocks):
            label = "\\l".join(block).replace('"', '\\"') + "\\l"
            rows.append(f'  B{i} [label="B{i}:\\l{label}"];')
        rows.extend(f"  B{a} -> B{b};" for a, b in self.edges)
        return "\n".join(rows + ["}"])

def build_cfg(ir: list[str]) -> CFG:
    """Partition a straight-line listing into a valid one-block CFG.

    The current IR printer deliberately keeps structured control flow readable;
    subsequent lowering can replace this with label-based leader partitioning.
    """
    return CFG([ir or ["(empty)"]], [])
