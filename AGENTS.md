# AGENTS.md — MovingCap CODE Suite

Portable, tool-agnostic guidance for AI coding agents (GitHub Copilot, Claude Code, and
others) working in this suite. GitHub Copilot also reads the mirrored files under
[`.github/`](.github/).

## What this suite is
A self-contained workspace for **developing and testing MovingCap CODE (MicroPython)**
applications on MovingCap Ethernet ETH servo drives (MC349 ETH), with host-side Python
tooling to upload, run, and diagnose them.

## Map of the suite
| Path | Purpose |
|------|---------|
| `app-scripts/` | Drive-side MicroPython application scripts (e.g. `driveTurntablePositioning.py`). |
| `app-scripts/*.pyi` | Authoritative MovingCap CODE API stubs (`mcdrive/mcnet/refgo/sys/time.pyi`), kept beside the drive scripts so editors (VS Code/Pylance) resolve imports and show inline docs. |
| `skills/movingcap-code-python-writer/SKILL.md` | How to write MovingCap CODE; key APIs and rules. |
| `instructions/movingcap-scripts.instructions.md` | Hard coding rules for `app-scripts/**/*.py`. |
| `agents/` | Engineer and reviewer agent definitions (portable). |
| `testing/mctk/` | Host-side test kit: upload/run, REFGO `OR`/`OW`, UDP monitor, test runner. |
| `testing/test_turntable_positioning.py` | Worked functional test for the example app. |
| `testing/TestPlan.md` | Generalized functional test plan. |

## Two kinds of Python — do not mix the rules
1. **Drive-side MicroPython** (`app-scripts/`): documented MovingCap APIs only, **no f-strings**,
   prefer `time.sleep_ms`, bounded `ChkReady`/`ChkError` waits, clean `EnableDrive`/`PowerQuit`.
2. **Host-side CPython** (`testing/`): ordinary desktop Python 3; f-strings and the standard
   library are fine. Only dependency is `requests` (see `requirements.txt`).

## Typical workflow
1. Read the skill + instructions. Restate the spec as concrete, testable behaviors.
2. Write/adapt the drive script in `app-scripts/` using documented APIs only.
3. From `testing/`, upload + run with `mctk` and verify against UDP/REFGO output and the TestPlan.
4. Iterate until the spec is met. Flag any physical actuation (motion/power/outputs).

## Safety
The drive can physically move. Confirm the axis can move freely before running, and never
guess units, limits, speeds, or directions — confirm from the spec, docs, or observed output.
