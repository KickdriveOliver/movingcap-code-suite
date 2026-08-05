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

POSITION_OPTION_INDEX = 0x60F2
POSITION_OPTION_SUBINDEX = 0x00
ROTARY_FORWARD_ONLY = 0x0080

IN1_CONFIG_INDEX = 0x3511
IN2_CONFIG_INDEX = 0x3512
IN_CONFIG_FUNCTION_SUBINDEX = 0x01
IN_CONFIG_TARGET_SUBINDEX = 0x08

SIM_IN_FUNCTION_CMD_INDEX = 0x3510
SIM_IN_FUNCTION_CMD_SUBINDEX = 0x02

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

mc.WriteObject(POSITION_OPTION_INDEX, POSITION_OPTION_SUBINDEX, ROTARY_FORWARD_ONLY)

# make sure there is no hardwired "Timed Motion Absolute" on IN1 or IN2. 
# our script will control this directly
mc.WriteObject(IN1_CONFIG_INDEX, IN_CONFIG_FUNCTION_SUBINDEX, 0x0) 
mc.WriteObject(IN2_CONFIG_INDEX, IN_CONFIG_FUNCTION_SUBINDEX, 0x0) 

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