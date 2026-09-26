"""A Zig program: compiled once per verify inside the compiler's image (a
compile error is a charged deploy failure); the image absent, the cell halts
before spending an attempt."""
from __future__ import annotations

from ..sandbox import Sandboxed


class Zig(Sandboxed):
    ARM = "zig"
    TECH = "zig"
    CONDITIONS = ("apidocs",)
    AUTHORABLE = (("calc.zig",), ())
    IMAGE = "tangowithfoxtrot/zig:0.13.0"
    BUILD = ("/zig/zig", "build-exe", "calc.zig", "-femit-bin=calc", "-OReleaseSafe")   # scratch image: zig is not on PATH
    RUN = ("./calc",)
