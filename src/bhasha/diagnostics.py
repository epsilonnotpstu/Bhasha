"""Source-aware diagnostic objects shared across compiler phases."""
from dataclasses import dataclass

@dataclass
class Diagnostic:
    message: str
    line: int
    column: int
    source: str = "<input>"
    kind: str = "error"
    def render(self, text: str = "") -> str:
        head = f"{self.source}:{self.line}:{self.column}: {self.kind}: {self.message}"
        lines = text.splitlines()
        if 0 < self.line <= len(lines):
            return head + "\n" + lines[self.line-1] + "\n" + " "*(self.column-1) + "^"
        return head
