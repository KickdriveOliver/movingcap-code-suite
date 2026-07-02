# MovingCap CODE Suite

A self-contained workspace for **developing and testing MovingCap CODE (MicroPython)
applications** on [MovingCap](https://movingcap.de) Ethernet ETH servo drives
(MC349 ETH). It bundles everything an engineer — or an AI coding agent — needs to write a
servo drive application, upload it to a real servo drive, run it, and verify its behaviour.

It is designed to be dropped into any agentic coding tool (GitHub Copilot, Claude Code, and
others) and used for autonomous development and testing.

## About MovingCap
[MovingCap](https://movingcap.de) is a family of intelligent compact servo drives by
**Fullmo Drives GmbH** — motors with integrated control and Web & Python programmability for
industrial, agricultural, and special applications (12/24/48/72 V DC or custom supply),
communicating via EtherCAT, CANopen, Ethernet TCP/IP, or digital I/O. **MovingCap CODE** is
the on-drive MicroPython environment that lets you run application logic directly on the
drive. This suite targets the **MovingCap Ethernet ETH** servo drives range: 
MovingCap turnTRACK, flatTRACK, shortTRACK, FATtrack and pushTRACK.

## What's inside
```
movingcap-code-suite/
├─ app-scripts/         Servo drive-side MicroPython apps (MovingCap CODE)
│   ├─ driveTurntablePositioning.py   ← worked example
│   └─ *.pyi              API stubs (mcdrive/mcnet/refgo/sys/time) for editor support
├─ skills/              "How to write MovingCap CODE" skill
├─ instructions/        Coding rules for app-scripts/**/*.py
├─ agents/              Engineer & reviewer agent definitions (portable)
├─ .github/             Copilot-native mirror of the agents/skills/instructions
├─ testing/
│   ├─ mctk/            Host-side MovingCap Test Kit (CPython 3)
│   ├─ test_turntable_positioning.py  ← functional test for the example
│   ├─ TestPlan.md      Generalized functional test plan
│   └─ results/         JSON test reports land here
├─ AGENTS.md            Tool-agnostic agent guide
└─ requirements.txt     Host-side deps (requests)
```

## Audience
Clients and users of MovingCap servo drive products who want a reproducible, scriptable way to build and validate MovingCap servo drive applications.

## Two kinds of Python
| | Drive-side | Host-side |
|---|---|---|
| Where | `app-scripts/` | `testing/` (`mctk`) |
| Runtime | MovingCap CODE MicroPython, on the servo drive | Desktop CPython 3, on your PC |
| Rules | Documented APIs only, **no f-strings**, `time.sleep_ms` | Normal Python; only needs `requests` |

Do not apply servo drive-side constraints to the host tooling, or host conventions to servo drive scripts.

## Quick start
```bash
# 1. Install host dependencies (Python 3.8+)
python -m pip install -r requirements.txt

# 2. Make sure the servo drive is reachable (default IP 192.168.2.150)
ping 192.168.2.150

# 3. Run the example functional test (uploads + runs + verifies on the drive)
cd testing
python test_turntable_positioning.py            # or: python test_turntable_positioning.py 192.168.2.150
```
A JSON report is written to `testing/results/`. Exit code 0 = all checks passed (CI-friendly).

> ⚠️ **Safety:** the example test ENABLES the servo drive and PHYSICALLY MOVES the axis between 0° and 180°. 
> Ensure the turntable can rotate freely before running.

## Using the test kit (`mctk`) directly
```python
from mctk import RefgoClient, UdpMonitor, upload_script, start_script, stop_script

upload_script("192.168.2.150", "../app-scripts/driveTurntablePositioning.py")

monitor = UdpMonitor("192.168.2.150"); monitor.start()
start_script("192.168.2.150")

with RefgoClient("192.168.2.150") as drive:
    print("status", drive.tell_status())          # TS
    print("position", drive.tell_position())       # TP
    drive.write_object(0x6073, 0x00, 1000)         # OW: max torque 100%
    drive.simulate_inputs(0x10000)                 # virtual IN1 high
    print("actual pos", drive.actual_position())   # OR 6064h.00h

stop_script("192.168.2.150")
monitor.stop()
```

### `mctk` modules
- **`uploader`** — `upload_script`, `start_script`, `stop_script` (HTTP `program.html`).
- **`refgo`** — `RefgoClient` with `read_object`/`write_object` (`OR`/`OW`), `tell_status`/
  `tell_position` (`TS`/`TP`), `actual_position`, `simulate_inputs`/`clear_inputs`, plus
  `input_mask(...)` and `parse_int(...)` helpers.
- **`udp`** — `UdpMonitor` (threaded background collector) and a one-shot `listen()`.
- **`runner`** — `TestRunner` with `check`/`section`/`summary` and JSON report output.

## Writing your own drive app
1. Read [`skills/movingcap-code-python-writer/SKILL.md`](skills/movingcap-code-python-writer/SKILL.md)
   and [`instructions/movingcap-scripts.instructions.md`](instructions/movingcap-scripts.instructions.md).
2. Copy `app-scripts/driveTurntablePositioning.py` as a starting point.
3. Use only documented APIs (the `app-scripts/*.pyi` stubs give you editor docs); no
   f-strings; bounded `ChkReady`/`ChkError` waits; clean `EnableDrive`/`PowerQuit`.
4. Add a functional test under `testing/` modeled on `test_turntable_positioning.py`.

## Communication interfaces (reference)
| Interface | Port | Use |
|-----------|------|-----|
| HTTP | 80 | Upload (`POST program.html`), start/stop (`?codeAct=3/4`) |
| REFGO (TCP) | 10001 | ASCII object read/write (`OR`/`OW`), status/position (`TS`/`TP`) |
| UDP debug | 14999 | Script `print()` output and drive diagnostics |

## Related MovingCap resources
- **Product & company:** https://movingcap.de — Fullmo Drives GmbH.
- **MovingCap CODE manual:** https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html
- **API documentation** (the `.pyi` stubs in `app-scripts/` mirror these):
  https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/
- **Example & demo collection:** https://github.com/KickdriveOliver/movingcap — a broad
  collection of MovingCap examples, demos, applications, and scripts.

The drive-script authoring rules and the full reference URL list also live in
[`skills/movingcap-code-python-writer/SKILL.md`](skills/movingcap-code-python-writer/SKILL.md),
so AI agents working in this repo pick them up automatically.

## Relationship to the `movingcap` examples repo
[`KickdriveOliver/movingcap`](https://github.com/KickdriveOliver/movingcap) is the broad
collection of MovingCap examples and demos. **This** repository is a focused, installable
toolkit for *agent-driven development and testing* of MovingCap CODE applications: the agent
and skill definitions, the host-side `mctk` test kit, and a worked example. Use the examples
repo to browse drive-application ideas; use this suite to build, run, and verify your own.

## License
[MIT](LICENSE) © 2026 Fullmo Drives GmbH and Kickdrive Software Solutions e.K.

The MovingCap CODE API stub files (`app-scripts/*.pyi`) are derived from MovingCap
documentation by Fullmo Drives GmbH and are included for editor support and reference.

