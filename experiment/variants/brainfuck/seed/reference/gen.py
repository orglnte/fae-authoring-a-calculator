"""Generate overlay/calc.bf, the brainfuck reference: reads `<a> <op> <b>` from
stdin, prints the signed decimal result. Cells are 32-bit integers (the
verifier runs tritium bfi -b32); nothing here may drive a cell below zero
and then copy it, since a copy loop of a wrapped cell never ends."""
from pathlib import Path

out = []
pos = 0

def at(c):
    global pos
    out.append(">" * (c - pos) if c > pos else "<" * (pos - c)); pos = c
def emit(s): out.append(s)
def clear(c): at(c); emit("[-]")
def inc(c, n): at(c); emit("+" * n if n >= 0 else "-" * (-n))
def move(src, dst):
    at(src); emit("["); at(dst); emit("+"); at(src); emit("-]")
def sub_into(src, dst):        # dst -= src; src = 0
    at(src); emit("["); at(dst); emit("-"); at(src); emit("-]")
def copy(src, dst, tmp):
    clear(tmp); at(src); emit("["); at(dst); emit("+"); at(tmp); emit("+"); at(src); emit("-]"); move(tmp, src)
def begin(c): at(c); emit("[")
def end(c): at(c); emit("]")
def if_zero_flag(c, flag, tmp1, tmp2):
    """flag = (c == 0), c preserved."""
    clear(flag); inc(flag, 1); copy(c, tmp1, tmp2); begin(tmp1); clear(flag); clear(tmp1); end(tmp1)

A, C, F, T, U = 0, 1, 2, 3, 4
O = 5
B, BC, BFl, BT, BU = 6, 7, 8, 9, 10
R, S, X, Y, Z, W, V = 11, 12, 13, 14, 15, 16, 17
M, P, Q = 18, 19, 20
D3, D2, D1, D0, QQ, CNT, REM, ST, TT = 21, 22, 23, 24, 25, 26, 27, 28, 29

def read_number(N, Cc, Fc, Ta, term):
    """N = the digits read until the byte `term` (consumed)."""
    clear(N); clear(Fc); inc(Fc, 1)
    begin(Fc)
    clear(Fc)
    at(Cc); emit(","); inc(Cc, -term)
    begin(Cc)
    inc(Cc, term - 48)
    move(N, Ta)
    begin(Ta); inc(N, 10); at(Ta); emit("-]")
    move(Cc, N)
    inc(Fc, 1)
    end(Cc)
    end(Fc)

read_number(A, C, F, T, 32)
at(O); emit(",")
at(C); emit(","); clear(C)
read_number(B, BC, BFl, BT, 10)
clear(R); clear(S)

# dispatch on O - 42 in {0 '*', 1 '+', 3 '-'}: a cascade that never drives a
# cell negative (a copy of a negative cell would loop forever)
inc(O, -42)
clear(M); inc(M, 1); clear(P); clear(Q)
begin(O)                                       # O >= 1: not '*'
clear(M); inc(P, 1); inc(O, -1)                # O now 0 ('+') or 2 ('-')
begin(O)
clear(P); inc(Q, 1); clear(O)
end(O)
end(O)

begin(M)
copy(A, X, W)
begin(X); copy(B, R, W); inc(X, -1); end(X)
clear(M)
end(M)

begin(P)
copy(A, R, W); copy(B, R, W)
clear(P)
end(P)

begin(Q)
copy(A, X, W); copy(B, Y, W)
begin(X)
if_zero_flag(Y, V, Z, W)                       # V = (Y == 0)
clear(W); inc(W, 1); begin(V); clear(W); move(X, R); clear(V); end(V)   # Y zero: R = X, stop
begin(W); inc(X, -1); inc(Y, -1); clear(W); end(W)                        # Y nonzero: both down
end(X)
begin(Y); move(Y, R); inc(S, 1); end(Y)
clear(Q)
end(Q)

# print: sign
begin(S); clear(V); inc(V, 45); at(V); emit("."); clear(V); clear(S); end(S)

def div(n, q, rem):
    """q, rem = divmod(R, n); R consumed."""
    clear(q); clear(CNT); inc(CNT, n)
    begin(R)
    inc(R, -1); inc(CNT, -1)
    if_zero_flag(CNT, W, Z, V)
    begin(W); inc(q, 1); clear(CNT); inc(CNT, n); clear(W); end(W)
    end(R)
    clear(rem); inc(rem, n); sub_into(CNT, rem)

div(1000, D3, REM); move(REM, R)
div(100, D2, REM); move(REM, R)
div(10, D1, REM); move(REM, D0)

clear(ST)
for d in (D3, D2, D1):
    clear(TT); copy(d, TT, W); copy(ST, TT, W)   # TT = d + started
    begin(TT); clear(ST); inc(ST, 1); inc(d, 48); at(d); emit("."); clear(TT); end(TT)
inc(D0, 48); at(D0); emit(".")
clear(TT); inc(TT, 10); at(TT); emit(".")

code = "".join(out)
# wrap at 72 columns for the file
lines = [code[i:i + 72] for i in range(0, len(code), 72)]
header = ("calc bf: reads one line (a op b) from stdin where a and b are integers 0 to 99 and op is\n"
          "plus or minus or star; prints the signed decimal result and a newline\n"
          "cells are 32 bit integers (the verifier runs tritium bfi)\n"
          "generated program follows; a comment may use no brainfuck character\n\n")
(Path(__file__).resolve().parent / "overlay" / "calc.bf").write_text(header + "\n".join(lines) + "\n")
print(len(code), "ops")
