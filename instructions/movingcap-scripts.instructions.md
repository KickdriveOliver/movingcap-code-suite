---
applyTo: "app-scripts/**/*.py"
description: "MovingCap CODE (MicroPython) coding rules for drive application scripts in app-scripts/."
---
# MovingCap CODE (MicroPython) Script Rules

Files in `app-scripts/` are **MovingCap CODE MicroPython** scripts that run on a MovingCap
Ethernet ETH servo drive — not desktop Python. Always treat "Python" here as drive-side
MicroPython. (Host-side tooling in `testing/` is ordinary CPython and is NOT covered by
these rules.)

## Allowed APIs only
- Use ONLY modules, functions, and patterns documented in
  [`skills/movingcap-code-python-writer/SKILL.md`](../skills/movingcap-code-python-writer/SKILL.md)
  and the `app-scripts/*.pyi` stubs and `movingcap.de` docs.
- Do NOT invent function names, arguments, return values, or side effects.
- Do NOT assume desktop-Python or standard-library modules are available unless the
  MovingCap docs explicitly show them.

## Syntax & style constraints
- Do NOT use f-strings — they are unavailable. Build strings with concatenation:
  `'pos=' + str(pos)`.
- Prefer `time.sleep_ms(ms)` over the legacy `sys.wait(ms)`.
- Keep scripts small, conservative, and matched to the drive's documented capabilities.

## Motion & IO safety
- Wait for motion completion with `mc.ChkReady()` and check `mc.ChkError()` before continuing.
  Prefer a bounded wait (timeout) over an infinite loop so faults are handled.
- Use a clean enable/disable sequence (`mc.EnableDrive()` … `mc.PowerQuit()`).
- Do not assume speed, acceleration, current, or direction settings unless the spec gives them.
- Add a comment whenever a line can move the axis, power the drive, or switch an output.

## Common references
- `mc.GoPosAbs(x)` / `mc.GoPosRel(x)` — absolute / relative move.
- `mc.GoHome(method, vel, acc, offset)` — homing; method 35/37 sets current pos as zero.
- `mc.ChkIn(x)` — read digital input x; `mc.SetOut(x)` / `mc.ClearOut(x)` — set/reset output x.
- `mc.GetActualPos()` — current position; `mc.ReadObject(i, s)` / `mc.WriteObject(i, s, v)` —
  numeric CANopen objects. Free user objects live at 340Bh–3410h (sub 01h–0Ah).
