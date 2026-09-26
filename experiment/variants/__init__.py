"""The calculator's variants: three languages for one task. Each declares
what it authors, how the verifier builds and runs its program, and what
the host must carry."""
from .brainfuck import Brainfuck
from .python import Python
from .zig import Zig

VARIANTS = (Python, Brainfuck, Zig)
