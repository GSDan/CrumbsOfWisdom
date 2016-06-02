import RPi.GPIO as GPIO
from time import sleep
import subprocess

# GPIO pins
gBut = 7	# button 
gLed = 10	# LED

# recordings
rec_num = 1

com_record = "arecord -f dat -r 48000 -D plughw:0,0 out%d.wav" % rec_num
com_lame = "lame -b 320 out%d.wav out%d.mp3" % (rec_num, rec_num)
com_play = "mpg123 out%d.mp3" % rec_num
com_kill = "killall -KILL arecord"

def play_it(mp3file):
	com_playfile = "mpg123 %s" % mp3file
	subprocess.call(com_playfile, shell=True)

def record_message():
	return subprocess.Popen(com_record, shell=True)

def process_recording(pid):
	# stop recording
	pid.terminate()
	pid.kill()
	subprocess.call(com_kill, shell=True)
	print "Kill Kill Kill!"
	# convert wav into mp3 
	subprocess.call(com_lame, shell=True)
	# play message
	subprocess.call(com_play, shell=True)

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
					# stop the recording and process the audio file
					process_recording(pid)
				else:
					GPIO.output(gLed, GPIO.HIGH)
					print "on"
					# start recording
					pid = record_message()
				ledState = not(ledState)
		butState = but
		sleep(0.1)
	
finally:
	GPIO.cleanup()
