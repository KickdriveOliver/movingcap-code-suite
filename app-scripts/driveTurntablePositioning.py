# driveTurntablePositioning.py
# MovingCap CODE (MicroPython) example application for MovingCap Ethernet ETH.
# www.movingcap.de
#
# WHAT THIS EXAMPLE SHOWS
#   A minimal but complete turntable demo that moves between two absolute
#   positions, driven by a single digital input:
#     * Each rising edge on IN1 toggles the target between POS_A and POS_B.
#     * OUT1 pulses to confirm that the target was reached.
#   It demonstrates the general building blocks of a MovingCap CODE app:
#     1. parameter setup from an object list (Kickdrive export style),
#     2. a first-run guard using the documented user-parameter area (3410h),
#     3. a clean enable -> reference -> move -> confirm sequence,
#     4. UDP diagnostics via print() so a host test can observe behaviour.
#
# SAFETY: running this script ENABLES the drive and MOVES the axis. Make sure
# the turntable can rotate freely between POS_A and POS_B before starting.

import time
import mcdrive as mc

# ---------------------------------------------------------------------------
# Application configuration (edit to taste)
# ---------------------------------------------------------------------------
IN_TOGGLE = 1          # digital input that toggles the target position
OUT_CONFIRM = 1        # digital output pulsed when a target is reached
CONFIRM_MS = 400       # how long OUT1 stays high to confirm arrival [ms]
INITIAL_WAIT_MS = 3000 # startup delay so the axis does not move immediately

POS_A = 0              # first target position [user units = degrees]
POS_B = 180            # second target position [user units = degrees]

PROFILE_VELOCITY = 180 # positioning speed [user units/s]
PROFILE_ACCEL = 500    # positioning acceleration [user units/s^2]
PROFILE_DECEL = 500    # positioning deceleration [user units/s^2]
MAX_TORQUE = 1000      # max current/torque [0.1%], 1000 = 100%

MOTION_TIMEOUT_MS = 8000  # give up waiting for a move after this long

# First-run guard: object 3410h.01h (documented integer32 user parameter) holds
# this magic number once the defaults have been written. On the next start the
# script sees the magic and skips the (slower) parameter init.
CONFIG_INDEX = 0x3410
CONFIG_SUBINDEX = 0x01
APP_MAGIC_NUMBER = 0x7475726E   # arbitrary marker for THIS application's config

# ---------------------------------------------------------------------------
# Default parameters, written only on the first run (Kickdrive export format:
#   "<seg>.<index>h.<sub>h,<type>,<value> # comment"). Segment 050 = drive axis.
# ---------------------------------------------------------------------------
MOTOR_PARAMETERS = """
050.3401h.03h,unsigned32,1     # Position control window
050.3401h.15h,unsigned16,1000  # Acc. torque [0.1%]
050.3401h.16h,unsigned16,1000  # Dec. torque [0.1%]
050.3401h.18h,unsigned16,1000  # Stall torque [0.1%]
050.3511h.01h,unsigned16,0     # IN1 function = none (we read IN1 in script)
050.3512h.01h,unsigned16,0     # IN2 function = none
050.3513h.01h,unsigned16,0     # IN3 function = none
050.3514h.01h,unsigned16,0     # IN4 function = none
050.3611h.01h,unsigned16,0     # OUT1 function = none (we drive OUT1 in script)
050.3612h.01h,unsigned16,0     # OUT2 function = none
050.6073h.00h,unsigned16,1000  # Max current/torque [0.1%]
050.6091h.01h,unsigned32,5     # Gear: motor revolutions
050.6091h.02h,unsigned32,1     # Gear: shaft revolutions
050.6092h.01h,unsigned32,360   # Feed (user units per shaft revolution)
050.6092h.02h,unsigned32,1     # Feed shaft revolutions
"""

