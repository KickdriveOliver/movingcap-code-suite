# MovingCap CODE Suite

A self-contained workspace for **developing and testing MovingCap CODE (MicroPython)
applications** on [MovingCap](https://movingcap.de) Ethernet ETH servo drives
(e.g. MovingCap turnTRACK 349 / MC349 ETH or MovingCap flatTRACK / MCFLAT ETH). 
It bundles everything an engineer — or an AI coding agent — needs to write a
servo drive application, upload it to a real servo drive, run it, and verify its behaviour.

It is designed to be dropped into any agentic coding tool (GitHub Copilot, Claude Code, and
others) and used for autonomous development and testing.

Public repository at [movingcap-code-suite](https://github.com/KickdriveOliver/movingcap-code-suite)

## About MovingCap
[MovingCap](https://movingcap.de) is a family of intelligent compact servo drives by
**Fullmo Drives GmbH** for industrial, agricultural, and special applications. The motors
combine integrated control with web-based configuration and on-drive Python programmability.
They operate from 12, 24, 48, or 72 V DC supplies (or custom supply variants) and communicate
via EtherCAT, CANopen, Ethernet TCP/IP, or digital I/O. **MovingCap CODE** is the on-drive
MicroPython engine that lets you run application logic directly on the drive. This suite
targets the **MovingCap Ethernet ETH** servo drive range:
MovingCap turnTRACK, flatTRACK, shortTRACK, FATtrack and pushTRACK.

## Audience
Application builders and MovingCap users who want a reproducible, scriptable way to develop
and validate servo drive applications.

## What's inside

```
movingcap-code-suite/
├─ app-scripts/         Servo drive-side MicroPython apps (MovingCap CODE)
│   ├─ turntrack_a_b_turntable.py     ← A/B positioning example
│   ├─ turntrack_a_b_turntable_README.md
│   ├─ turntrack_6_slot_turntable.py  ← six-slot rotary-table example
│   ├─ turntrack_6_slot_turntable_README.md
│   ├─ flattrack_demo.py              ← continuous flatTRACK/shortTRACK motion demo
│   ├─ mc_rest_api_example.py         ← HTTP/JSON REST API server example
│   ├─ mc_rest_api_example_README.md
│   ├─ mc_rest_api_simple_GET_example.py ← minimal HTTP GET object-read example
│   ├─ modbus_tcp_motion.py           ← Modbus TCP motion/object gateway example
│   ├─ modbus_tcp_motion_README.md
│   └─ *.pyi              API stubs (mcdrive/mcnet/refgo/sys/time) for editor support
├─ .github/             Agent skills, coding instructions, and custom agents
│   ├─ skills/          MovingCap CODE authoring skill + Kickdrive `.kickpro` config skill
│   ├─ instructions/    Coding rules & MicroPython subset for app-scripts/**/*.py
│   └─ agents/          Engineer & reviewer custom agent definitions
├─ testing/
│   ├─ mctk/            Host-side MovingCap Test Kit (CPython 3)
│   ├─ upload_mc_script.py  One-command upload/start utility
│   ├─ upload_mc_script_README.md  CLI reference
│   ├─ test_turntrack_a_b_turntable.py  ← A/B example functional test
│   ├─ test_turntrack_6_slot_turntable.py  ← six-slot example functional test
│   ├─ test_mc_rest_api_example.py
│   ├─ test_modbus_tcp_motion.py
│   ├─ verify_modbus_tcp_modpoll.py
│   ├─ verify_modbus_tcp_modpoll_README.md
│   ├─ TestPlan.md      Generalized functional test plan
│   └─ results/         JSON test reports land here
├─ kickdrive-projects/  Reference examples for Kickdrive .kickpro project format
│   └─ flattrack_testing_example/  Working setup, service, parameter and motion-test project
├─ AGENTS.md            Workspace guide for AI coding agents
└─ requirements.txt     Host-side deps (requests)
```


## Two kinds of Python
| | Drive-side | Host-side |
|---|---|---|
| Where | `app-scripts/` | `testing/` (`mctk`) |
| Runtime | MovingCap CODE MicroPython, on the servo drive (firmware `v5X.XX.13.00+`) | Desktop CPython 3, on your PC |
| Rules | `mcdrive`/`mcnet`/`refgo`/`time`/`sys` + compact MicroPython subset (`collections.namedtuple`, `struct`, `array`, `binascii`, `gc`, slices, `splitlines`/`partition`, `%` format). **No f-strings, no `float`/`math`**, use `time.sleep_ms`. See [`movingcap-scripts.instructions.md`](.github/instructions/movingcap-scripts.instructions.md) | Normal Python; only needs `requests` |

Do not apply servo drive-side constraints to the host tooling, or host conventions to servo drive scripts.

## Quick start
```bash
# 1. Install host dependencies (Python 3.8+)
python -m pip install -r requirements.txt

# 2. Make sure the servo drive is reachable (default IP 192.168.2.150)
ping 192.168.2.150

# 3. Run the example functional test (uploads + runs + verifies on the drive)
cd testing
python test_turntrack_a_b_turntable.py
# or: python test_turntrack_6_slot_turntable.py 192.168.2.150
```
A JSON report is written to `testing/results/`. Exit code 0 = all checks passed (CI-friendly).

> ⚠️ **Safety:** Both example tests enable the servo drive and physically move the axis.
> Ensure the turntable can rotate freely through the tested range before running either test.

To upload and start any application directly from the repository root:

```bash
python testing/upload_mc_script.py app-scripts/turntrack_6_slot_turntable.py --stop-first
```

The default drive IP is `192.168.2.150`; pass another IP positionally or with
`--device-ip`. See [`testing/upload_mc_script_README.md`](testing/upload_mc_script_README.md).

## Using the test kit (`mctk`) directly
Run this example from the `testing/` directory:

```python
from mctk import (
    RefgoClient,
    UdpMonitor,
    input_mask,
    start_script,
    stop_script,
    upload_script,
)

upload_script("192.168.2.150", "../app-scripts/turntrack_a_b_turntable.py")

monitor = UdpMonitor("192.168.2.150"); monitor.start()
start_script("192.168.2.150")

with RefgoClient("192.168.2.150") as drive:
    print("status", drive.tell_status())          # TS
    print("position", drive.tell_position())       # TP
    drive.write_object(0x6073, 0x00, 1000)         # OW: max torque 100%
    drive.pulse_inputs(input_mask(1))              # pulse virtual IN1
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
1. Read [`.github/skills/movingcap-code-python-writer/SKILL.md`](.github/skills/movingcap-code-python-writer/SKILL.md)
   and [`.github/instructions/movingcap-scripts.instructions.md`](.github/instructions/movingcap-scripts.instructions.md).
2. Choose an example that matches the application:
   - `turntrack_*.py` demonstrate first-run defaults guarded by an application magic value.
   - `flattrack_demo.py` demonstrates continuous flatTRACK/shortTRACK profile positioning and intentionally blocks while waiting for motion or fault clearance.
   - `mc_rest_api_example.py`, `mc_rest_api_simple_GET_example.py`, and `modbus_tcp_motion.py` demonstrate custom TCP/HTTP/Modbus protocol servers using `mcnet`, `collections.namedtuple`, `struct`, `%` formatting, and string partitioning/slicing.
3. Use only documented APIs (the `app-scripts/*.pyi` stubs provide editor documentation)
   and the validated MicroPython subset (no f-strings, no `float`). Follow the motion and
   error-handling pattern appropriate to the app: bounded `ChkReady`/`ChkError` waits for
   direct motion commands, or configured drive profiles and status outputs for event-driven applications.
4. Upload quickly with `testing/upload_mc_script.py`, or add a functional test under
   `testing/` modeled on the `test_*.py` examples for repeatable validation.

## Configuring the drive (Kickdrive companion skill)
Beside the MovingCap CODE authoring skill, this suite ships a companion skill,
[`.github/skills/kickdrive-project-writer/SKILL.md`](.github/skills/kickdrive-project-writer/SKILL.md), for
 [Kickdrive](https://www.kickdrive.de) `.kickpro` XML projects. Kickdrive is a Windows-only,
host-side tool for reading and writing a servo drive's CANopen object-dictionary
parameters — *configuration*, as opposed to the on-drive MicroPython *application* that
MovingCap CODE runs. Use it to build user tools for managing presets of relevant CANopen
object parameters. The working
[`flattrack_testing_example.kickpro`](kickdrive-projects/flattrack_testing_example/flattrack_testing_example.kickpro)
project demonstrates setup, service, parameter configuration, scope, and an embedded
MovingCap CODE motion demo.

## Communication interfaces (reference)
| Interface | Port | Use |
|-----------|------|-----|
| HTTP | 80 | drive app upload (`POST program.html`), start/stop (`?codeAct=3/4`) |
| REFGO (TCP) | 10001 | REFGO ASCII object read/write (`OR`/`OW`), status/position (`TS`/`TP`) |
| UDP debug | 14999 | Python `print()` console output; additional drive diagnostics |

## Related MovingCap resources
- **Product & company:** https://movingcap.de — Fullmo Drives GmbH.
- **MovingCap CODE manual:** https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html
- **API documentation** (the `.pyi` stubs in `app-scripts/` mirror these):
  [mcdrive module reference](https://movingcap.de/user/MovingCap-AnwenderDoku/2-MovingCap_ETH_Ethernet/MovingCap%20CODE%20Python/MovingCap_Import_Documentation/mcdrive_pyi.txt)
  and the other module references listed in the authoring skill.
- **Example & demo collection:** [`KickdriveOliver/movingcap`](https://github.com/KickdriveOliver/movingcap). 
  Dedicated repository for the example files (demos, applications, scripts) and docs-as-code source files (.md).

The drive-script authoring rules and the full reference URL list live in
[`.github/skills/movingcap-code-python-writer/SKILL.md`](.github/skills/movingcap-code-python-writer/SKILL.md)
and [`.github/instructions/movingcap-scripts.instructions.md`](.github/instructions/movingcap-scripts.instructions.md),
so AI agents working in this repo pick them up automatically.

## Relationship to the `movingcap` examples repo
[`KickdriveOliver/movingcap`](https://github.com/KickdriveOliver/movingcap) is the broad
collection of MovingCap examples and demos. **This** repository is a focused, installable
toolkit for *agent-driven development and testing* of MovingCap CODE applications: the agent
and skill definitions, the host-side `mctk` test kit, and worked examples. Use the examples
repo to browse drive-application ideas; use this suite to build, run, and verify your own.

## License
[MIT](LICENSE) © 2026 Fullmo Drives GmbH and Kickdrive Software Solutions e.K.

The MovingCap CODE API stub files (`app-scripts/*.pyi`) are derived from MovingCap
documentation by Fullmo Drives GmbH and are included for editor support and reference.
