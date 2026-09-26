"""What every calculator variant is: a program the verifier builds and runs
inside a throwaway container of the variant's runtime image (the engine's
substrate/sandbox block). The runtime is either a pinned registry tag
(IMAGE, pulled by the operator) or a Dockerfile directory the engine builds
and tags by content (RUNTIME_DIR). Nothing the agent wrote runs on the
host; the container has no network and sees one directory, the verifier's
copy of the artifacts."""
from __future__ import annotations

import subprocess

from fae.cell import experiment as _experiment
from fae.cell import image as _image
from fae.cell.substrate import sandbox
from fae.cell.variants.base import Variant, daemon_answers

PREFIX = "fae-calc-"


class Sandboxed(Variant):
    IMAGE = ""          # a pinned registry tag the program runs in, or
    RUNTIME_DIR = None  # the Dockerfile directory the engine builds it from
    BUILD = None        # argv inside the container, or None
    RUN = ()            # argv inside the container; the expression on stdin
    SUBSTRATE_PREFIXES = {"container": PREFIX}

    @classmethod
    def container_name(cls, cid):
        return f"{PREFIX}{cid}"

    @classmethod
    def substrate_identities(cls, cid):
        return [("container", cls.container_name(cid))]

    @classmethod
    def runtime_name(cls):
        return f"{_experiment.current().name}-{cls.TECH}-runtime"

    @classmethod
    def runtime_image(cls):
        """The tag the program runs in. A built runtime's tag is its content
        hash, so it resolves without a daemon."""
        if cls.RUNTIME_DIR:
            return _image.tag(cls.runtime_name(), cls.RUNTIME_DIR)
        return cls.IMAGE

    @classmethod
    def run(cls, cid, workdir, program, stdin, timeout_s):
        """(stdout, stderr, rc, error) of `program` in this variant's runtime."""
        return sandbox.run(cls.runtime_image(), cls.container_name(cid), workdir, program,
                           stdin=stdin, timeout_s=timeout_s)

    def substrate_alive(self):
        return daemon_answers(["docker", "version"])

    def substrate_ok(self):
        if subprocess.run(["docker", "info"], capture_output=True).returncode:
            self.log("HALT[substrate]: docker unreachable")
            return False
        if self.RUNTIME_DIR:
            try:
                _image.ensure(self.runtime_name(), self.RUNTIME_DIR, log=self.log)
            except RuntimeError as e:
                self.log(f"HALT[substrate]: {e}")
                return False
        elif subprocess.run(["docker", "image", "inspect", self.IMAGE],
                            capture_output=True).returncode:
            self.log(f"HALT[substrate]: image {self.IMAGE} not present "
                     f"(docker pull {self.IMAGE})")
            return False
        return True
