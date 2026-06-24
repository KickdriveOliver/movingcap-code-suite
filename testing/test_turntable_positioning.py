#!/usr/bin/env python3
"""Functional test for app-scripts/driveTurntablePositioning.py.

Host-side (desktop CPython 3) test. It uploads the example MovingCap CODE app to
a real drive, runs it, drives it through the REFGO virtual-input interface, and
verifies the behaviour against UDP diagnostics and the actual-position object.

Run from this directory (``testing/``) so ``import mctk`` resolves::

    python test_turntable_positioning.py [DEVICE_IP]

SAFETY: this enables the drive and PHYSICALLY MOVES the axis between 0 and 180
degrees. Ensure the turntable can rotate freely before running.
"""

import os
import sys
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from mctk import (
    RefgoClient,
    TestRunner,
    UdpMonitor,
    input_mask,
    start_script,
    stop_script,
    upload_script,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEVICE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.2.150"
SCRIPT_NAME = "driveTurntablePositioning.py"
SCRIPT_PATH = os.path.normpath(os.path.join(THIS_DIR, "..", "app-scripts", SCRIPT_NAME))
RESULTS_DIR = os.path.join(THIS_DIR, "results")

# Must match the values in the drive script.
APP_MAGIC_NUMBER = 0x7475726E
CONFIG_INDEX = 0x3410
CONFIG_SUBINDEX = 0x01
POS_A = 0
POS_B = 180
POS_TOLERANCE = 4

IN1 = input_mask(1)        # 0x10000
SIM_CLEAR = 0

STARTUP_WAIT_S = 5.0
MOVE_WAIT_S = 5.0


def near(actual, expected, tol=POS_TOLERANCE):
    """True if actual ~= expected on a 360-degree rotating axis."""
    if actual is None:
        return False
    diff = (actual - expected) % 360
    return diff <= tol or diff >= (360 - tol)


def main():
    runner = TestRunner("test_turntable_positioning", device_ip=DEVICE_IP, script=SCRIPT_NAME)

    runner.section("Setup: stop script, clear config magic + inputs, upload")
    stop_script(DEVICE_IP)
    time.sleep(1.0)

    drive = RefgoClient(DEVICE_IP, verbose=True)
    drive.connect()
    # Force a first-run parameter init by clearing the config magic, and make
    # sure no virtual input is held active before the script starts.
    drive.write_object(CONFIG_INDEX, CONFIG_SUBINDEX, 0)
    drive.simulate_inputs(SIM_CLEAR)
    print("[setup] config magic cleared, input simulation cleared")

    monitor = UdpMonitor(DEVICE_IP)
    monitor.start()

    uploaded = upload_script(DEVICE_IP, SCRIPT_PATH)
    if not runner.check("script upload", uploaded):
        monitor.stop()
        drive.close()
        return runner.finish(RESULTS_DIR)

    started = start_script(DEVICE_IP)
    if not runner.check("script start (HTTP)", started):
        monitor.stop()
        drive.close()
        return runner.finish(RESULTS_DIR)

    # -- TC-01: startup + first-run parameter init ---------------------------
    runner.section("TC-01: startup and first-run parameter init")
    time.sleep(STARTUP_WAIT_S)
    runner.check("TC-01 startup message", monitor.has_line("driveTurntablePositioning started"),
                 "UDP startup print received")
    runner.check("TC-01 first-run init", monitor.has_line("First run: writing default parameters"),
                 "cleared magic triggered parameter write")
    runner.check("TC-01 magic set", monitor.has_line("Default parameters applied, magic set"),
                 "magic written after init")
    runner.check("TC-01 referenced + ready", monitor.has_line("Ready at pos="),
                 "drive enabled and referenced without fault")
    magic = drive.read_object(CONFIG_INDEX, CONFIG_SUBINDEX)
    runner.check("TC-01 magic readable via REFGO", magic == APP_MAGIC_NUMBER,
                 "read 3410h.01h=" + (hex(magic) if magic is not None else "None")
                 + " (expect " + hex(APP_MAGIC_NUMBER) + ")")

    # -- TC-02: IN1 edge -> move to POS_B (180) ------------------------------
    runner.section("TC-02: IN1 rising edge moves to POS_B (180 deg)")
    monitor.clear()
    drive.simulate_inputs(IN1)         # IN1 high -> rising edge
    time.sleep(MOVE_WAIT_S)
    drive.simulate_inputs(SIM_CLEAR)   # release IN1
    time.sleep(1.0)
    runner.check("TC-02 POS_B reached (UDP)", monitor.has_line("POS_B OK"), "move to POS_B completed")
    pos_refgo = drive.actual_position()
    pos_udp = monitor.last_value("POS_B OK", "pos=")
    runner.check("TC-02 position near 180 (REFGO)", near(pos_refgo, POS_B),
                 "6064h=" + str(pos_refgo) + " (expect " + str(POS_B) + "+-" + str(POS_TOLERANCE) + ")")
    runner.check("TC-02 position near 180 (UDP)", near(pos_udp, POS_B),
                 "udp pos=" + str(pos_udp))

    # -- TC-03: IN1 edge -> move back to POS_A (0) ---------------------------
    runner.section("TC-03: next IN1 rising edge moves back to POS_A (0 deg)")
    monitor.clear()
    drive.simulate_inputs(IN1)
    time.sleep(MOVE_WAIT_S)
    drive.simulate_inputs(SIM_CLEAR)
    time.sleep(1.0)
    runner.check("TC-03 POS_A reached (UDP)", monitor.has_line("POS_A OK"), "move to POS_A completed")
    pos_refgo = drive.actual_position()
    runner.check("TC-03 position near 0 (REFGO)", near(pos_refgo, POS_A),
                 "6064h=" + str(pos_refgo) + " (expect " + str(POS_A) + "+-" + str(POS_TOLERANCE) + ")")

    # -- TC-04: second run skips parameter init ------------------------------
    runner.section("TC-04: restart skips parameter init (magic already set)")
    stop_script(DEVICE_IP)
    time.sleep(1.0)
    monitor.clear()
    started2 = start_script(DEVICE_IP)
    runner.check("TC-04 script restart", started2, "restarted without re-upload")
    time.sleep(STARTUP_WAIT_S)
    runner.check("TC-04 magic OK skip", monitor.has_line("skipping parameter init"),
                 "second run skipped parameter write as expected")

    # Cleanup: stop script and release inputs.
    stop_script(DEVICE_IP)
    drive.simulate_inputs(SIM_CLEAR)
    monitor.stop()
    drive.close()

    return runner.finish(RESULTS_DIR)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
