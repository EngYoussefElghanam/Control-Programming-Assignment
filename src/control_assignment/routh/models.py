from dataclasses import dataclass


@dataclass
class RouthInput:
    coefficients: list   # highest power first: s^3 + 2s^2 + 3s + 4 -> [1, 2, 3, 4]
