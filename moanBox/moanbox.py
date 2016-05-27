import RPi.GPIO as GPIO
from time import sleep

# GPIO pins
gBut = 7	# button 
gLed = 10	# LED

try:
	# initialising GPIO + pins + states
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(gBut, GPIO.IN, GPIO.PUD_UP)
	GPIO.setup(gLed, GPIO.OUT)
	butState = 1
	ledState = False
	
	while True:
		but = GPIO.input(gBut)
		if but != butState:
			if but == 0:
				# if button is pressed
				if ledState:
					GPIO.output(gLed, GPIO.LOW)
					print "off"
				else:
					GPIO.output(gLed, GPIO.HIGH)
					print "on"
				ledState = not(ledState)
		butState = but
		sleep(0.1)
	
finally:
	GPIO.cleanup
