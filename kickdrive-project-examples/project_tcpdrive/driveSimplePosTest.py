#id driveSimplePosTest.py 2022-10-14 oh
# This is a simple positioning demo, it assumes a MovingCap turnTRACK 
# with user defined coordinates, e.g. positioning unit = ° (degrees)
import sys
import drive

def ChkReady(): 
	# Check statusword for "target reached"
	while (drive.ChkReady() == 0):
		sys.wait(1)
	# only continue if no error 
	while (drive.ChkError() != 0):
		sys.wait(1)

# initial wait, don't surprise me with immediate movement
sys.wait(2000)

# general init
drive.EnableDrive()
drive.SetAcc(500)
drive.SetDec(500)
drive.SetPosVel(360)
# and go...
while(1):
	drive.GoPosAbs(0)
	ChkReady()
	drive.GoPosAbs(1080)
	ChkReady()
	drive.GoPosAbs(360) 
	ChkReady()