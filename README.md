# fae-authoring-a-calculator

An example experiment built with [FAE](https://github.com/orglnte/fae):
coding agents write a calculator in Python, Zig and Brainfuck, and the
experiment counts the attempts each needs to get it right.

A bigger example: [fae-terraform-vs-pulumi](https://github.com/orglnte/fae-terraform-vs-pulumi).

## Run it

You need Python 3.11+ with `typer` and `ujson`, docker, and [FAE](https://github.com/orglnte/fae)
cloned beside this repo (`../fae`, or set `FAE_DIR`).

```sh
python3 cli.py rig init       # writes fae.toml, the machine-local config
python3 cli.py rig smoke      # one cell per language, the reference solution in place of an agent
```

```
=== SMOKE SUMMARY ===
  ok   python         GREEN at attempt 1
  ok   brainfuck      GREEN at attempt 1
  ok   zig            GREEN at attempt 1
  PIPELINE OK on every arm.
```

A scripted agent, in the same sealed container a real one gets, that fails
once and then solves it (build the agent image once: `bash ../fae/fae/agent-container/build.sh`):

```sh
TESTAGENT_PLAN=fail,green python3 cli.py cell spawn testagent python apidocs --rep 1
python3 cli.py fleet-status
```

A real agent, once its CLI is logged in (see the FAE README):

```sh
python3 cli.py cell spawn sonnet zig apidocs --rep 1
python3 cli.py results score
```

## What is where

```
experiment/
├── __init__.py              the definition: three variants, one arrangement, the verifier
├── task/
│   ├── T1.PROMPT.md         the brief every agent gets (it becomes TODO.md)
│   └── skeleton/README.md   the files every variant starts from
├── variants/
│   ├── sandbox.py           what the three have in common: a program run in a throwaway container
│   ├── python/              runs in python:3.12.3-slim
│   ├── zig/                 compiled with zig build-exe, then run
│   └── brainfuck/           runs in an interpreter image built from runtime/Dockerfile
│       └── seed/
│           ├── overlay/calc.bf                  the stub the agent starts from
│           ├── T1.brainfuck.project_layout.md   what the agent may change
│           ├── any.brainfuck.apidocs.api.md     the contract the verifier holds it to
│           └── reference/overlay/calc.bf        the known-good answer smoke uses
├── verifier/
│   ├── __init__.py          build if needed, run 8 expressions, compare
│   └── Dockerfile           the verifier's own environment
└── tests/                   this experiment's suite: python3 -m unittest discover -s experiment/tests
```

| | python | brainfuck | zig |
|---|---|---|---|
| authors | `calc.py` | `calc.bf` | `calc.zig` |
| runtime | `python:3.12.3-slim` | built from `variants/brainfuck/runtime/Dockerfile` (tritium `bfi` v1.2) | `tangowithfoxtrot/zig:0.13.0` |
| build | – | – | `zig build-exe` (a compile error is a charged fail) |
| run | `python3 calc.py` | `bfi -b32 -z calc.bf` | `./calc` |

Nothing an agent writes runs on the host: the verifier runs in its own
container, and it runs each case in a `docker run --rm --network none`
container of the variant's image, over its own copy of the artifacts. A
missing runtime image halts the cell before an attempt is spent (exit 45,
nothing charged).

Building an experiment like this one from an empty directory, step by
step: the FAE [HOWTO](https://github.com/orglnte/fae/blob/main/HOWTO.md).
