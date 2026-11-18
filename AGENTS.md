# AGENTS.md — MovingCap CODE Suite

Workspace instructions for AI coding agents (GitHub Copilot, Claude Code, and others).
See [`README.md`](README.md) for the full file tree, quick-start commands, and architecture overview.

## Key resources
- **Drive-script authoring & API reference:**
  [`.github/skills/movingcap-code-python-writer/SKILL.md`](.github/skills/movingcap-code-python-writer/SKILL.md)
  and the API stubs in [`app-scripts/`](app-scripts/) (`*.pyi`, kept beside the drive scripts for editor support).
- **Coding rules & MicroPython subset (`v5X.XX.13.00+`):**
  [`.github/instructions/movingcap-scripts.instructions.md`](.github/instructions/movingcap-scripts.instructions.md).
- **Host tooling & tests:** [`testing/mctk/`](testing/mctk/) (`uploader.py`, `refgo.py`, `udp.py`, `runner.py`),
  [`testing/upload_mc_script.py`](testing/upload_mc_script.py) (see [`testing/upload_mc_script_README.md`](testing/upload_mc_script_README.md)),
  [`testing/TestPlan.md`](testing/TestPlan.md), and `testing/test_*.py`.
- **Kickdrive project authoring:** [`.github/skills/kickdrive-project-writer/SKILL.md`](.github/skills/kickdrive-project-writer/SKILL.md)
  and the [`flattrack_testing_example.kickpro`](kickdrive-projects/flattrack_testing_example/flattrack_testing_example.kickpro) blueprint.

## Two kinds of Python — do not mix the rules
1. **Drive-side MicroPython** (`app-scripts/`): runs on the drive via MovingCap CODE (firmware `v5X.XX.13.00+`).
   Use documented drive APIs (`mcdrive`, `mcnet`, `refgo`, `time`, `sys`) and the validated MicroPython subset
   (`collections.namedtuple`, `struct`/`ustruct`, `array`, `binascii`/`ubinascii`, `gc`, `%` formatting,
   `str.splitlines`/`partition`, slice syntax). **No f-strings, no `float`/`math`, no `bytearray`/`set`** — use
   integer/fixed-point math and `time.sleep_ms`. Follow [`.github/instructions/movingcap-scripts.instructions.md`](.github/instructions/movingcap-scripts.instructions.md).
2. **Host-side CPython** (`testing/`): ordinary desktop Python 3 on the PC (`requests` is the only external dependency).
   Normal Python conventions (f-strings, stdlib) apply here.

## Typical workflow
1. Read the skill + instructions. Restate the spec as concrete, testable behaviors.
2. Write/adapt the drive script in `app-scripts/` using documented APIs only.
3. Upload with `python testing/upload_mc_script.py app-scripts/<script>.py --stop-first` (default IP `192.168.2.150`),
   or use `mctk` directly from inside `testing/` for test automation.
4. Verify against UDP/REFGO output and `testing/TestPlan.md`.
5. Iterate until the spec is met. Clearly flag any physical actuation (motion/power/outputs).

## Safety
Scripts may physically move the axis, power the drive, or switch outputs. Confirm the axis can move freely
before running, and never guess units, limits, speeds, or directions — confirm from the spec, docs, or observed output.
