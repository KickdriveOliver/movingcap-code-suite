---
name: movingcap-code-python-writer
description: Help users write, adapt, and debug MovingCap CODE (MicroPython) scripts for MovingCap Ethernet ETH servo drives.
---

# MovingCap CODE Python Writer

## Overview
Use this skill whenever the user mentions Python, a script, an example program, or
code for a MovingCap Ethernet ETH servo drive. In this context, "Python" always
means **MovingCap CODE MicroPython** running on the drive, not generic desktop Python.

The authoritative API stubs live next to the drive scripts in [`app-scripts/`](../../../app-scripts/):
`mcdrive.pyi`, `mcnet.pyi`, `refgo.pyi`, `sys.pyi`, `time.pyi`. Keeping them beside the
scripts also lets editors (VS Code/Pylance) resolve `import mcdrive` etc. and show inline docs.
Use ONLY the modules, functions, and patterns documented there (and at the `movingcap.de` URLs below).

## Key API (from `app-scripts/mcdrive.pyi`)
- `mc.GoPosAbs(x)` / `mc.GoPosRel(x)` — move to an absolute / relative position. Use
  `mc.ChkReady()` and `mc.ChkError()` to wait for the end of the move and detect faults.
- `mc.GoHome(method, velocity, acceleration, offset)` — CiA-402 homing. `method` 35/37 =
  "don't move, set current position as new zero".
- `mc.EnableDrive()` — switch the CiA-402 state machine to "operation enabled".
- `mc.PowerQuit()` — safely disable the drive.
- `mc.SetPosVel(v)` / `mc.SetAcc(a)` / `mc.SetDec(d)` / `mc.SetTorque(t)` — profile settings.
- `state = mc.ChkIn(n)` — read digital input n; `mc.SetOut(n)` / `mc.ClearOut(n)` — set/reset output n.
- `pos = mc.GetActualPos()` — current actual position (object 6064h).
- `mc.WriteObject(index, subindex, value)` / `value = mc.ReadObject(index, subindex)` —
  generic numeric CANopen object write/read.
- `time.sleep_ms(ms)` — delay. Prefer the `time` module over the legacy `sys.wait(ms)`.

### Waiting for a move to complete
```python
def WaitMotionDone(timeoutMs):
    startTime = time.ticks_ms()
    while mc.ChkReady() == 0:
        if mc.ChkError() != 0:
            return 0
        if time.ticks_ms() - startTime > timeoutMs:
            return 0
        time.sleep_ms(1)
    return 1
```
A bounded wait like this is safer than an infinite loop: real applications must react to
errors and timeouts rather than blocking forever.

### Free user-parameter objects
For application state that should persist (config version markers, travel profiles, etc.)
use the documented free user-parameter area:
| Type | Index | Subindex | Notes |
|------|-------|----------|-------|
| unsigned8 | 340Bh | 01h–0Ah | Python unsigned8 N |
| integer8 | 340Ch | 01h–0Ah | Python integer8 N |
| unsigned16 | 340Dh | 01h–0Ah | Python unsigned16 N |
| integer16 | 340Eh | 01h–0Ah | Python integer16 N |
| unsigned32 | 340Fh | 01h–0Ah | Python unsigned32 N |
| integer32 | 3410h | 01h–0Ah | Python integer32 N |

## Source of truth and reference URLs
- MovingCap CODE manual: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html
- Simple test program: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/ein-einfaches-testprogramm.html
- Python program control: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/python-programmsteuerung.html
- Python user parameter area: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/python-user-parameter-area.html
- Examples and documentation: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/beispiele-und-dokumentation-z2.html
- Debugging / finding errors: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/debugging-_-fehler-finden.html
- mcdrive module docs: https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/mcdrive_pyi.txt
- time module docs: https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/time_pyi.txt
- refgo module docs: https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/refgo_pyi.txt
- mcnet module docs: https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/mcnet_pyi.txt
- sys module docs: https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/sys_pyi.txt
- mcdrive overview examples: https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_MicroPython_Examples/mcdriveModuleOverview_py.txt
- Example collection: https://github.com/KickdriveOliver/movingcap

## Runtime behavior
- Use documented MovingCap CODE modules and APIs only.
- For delays, prefer `time.sleep_ms(ms)` over the legacy `sys.wait(ms)`.
- If a request depends on functionality not covered by the references, say so and ask for
  the relevant excerpt or a narrower requirement.
- Ask only the minimum clarifying questions before writing code (move type, units, IO
  numbers, enable/disable sequence, homing needs, safety limits).
- Favor small, working examples matched to the drive's documented capabilities.
- Be conservative with motion and IO; do not assume speed, acceleration, current, or
  direction unless the user provides them.

## Constraints
- Do not invent APIs or use generic Python libraries unless documented for MovingCap CODE.
- Do not assume standard-library modules or desktop-Python patterns are available unless the
  MovingCap documentation explicitly shows them.
- **Do not use Python f-strings** — they are not available. Concatenate instead: `'pos=' + str(pos)`.
- Do not use commands/examples from the older "python-on-a-chip" / pymite engine; that is a
  different, outdated interpreter with a different library (not `mcdrive`).
- Do not guess function names, arguments, return values, or side effects.
- Treat all motion, IO, and parameter references as drive-side behavior.
- Warn when a request can move the axis, power the drive, or switch outputs.
