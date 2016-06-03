import RPi.GPIO as GPIO
from time import sleep

# GPIO pin
gBut = 7	# button 

try:
	# initialising GPIO pin and initial button state 
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(gBut, GPIO.IN, GPIO.PUD_UP)
	butState = 1
	
	while True:
		# get current button signal 
		# 1 = not pressed, 0 = pressed
		but = GPIO.input(gBut)
		# compare if button is being pressed 
		if but != butState:
			if but == 0:
				# if button is pressed, DO SOMETHING
				print "pressed"
		butState = but
		sleep(0.1)
	
finally:
	GPIO.cleanup
