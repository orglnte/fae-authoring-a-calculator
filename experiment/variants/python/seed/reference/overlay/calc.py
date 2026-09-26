"""calc: read `<a> <op> <b>` from stdin, print the result."""
import sys

OPS = {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b}


def evaluate(line: str) -> int:
    a, op, b = line.split()
    return OPS[op](int(a), int(b))


if __name__ == "__main__":
    print(evaluate(sys.stdin.readline()))
