from dataclasses import dataclass, field


@dataclass
class Branch:
    source: str
    target: str
    gain: float
    label: str


@dataclass
class SFGInput:
    nodes: list = field(default_factory=list)      # ["R", "X1", "C"]
    branches: list = field(default_factory=list)   # list of Branch
    input_node: str = ""
    output_node: str = ""

    def branch_dicts(self):
        """Same format as tests/fixtures/sfg_case_*.json (Student 3 & 4 read it)."""
        return [{"from": b.source, "to": b.target, "gain": b.gain, "label": b.label}
                for b in self.branches]
