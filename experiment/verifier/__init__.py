"""The calculator's verifier: build the variant's program if it declares a
build, then run it over a fixed table of expressions; green iff every answer
matches.

`CalculatorVerifier.verify(ctx)` is what the engine calls
(fae/cell/verify.py), inside a container of the image IMAGE_DIR declares;
it judges the solution only through its public interface — stdin in,
stdout out, one container run per case — and answers a Verdict. The
variant declares IMAGE, BUILD (an argv, or None) and RUN (the argv
prefix); build and cases run inside `docker run --rm` (the engine's
substrate/sandbox block) over the verifier's own copy of the artifacts
(`<out>/run/`), with no network. Nothing the agent wrote executes on the
host.
"""
from __future__ import annotations

import time
from pathlib import Path

from fae.cell import experiment as _experiment
from fae.cell.substrate import sandbox
from fae.cell.verify import Verdict, Verifier

CASES = (
    ("1 + 1", "2"),
    ("7 - 10", "-3"),
    ("6 * 7", "42"),
    ("12 + 30", "42"),
    ("99 * 99", "9801"),
    ("0 - 0", "0"),
    ("50 - 8", "42"),
    ("3 * 0", "0"),
)

TIMEOUT_S = 20
BUILD_TIMEOUT_S = 180


def run_case(variant, cid, workdir, expr):
    """(answer, error) from one invocation with the expression on stdin."""
    out, err, rc, error = variant.run(cid, workdir, variant.RUN, expr + "\n", TIMEOUT_S)
    if error:
        return None, error
    if rc != 0:
        return None, f"exit {rc}: {err.strip()[-200:]}"
    return out.strip(), None


class CalculatorVerifier(Verifier):
    IMAGE_DIR = Path(__file__).parent
    FILES = ("verify.log",)

    def verify(self, ctx):
        t0 = time.time()
        artifacts, out = Path(ctx.artifacts), Path(ctx.out)
        variant = _experiment.current().variant(ctx.variant)
        log = out / "verify.log"
    
        def done(ok, stage, why, passed=0):
            return Verdict(ok=ok, stage=stage, why=why,
                           metrics={"cases": len(CASES), "passed": passed},
                           seconds=time.time() - t0)

        with log.open("w") as f:
            if variant is None:
                f.write(f"FAIL[deploy]: no variant named {ctx.variant!r}\n")
                return done(False, "deploy", f"no variant {ctx.variant!r}")
            program = variant.AUTHORABLE[0][0]
            if not (artifacts / program).is_file():
                f.write(f"FAIL[deploy]: no {program} in the workspace\n")
                return done(False, "deploy", f"no {program}")
            workdir = sandbox.fresh_copy(artifacts, out)
            if variant.BUILD:
                _o, err, rc, error = variant.run(ctx.cid, workdir, variant.BUILD, "", BUILD_TIMEOUT_S)
                f.write(f"build: {' '.join(variant.BUILD)} -> exit {rc}\n{err}")
                if error or rc != 0:
                    # the image (compiler) was there; the program was rejected: charged
                    return done(False, "deploy", f"build failed: {error or err.strip()[-200:]}")
            passed, first_why = 0, ""
            for expr, want in CASES:
                got, err = run_case(variant, ctx.cid, workdir, expr)
                ok = err is None and got == want
                passed += ok
                f.write(f"{'ok  ' if ok else 'FAIL'} {expr!r} -> {got!r}"
                        f"{'' if ok else f' (want {want!r}{'; ' + err if err else ''})'}\n")
                if not ok and not first_why:
                    first_why = f"{expr} -> {got if err is None else err}, want {want}"
            f.write(f"cases: {passed}/{len(CASES)}\n")
        green = passed == len(CASES)
        return done(green, "" if green else "cases", first_why, passed)
