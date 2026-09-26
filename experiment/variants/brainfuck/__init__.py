"""A brainfuck program, run by tritium `bfi` (rdebath/Brainfuck v1.2) in the
runtime image `runtime/Dockerfile` builds: 32-bit cells, 0 at end of input."""
from __future__ import annotations

from pathlib import Path

from ..sandbox import Sandboxed


class Brainfuck(Sandboxed):
    ARM = "brainfuck"
    TECH = "brainfuck"
    CONDITIONS = ("apidocs",)
    AUTHORABLE = (("calc.bf",), ())
    RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
    RUN = ("bfi", "-b32", "-z", "calc.bf")
