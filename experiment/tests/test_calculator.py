"""The calculator end to end: a cell prepared, run, verified and sealed with
no agent and nothing but the engine and this experiment on its path, for each
of three variants; the program under judgment runs only inside the variant's
container. Needs docker and the variants' images; skips otherwise."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _ctx import _ENGINE as ENGINE, _ROOT as ROOT

CALC = ROOT / "experiment"
def REF(tech):
    return CALC / "variants" / tech / "seed" / "reference" / "overlay"


from experiment.variants import Brainfuck, Python, Zig  # noqa: E402
from experiment.verifier import CalculatorVerifier  # noqa: E402
from fae.cell import image as _image  # noqa: E402


class TestTheDeclaredImage(unittest.TestCase):
    def test_the_calculator_verifier_declares_a_buildable_image(self):
        """No IMAGE_DIR = every calculator cell halts at preflight; the tag
        must resolve without a daemon."""
        cls = CalculatorVerifier
        self.assertTrue(cls.IMAGE_DIR and (Path(cls.IMAGE_DIR) / "Dockerfile").is_file())
        self.assertRegex(_image.tag("calculator-verifier", cls.IMAGE_DIR, cls.image_context(None)),
                         r"^fae-calculator-verifier:[0-9a-f]{12}$")

    def test_the_brainfuck_runtime_is_a_buildable_image(self):
        """The interpreter is an image the engine builds, never a file of
        the verifier's mounted into another runtime."""
        self.assertTrue((Path(Brainfuck.RUNTIME_DIR) / "Dockerfile").is_file())
        self.assertRegex(_image.tag("calculator-brainfuck-runtime", Brainfuck.RUNTIME_DIR),
                         r"^fae-calculator-brainfuck-runtime:[0-9a-f]{12}$")
        self.assertFalse((CALC / "verifier" / "bf.py").exists())