APP_PARAMETERS = """
050.6067h.00h,unsigned32,1     # Target reached window [user units]
050.6068h.00h,unsigned16,200   # Target window time [ms]
050.607dh.01h,integer32,-3600  # Soft limit min position [user units]
050.607dh.02h,integer32,3600   # Soft limit max position [user units]
050.60f2h.00h,unsigned16,0     # Positioning option code (absolute)
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def WriteObjectsFromKickdriveList(exportText):
    # Apply a Kickdrive object-list export line by line.
    params = [line.split(',') for line in exportText.split('\n') if line.strip()]
    for param in params:
        if len(param) < 3:
            continue
        ident = param[0].split('.')
        index = int(ident[1].rstrip('h'), 16)
        subindex = int(ident[2].rstrip('h'), 16)
        value = int(param[2].split('#')[0])
        mc.WriteObject(index, subindex, value)
        print('  set ' + hex(index) + '.' + hex(subindex) + ' = ' + str(value))


def WaitMotionDone(timeoutMs):
    # Wait for "target reached", aborting on error or timeout.
    # Returns 1 on success, 0 on error/timeout.
    startTime = time.ticks_ms()
    while mc.ChkReady() == 0:
        if mc.ChkError() != 0:
            print('  ERROR during motion, statusword error bit set')
            return 0
        if time.ticks_ms() - startTime > timeoutMs:
            print('  TIMEOUT waiting for target reached')
            return 0
        time.sleep_ms(1)
    return 1


def ApplyParametersIfFirstRun():
    # First-run guard using the documented user-parameter object 3410h.01h.
    magic = mc.ReadObject(CONFIG_INDEX, CONFIG_SUBINDEX)
    if magic == APP_MAGIC_NUMBER:
        print('Config magic OK (' + hex(magic) + '): skipping parameter init')
        return
    print('First run: writing default parameters ...')
    WriteObjectsFromKickdriveList(MOTOR_PARAMETERS)
    WriteObjectsFromKickdriveList(APP_PARAMETERS)
    mc.WriteObject(CONFIG_INDEX, CONFIG_SUBINDEX, APP_MAGIC_NUMBER)
    print('Default parameters applied, magic set to ' + hex(APP_MAGIC_NUMBER))


def ConfirmArrival():
    mc.SetOut(OUT_CONFIRM)        # drives digital output OUT1 high
    time.sleep_ms(CONFIRM_MS)
    mc.ClearOut(OUT_CONFIRM)      # drives digital output OUT1 low


def WaitRisingEdge(inputNo):
    # Wait for input to go low (if currently high) then return on the next high.
    while mc.ChkIn(inputNo) == 1:
        time.sleep_ms(1)
    while mc.ChkIn(inputNo) == 0:
        time.sleep_ms(1)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
print('driveTurntablePositioning started')
ApplyParametersIfFirstRun()

mc.ClearOut(OUT_CONFIRM)         # ensure confirm output starts low
mc.SetPosVel(PROFILE_VELOCITY)
mc.SetAcc(PROFILE_ACCEL)
mc.SetDec(PROFILE_DECEL)
mc.SetTorque(MAX_TORQUE)

print('Enabling drive ...')
mc.EnableDrive()                 # powers and enables the drive

# Reference without motion: make the current position the new zero (method 35).
print('Referencing current position as zero ...')
mc.GoHome(35, PROFILE_VELOCITY, PROFILE_ACCEL, 0)
WaitMotionDone(MOTION_TIMEOUT_MS)
print('Ready at pos=' + str(mc.GetActualPos()))

time.sleep_ms(INITIAL_WAIT_MS)

# ---------------------------------------------------------------------------
# Main loop: each IN1 rising edge toggles between POS_A and POS_B
# ---------------------------------------------------------------------------
targetIsB = 1
while 1:
    WaitRisingEdge(IN_TOGGLE)
    if targetIsB == 1:
        target = POS_B
        label = 'POS_B'
    else:
        target = POS_A
        label = 'POS_A'
    print('IN1 edge: moving to ' + label + ' (' + str(target) + ')')
    mc.GoPosAbs(target)          # starts axis motion to absolute target
    if WaitMotionDone(MOTION_TIMEOUT_MS) == 1:
        print(label + ' OK pos=' + str(mc.GetActualPos()))
        ConfirmArrival()
        targetIsB = 1 - targetIsB
    else:
        print(label + ' FAILED pos=' + str(mc.GetActualPos()))
        mc.PowerQuit()           # disable drive on failure
        break
