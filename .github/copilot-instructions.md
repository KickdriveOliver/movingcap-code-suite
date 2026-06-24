# MovingCap CODE Suite — Copilot Instructions

This workspace develops and tests **MovingCap CODE (MicroPython)** application scripts for
MovingCap Ethernet ETH servo drives (MC349 ETH), plus the host-side Python tooling that
uploads, runs, and diagnoses them.

## Key resources
- Drive-script authoring & API reference:
  [.github/skills/movingcap-code-python-writer/SKILL.md](skills/movingcap-code-python-writer/SKILL.md)
  and the API stubs in [app-scripts/](../app-scripts/) (`*.pyi`, kept beside the drive scripts for editor support).
- Coding rules for drive scripts:
  [.github/instructions/movingcap-scripts.instructions.md](instructions/movingcap-scripts.instructions.md).
- Host tooling: the [testing/mctk/](../testing/mctk/) package — `uploader.py`, `refgo.py`
  (REFGO `OR`/`OW`, `TS`/`TP`, virtual inputs), `udp.py`, `runner.py` — plus
  [testing/TestPlan.md](../testing/TestPlan.md) and the worked example test.
- Generated drive application scripts live in [app-scripts/](../app-scripts/).

## Two kinds of Python in this repo
1. **Drive-side MicroPython** (in `app-scripts/`): runs on the drive via MovingCap CODE.
   Subject to [movingcap-scripts.instructions.md](instructions/movingcap-scripts.instructions.md)
   — documented MovingCap APIs only, **no f-strings**, prefer `time.sleep_ms`, no desktop-Python libs.
2. **Host-side desktop Python** (the `testing/` harness and `mctk` package): normal CPython 3 that
   runs on the PC to upload scripts and drive the web/UDP/REFGO interfaces. Normal Python conventions apply.

Never apply drive-side constraints to host tooling, or host conventions (f-strings, stdlib) to drive scripts.

## Testing drive scripts
- Default drive IP is `192.168.2.150` (override when specified).
- Run tests from inside `testing/` so `import mctk` resolves.
- Verify behavior with UDP diagnostics (`UdpMonitor`), REFGO `TS`/`TP` and object reads
  (`RefgoClient`), and the criteria in `testing/TestPlan.md`.

## Safety
- Scripts may physically move the axis, power the drive, or switch outputs. Clearly flag any such
  actuation in summaries.
- Never guess units, limits, speeds, or directions — confirm from the spec, docs, or observed drive output.
