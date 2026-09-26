"""The calculator — the smallest experiment the engine runs, in three
languages.

One task (evaluate `<a> <op> <b>` read from stdin), three variants (python,
brainfuck, zig), one arrangement, no lock; the only substrate is a docker
daemon, so a cell runs end to end on a laptop — and the three cells'
attempts-to-green on the same task are the results table in miniature.
"""
from __future__ import annotations

from fae.cell.experiment import Gate

NAME = "calculator"


def variant_classes():
    from .variants import VARIANTS
    return VARIANTS


SEED_DOCS = {(arm, "apidocs"): (f"any.{arm}.apidocs.api.md", 10)
             for arm in ("python", "brainfuck", "zig")}

GATE = Gate()

def verifier_class():
    from .verifier import CalculatorVerifier
    return CalculatorVerifier
