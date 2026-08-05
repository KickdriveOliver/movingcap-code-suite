#!/usr/bin/env python3
"""Basic functional test for app-scripts/turntrack_6_slot_turntable.py.

Host-side (desktop CPython 3) test. It uploads the example MovingCap CODE app,
simulates IN1/IN2 through REFGO, and verifies the resulting actual positions.

Run from this directory (``testing/``) so ``import mctk`` resolves::

    python test_turntrack_6_slot_turntable.py [DEVICE_IP]

SAFETY: this enables the drive and PHYSICALLY MOVES the axis through several
60-degree slots. Ensure the turntable can rotate freely before running.
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
    input_mask,
    start_script,
    stop_script,
    upload_script,
)

DEVICE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.2.150"
SCRIPT_NAME = "turntrack_6_slot_turntable.py"
SCRIPT_PATH = os.path.normpath(os.path.join(THIS_DIR, "..", "app-scripts", SCRIPT_NAME))
RESULTS_DIR = os.path.join(THIS_DIR, "results")

IN1 = input_mask(1)
IN2 = input_mask(2)
SIM_CLEAR = 0
POSITION_TOLERANCE = 4
STARTUP_WAIT_S = 2.0
MOVE_WAIT_S = 5.0


def near(actual, expected, tolerance=POSITION_TOLERANCE):
    """Return whether two positions are near each other on a 360-degree axis."""
    if actual is None:
        return False
    difference = (actual - expected) % 360
    return difference <= tolerance or difference >= 360 - tolerance


def pulse_input(drive, input_value):
    drive.simulate_inputs(input_value)
    time.sleep(MOVE_WAIT_S)
    drive.simulate_inputs(SIM_CLEAR)
    time.sleep(0.5)


def main():
    runner = TestRunner(
        "test_turntrack_6_slot_turntable",
        device_ip=DEVICE_IP,
        script=SCRIPT_NAME,
    )

    runner.section("Setup: stop script, clear inputs, upload and start")
    stop_script(DEVICE_IP)
    time.sleep(1.0)

    drive = RefgoClient(DEVICE_IP, verbose=True)
    drive.connect()
    drive.simulate_inputs(SIM_CLEAR)

    uploaded = upload_script(DEVICE_IP, SCRIPT_PATH)
    if not runner.check("script upload", uploaded):
        drive.close()
        return runner.finish(RESULTS_DIR)

    started = start_script(DEVICE_IP)
    if not runner.check("script start (HTTP)", started):
        drive.close()
        return runner.finish(RESULTS_DIR)
    time.sleep(STARTUP_WAIT_S)

    runner.section("TC-01: IN1 moves to the next 0-degree position")
    pulse_input(drive, IN1)
    position = drive.actual_position()
    runner.check(
        "TC-01 position near 0",
        near(position, 0),
        "6064h=" + str(position) + " (expect 0+-" + str(POSITION_TOLERANCE) + ")",
    )

    runner.section("TC-02: repeated IN2 advances through the next 60-degree slots")
    for expected in (60, 120, 180):
        pulse_input(drive, IN2)
        position = drive.actual_position()
        runner.check(
            "TC-02 position near " + str(expected),
            near(position, expected),
            "6064h=" + str(position) + " (expect " + str(expected)
            + "+-" + str(POSITION_TOLERANCE) + ")",
        )

    runner.section("TC-03: IN1 moves forward to the next 0-degree position")
    pulse_input(drive, IN1)
    position = drive.actual_position()
    runner.check(
        "TC-03 position near 0",
        near(position, 0),
        "6064h=" + str(position) + " (expect 0+-" + str(POSITION_TOLERANCE) + ")",
    )

    stop_script(DEVICE_IP)
    drive.simulate_inputs(SIM_CLEAR)
    drive.close()

    return runner.finish(RESULTS_DIR)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
