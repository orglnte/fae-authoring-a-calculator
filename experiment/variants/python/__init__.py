"""A Python program: nothing to build, run by the image's interpreter."""
from __future__ import annotations

from ..sandbox import Sandboxed


class Python(Sandboxed):
    ARM = "python"
    TECH = "python"
    CONDITIONS = ("apidocs",)
    AUTHORABLE = (("calc.py",), ())
    IMAGE = "python:3.12.3-slim"
    RUN = ("python3", "calc.py")
