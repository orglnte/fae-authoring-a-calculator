# The contract

The program reads ONE line from standard input, `<a> <op> <b>`:

- `a` and `b` are integers in 0..99, written in decimal, one space on each
  side of the operator;
- `op` is `+`, `-` or `*`;

and prints the result as a signed decimal integer followed by a newline,
exiting 0. Examples the verifier uses (among others):

| stdin       | stdout |
|-------------|--------|
| `1 + 1`     | `2`    |
| `7 - 10`    | `-3`   |
| `99 * 99`   | `9801` |
| `0 - 0`     | `0`    |

