#id rev6 flat/shortTRACK demo 2026-08-05 oh
# Example application for MovingCap flatTRACK or shortTRACK
# This demo demonstrates flatTRACK/shortTRACK profile positioning.
# It moves through several absolute positions with different velocity,
# acceleration, and jerk settings, then repeats the sequence continuously.
#
# Safety: The drive will be enabled and the axis will move automatically.
# Verify the soft limits, clear the working area, and keep an emergency stop
# accessible before starting the demo.
#
# This diagnostic demo intentionally waits without a timeout for target reached
# and for fault clearance. It supports different flatTRACK/shortTRACK variants
# and configurations; if motion cannot complete, inspect the drive, mechanics,
# configuration, and active fault instead of applying an automatic reaction.
import time
import mcdrive as mc

def WaitTargetReached():
	# avoid early abort, because drive has not yet processed the motion command
	time.sleep_ms(10) 
	# check for target reached. no timeout.
	while (mc.ChkReady() == 0):
		time.sleep_ms(1)
	# if there is an error, stay until cleared. no timeout
	while (mc.ChkError() != 0):
		time.sleep_ms(1)

# only run this script if softlimit is set up properly
softLimitMin = mc.ReadObject(0x607d, 1) 
softLimitMax = mc.ReadObject(0x607d, 2)
if ((softLimitMax - softLimitMin < 40000) or softLimitMax > 999999):
	print("flatTRACK demo abort. Check softlimit objects 607Dh.1h and 607D.2h!") 
else: 
	# initial wait, don't surprise me with immediate movement
	time.sleep_ms(5000)
	# prepare for operation and check success
	if mc.EnableDrive() > 0:
		while(1):
			mc.SetAcc(50) # (flat/shortTRACK currently does not evaluate deceleration parameter) 
			mc.WriteObject(0x60A4, 0, 1000) # flat/shortTRACK RABBIT controller uses jerk parameter
			mc.SetPosVel(50000)
			mc.GoPosAbs(softLimitMin + 3000)
			WaitTargetReached()
			time.sleep_ms(2000)

			mc.SetAcc(10000)
			mc.WriteObject(0x60A4, 0, 500000)
			mc.SetPosVel(200000)
			mc.GoPosAbs(softLimitMin + 15000)
			WaitTargetReached()
			time.sleep_ms(2000)
			
			mc.SetAcc(15000)
			mc.WriteObject(0x60A4, 0, 1000000)
			mc.SetPosVel(500000)
			nextPos = softLimitMin + 15000
			while (nextPos < softLimitMax - 10000):
				nextPos += 3000
				mc.GoPosAbs(nextPos)
				WaitTargetReached()
				time.sleep_ms(100)
			time.sleep_ms(1000)
			
			mc.SetAcc(20000)
			mc.WriteObject(0x60A4, 0, 200000)
			mc.SetPosVel(1000000)
			mc.GoPosAbs(softLimitMax - 3000)
			WaitTargetReached()
			time.sleep_ms(5000)
	else:
		print("flatTRACK demo abort. EnableDrive() failed; check drive status and errors.")
	