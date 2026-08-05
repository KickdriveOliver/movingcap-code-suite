#id turntrack_6_slot_turntable.py oh 2026-08-05
# MovingCap CODE (MicroPython) generic rotary-table slot positioning example.
#
# IN1 high/rising edge moves to 0 degrees.
# IN2 high/rising edge finds the nearest configured slot using circular distance,
# then moves forward to the following slot.
# 
# Preconditions: 
# - gear/axis configuration prepared for 360° motion, see http://192.168.2.150/quickstart.html
# - softlimit min=0 and max=360 for 360° motion, see http://192.168.2.150/setup.html
# - appropriate target reached window/time settings, see http://192.168.2.150/setup.html
#
# Motion result indication can be configured independently with an output function:
# 4 = positioning feedback, 5 = Drive without error/warning, or 6 = Position and status feedback.
#
# SAFETY: running this script ENABLES the drive and PHYSICALLY MOVES the axis.

import time
import mcdrive as mc

IN_ZERO = 1
IN_NEXT = 2
SLOTS = [0, 60, 120, 180, 240, 300]
REVOLUTION = 360

POLL_MS = 2

CONFIG_INDEX = 0x3410
CONFIG_SUBINDEX = 0x01
APP_MAGIC_NUMBER = 0x74753673  # "tu6s"

POSITION_OPTION_INDEX = 0x60F2
POSITION_OPTION_SUBINDEX = 0x00
ROTARY_FORWARD_ONLY = 0x0080

IN1_CONFIG_INDEX = 0x3511
IN2_CONFIG_INDEX = 0x3512
IN_CONFIG_FUNCTION_SUBINDEX = 0x01
IN_CONFIG_TARGET_SUBINDEX = 0x08

SIM_IN_FUNCTION_CMD_INDEX = 0x3510
SIM_IN_FUNCTION_CMD_SUBINDEX = 0x02

# Defaults captured from the reference turnTRACK 349 application drive.
# They are written only when the application magic is not present.
# NOTE: these defaults are intended for a 35:1 gear ratio, 360° motion. Adjust as needed for your application.
MOTOR_PARAMETERS = """
050.3401h.03h,unsigned32,20    # Position control window
050.3401h.15h,unsigned16,1000  # Acc. torque [0.1%]
050.3401h.16h,unsigned16,1000  # Dec. torque [0.1%]
050.3401h.18h,unsigned16,1000  # Stall torque [0.1%]
050.6073h.00h,unsigned16,1000  # Max current/torque [0.1%]
050.6091h.01h,unsigned32,35    # Gear: motor revolutions
050.6091h.02h,unsigned32,1     # Gear: shaft revolutions
050.6092h.01h,unsigned32,360   # Feed: degrees per shaft revolution
050.6092h.02h,unsigned32,1     # Feed: shaft revolutions
"""

APP_PARAMETERS = """
050.3511h.01h,unsigned16,0     # IN1 function = none (script triggers its profile)
050.3511h.06h,unsigned32,2400  # IN1 positioning velocity
050.3511h.07h,unsigned32,5000  # IN1 positioning acceleration
050.3511h.08h,integer32,0      # IN1 target position
050.3511h.09h,unsigned32,2500  # IN1 positioning deceleration
050.3512h.01h,unsigned16,0     # IN2 function = none (script triggers its profile)
050.3512h.06h,unsigned32,2400  # IN2 positioning velocity
050.3512h.07h,unsigned32,5000  # IN2 positioning acceleration
050.3512h.08h,integer32,60     # IN2 initial target position
050.3512h.09h,unsigned32,2500  # IN2 positioning deceleration
050.3611h.01h,unsigned16,4     # OUT1 = positioning feedback
050.3612h.01h,unsigned16,5     # OUT2 = status feedback
050.6067h.00h,unsigned32,1     # Target reached window [degrees]
050.6068h.00h,unsigned16,1     # Target window time [ms]
050.607dh.01h,integer32,0      # Soft limit min position [degrees]
050.607dh.02h,integer32,360    # Soft limit max position [degrees]
050.60f2h.00h,unsigned16,128   # Rotary positioning, forward only
"""


def WriteObjectsFromKickdriveList(exportText):
    params = [line.split(',') for line in exportText.split('\n') if line.strip()]
    for param in params:
        ident = param[0].split('.')
        index = int(ident[1].rstrip('h'), 16)
        subindex = int(ident[2].rstrip('h'), 16)
        value = int(param[2].split('#')[0])
        mc.WriteObject(index, subindex, value)


def ApplyParametersIfFirstRun():
    magic = mc.ReadObject(CONFIG_INDEX, CONFIG_SUBINDEX)
    if magic == APP_MAGIC_NUMBER:
        print('Config magic OK: skipping parameter init')
        return
    print('First run: writing default parameters')
    WriteObjectsFromKickdriveList(MOTOR_PARAMETERS)
    WriteObjectsFromKickdriveList(APP_PARAMETERS)
    mc.WriteObject(CONFIG_INDEX, CONFIG_SUBINDEX, APP_MAGIC_NUMBER)
    print('Default parameters applied, magic=' + hex(APP_MAGIC_NUMBER))


def CircularDistance(a, b):
    distance = (a - b) % REVOLUTION
    if distance > REVOLUTION // 2:
        distance = REVOLUTION - distance
    return distance


def NearestSlotIndex(position):
    wrapped = position % REVOLUTION
    nearestIndex = 0
    nearestDistance = CircularDistance(wrapped, SLOTS[0])
    index = 1
    while index < len(SLOTS):
        distance = CircularDistance(wrapped, SLOTS[index])
        if distance < nearestDistance:
            nearestIndex = index
            nearestDistance = distance
        index = index + 1
    return nearestIndex


ApplyParametersIfFirstRun()

print('Ready pos=' + str(mc.GetActualPos()) + ' option=' + hex(mc.ReadObject(POSITION_OPTION_INDEX, POSITION_OPTION_SUBINDEX)))

# Seed edge history low so an input already high at startup is accepted.
previousZero = 0
previousNext = 0
while 1:
    zero = mc.ChkIn(IN_ZERO)
    nextSlot = mc.ChkIn(IN_NEXT)

    if zero == 1 and previousZero == 0:
        # Trigger "4 = Timed Motion Absolute" with IN1 settings
        mc.WriteObject(SIM_IN_FUNCTION_CMD_INDEX, SIM_IN_FUNCTION_CMD_SUBINDEX, 0x0104)
    elif nextSlot == 1 and previousNext == 0:
        actual = mc.GetActualPos()
        nearestIndex = NearestSlotIndex(actual)
        targetIndex = (nearestIndex + 1) % len(SLOTS)
        target = SLOTS[targetIndex]
        mc.WriteObject(IN2_CONFIG_INDEX, IN_CONFIG_TARGET_SUBINDEX, target)
        print('IN2: nearest=' + str(SLOTS[nearestIndex]) + ' next=' + str(target))
        # Trigger "4 = Timed Motion Absolute" with IN2 settings
        mc.WriteObject(SIM_IN_FUNCTION_CMD_INDEX, SIM_IN_FUNCTION_CMD_SUBINDEX, 0x0204)  

    previousZero = zero
    previousNext = nextSlot
    time.sleep_ms(POLL_MS)