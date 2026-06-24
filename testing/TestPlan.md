# MovingCap CODE Suite — Functional Test Plan

## 1. Purpose
This plan describes how to functionally validate a MovingCap CODE (MicroPython) application
on a MovingCap Ethernet ETH drive using the host-side `mctk` test kit. It is intentionally
generic: the worked example targets `app-scripts/driveTurntablePositioning.py`, but the same
structure applies to any drive application.

## 2. Test environment
- **Device under test:** MovingCap ETH (MC349 ETH)
- **Default IP:** `192.168.2.150` (override via the test's command-line argument)
- **Host:** PC with Python 3.8+ and `requests` installed (`pip install -r requirements.txt`)
- **Interfaces:**
  | Interface | Port | Use |
  |-----------|------|-----|
  | HTTP | 80 | upload + start/stop script |
  | REFGO (TCP) | 10001 | object read/write (`OR`/`OW`), `TS`/`TP` |
  | UDP debug | 14999 | script `print()` output |

## 3. Preconditions
- Drive powered, on the network, and reachable (`ping`).
- Host firewall allows outbound TCP 80/10001 and inbound UDP 14999.
- For motion tests: the axis can move freely through the commanded range.

## 4. General method
1. Stop any running script; clear input simulation and (if used) the app's config-magic object.
2. Upload the target script (`mctk.upload_script`).
3. Start UDP monitoring (`mctk.UdpMonitor`) and start the script (`mctk.start_script`).
4. Drive inputs / parameters via REFGO (`mctk.RefgoClient`) — e.g. `simulate_inputs(...)`.
5. Assert behaviour from UDP lines and object reads (`actual_position`, `tell_status`).
6. Record results with `mctk.TestRunner` (JSON report in `testing/results/`).

## 5. Worked example: `test_turntable_positioning.py`
Run: `cd testing && python test_turntable_positioning.py [DEVICE_IP]`

> ⚠️ Enables the drive and physically moves the axis between 0° and 180°.

| Case | Objective | Stimulus | Expected result |
|------|-----------|----------|-----------------|
| TC-01 | Startup + first-run parameter init | clear `3410h.01h`, upload, start | UDP shows "started", "First run: writing default parameters", "magic set", "Ready at pos="; REFGO read of `3410h.01h` == app magic |
| TC-02 | Move to POS_B via IN1 | `simulate_inputs(IN1)` then release | UDP "POS_B OK"; actual position ≈ 180° (`6064h`) within tolerance |
| TC-03 | Move back to POS_A via IN1 | next `simulate_inputs(IN1)` then release | UDP "POS_A OK"; actual position ≈ 0° within tolerance |
| TC-04 | Restart skips parameter init | stop + start (no re-upload) | UDP shows "skipping parameter init" (magic already set) |

**Pass/fail:** every `TestRunner.check` must pass; the runner exits 0 only when all checks pass.

## 6. Protocol-level checks (no application script required)
These validate the drive's base interfaces and can be run standalone with `mctk`:
- **Network:** `ping` the drive.
- **REFGO:** `RefgoClient.tell_status()` / `tell_position()` return integers.
- **Object access:** `read_object` / `write_object` round-trip on a free user object
  (e.g. `3410h.01h`).
- **UDP:** `mctk.listen(ip, duration=…)` receives diagnostic lines after the registration ping.
- **Upload/run:** `upload_script` returns True; `start_script` / `stop_script` return True.

## 7. Results & CI
- Each run writes a timestamped JSON report to `testing/results/`.
- Exit code 0 = success, 1 = failure (CI-friendly).

## 8. Risks & mitigations
- *Motor not connected / blocked axis:* motion cases may fault — inspect UDP "ERROR"/"TIMEOUT"
  lines; protocol-level checks still pass.
- *UDP port already bound:* close other listeners on 14999, or rely on REFGO assertions.
- *Stale REFGO socket data:* `RefgoClient` drains the socket before each command.

## 9. References
- MovingCap CODE manual: https://movingcap.de/webmanuals/mc-eth-sw-manual-en/movingcapcode.html
- API stubs: `app-scripts/mcdrive.pyi`, `mcnet.pyi`, `refgo.pyi`, `sys.pyi`, `time.pyi`
  (kept beside the drive scripts so editors resolve `import mcdrive` etc. and show inline docs)