def image_present(image):
    try:
        return subprocess.run(["docker", "image", "inspect", image],
                              capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


DOCKER = image_present(Python.IMAGE)


@unittest.skipUnless(DOCKER, f"needs docker and {Python.IMAGE}")
class CalculatorCase(unittest.TestCase):
    """One cell through `python3 -m fae.cell` in a child, over a scratch root."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.ws = self.root / "workspaces"
        (self.root / "workspaces.nosync" / ".orch").mkdir(parents=True)
        self.ws.mkdir()

    def cid(self, arm):
        return f"stub_high_{arm}_apidocs_T1_r1"

    def run_cell(self, arm, overlay):
        # the root is this repo, as cli.py makes it: the verifier's container
        # mounts the root, and the definition must be under it
        env = dict(os.environ, REPO_ROOT=str(ROOT), EXPERIMENT_DIR=str(CALC),
                   WORKSPACES_DIR=str(self.ws), MODEL="stub", EFFORT="high",
                   HB_TICK="3600",
                   TRANSITIONS_LOG=str(self.root / "workspaces.nosync" / ".orch" / "transitions.log"),
                   PYTHONPATH=str(ENGINE) + os.pathsep + os.environ.get("PYTHONPATH", ""))
        return subprocess.run([sys.executable, "-m", "fae.cell", "T1", arm, "apidocs", "1",
                               "--stub", str(overlay)],
                              cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=600)

    def ledger(self, arm):
        return (self.ws / self.cid(arm) / "iterations.log").read_text()

    def metrics(self, arm):
        return json.loads((self.ws / self.cid(arm) / "metrics.json").read_text())

    def assert_green(self, arm, p):
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        self.assertIn("\tITER\tgreen\t", self.ledger(arm))
        self.assertIn("verdict=green", (self.ws / self.cid(arm) / ".sealed").read_text())
        m = self.metrics(arm)
        self.assertEqual((m["cell_id"], m["treatment"], m["cases"], m["passed"]),
                         (self.cid(arm), arm, 8, 8))
        self.assertIn("cases: 8/8", (self.ws / self.cid(arm) / "verify.log").read_text())
        # the verifier itself ran in a container of the declared image
        self.assertRegex((self.ws / self.cid(arm) / "verifier.log").read_text(),
                         rf"verifier start .* image=fae-calculator-verifier:[0-9a-f]{{12}} "
                         rf"container=fae-verify-{self.cid(arm)}")


class TestPython(CalculatorCase):
    def test_the_reference_is_green_and_seals(self):
        self.assert_green("python", self.run_cell("python", REF("python")))
        art = self.ws / self.cid("python") / "artifacts"
        self.assertTrue((art / "TODO.md").is_file())
        self.assertTrue((art / "docs" / "python.md").is_file())
        self.assertTrue(os.access(art / "calc.py", os.W_OK))
        self.assertFalse(os.access(art / "README.md", os.W_OK))
        self.assertTrue((self.ws / self.cid("python") / "arrangements" / "01-seed" / "verify.log").is_file())
        self.assertTrue((self.ws / self.cid("python") / "run" / "calc.py").is_file())
        self.assertEqual(subprocess.run(["docker", "ps", "-aq", "--filter", f"name=fae-calc-{self.cid('python')}"],
                                        capture_output=True, text=True).stdout.strip(), "")

    def test_a_broken_solution_is_a_charged_fail(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "calc.py").write_text("print(0)\n")
            p = self.run_cell("python", d)
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        self.assertIn("stage=cases", self.ledger("python"))
        self.assertEqual(self.metrics("python")["passed"], 2)     # the two cases whose answer is 0
        self.assertNotIn("\tHALT\t", self.ledger("python"))


class TestBrainfuck(CalculatorCase):
    def test_the_reference_is_green_through_the_built_runtime(self):
        self.assert_green("brainfuck", self.run_cell("brainfuck", REF("brainfuck")))
        art = self.ws / self.cid("brainfuck") / "artifacts"
        self.assertTrue((art / "calc.bf").is_file())
        self.assertFalse((art / "calc.py").exists())
        # the runtime the cases ran in: built by the preflight, tagged by content
        self.assertTrue(image_present(_image.tag("calculator-brainfuck-runtime", Brainfuck.RUNTIME_DIR)))


class TestZig(CalculatorCase):
    def test_the_compiler_image_is_the_substrate(self):
        p = self.run_cell("zig", REF("zig"))
        if image_present(Zig.IMAGE):
            self.assert_green("zig", p)
            return
        # no compiler image on this host: HALT[substrate] before any attempt
        # — exit 45, no ITER line, nothing charged
        self.assertEqual(p.returncode, 45, p.stderr[-2000:])
        self.assertIn("\tHALT\t", self.ledger("zig"))
        self.assertNotIn("\tITER\t", self.ledger("zig"))
        self.assertFalse((self.ws / self.cid("zig") / ".sealed").exists())


class TestTheExampleIsSelfContained(unittest.TestCase):
    def test_the_example_imports_only_the_stdlib_the_engine_and_itself(self):
        import ast
        foreign = set()
        for p in CALC.rglob("*.py"):
            if "tests" in p.relative_to(CALC).parts:
                continue
            for n in ast.walk(ast.parse(p.read_text())):
                names = ([a.name for a in n.names] if isinstance(n, ast.Import) else
                         [n.module] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module
                         else [])
                foreign |= {m.split(".")[0] for m in names} - set(sys.stdlib_module_names) - {"fae", "experiment"}
        self.assertEqual(foreign, set())

    def test_the_definition_declares_what_the_engine_reads(self):
        prog = ("import sys; sys.path.insert(0, %r)\nfrom fae.cell import experiment as exp\n"
                "d = exp.load(%r)\nprint(d.name, d.arms, sorted(d.matrix.items()), d.gate.arity, d.exclusive, "
                "d.variant('zig').AUTHORABLE, d.variant('zig').BUILD[:2], d.verifier_class().__name__)"
                % (str(ENGINE), str(CALC)))
        r = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(),
                         "calculator ('python', 'brainfuck', 'zig') "
                         "[('brainfuck', ['apidocs']), ('python', ['apidocs']), ('zig', ['apidocs'])] "
                         "1 None (('calc.zig',), ()) ('/zig/zig', 'build-exe') CalculatorVerifier", r.stderr)


if __name__ == "__main__":
    unittest.main()
