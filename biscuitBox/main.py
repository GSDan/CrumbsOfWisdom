import os
import errno
import requests
import threading
import RPi.GPIO as GPIO
from time import sleep

# GPIO pins
gBut = 7	# button 
gLed = 10	# LED

downloadsFolder = "./QuestionFiles"
serverAddress = "http://46.101.42.140:1337/"

def RefreshQuestions():
	# Make the downloads folder if it doesn't exist
	try:
		os.makedirs(downloadsFolder)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	while True:
		res = requests.get(serverAddress + "question/getnew")

		for question in res.json():
			localPath = os.path.join(downloadsFolder, os.path.basename(question["filename"]))
			
			# Download the file if it doesn't exist locally
			if not os.path.isfile(localPath):
				params = {"fd" : question["filename"] }
				r = requests.get(serverAddress + "file/download", params=params, stream=True)

				print "DOWNLOADING:", question["filename"]

				with open(localPath, 'wb') as f:
					for chunk in r.iter_content(chunk_size=1024): 
						if chunk: # filter out keep-alive new chunks
							f.write(chunk)
							f.flush()
				
				print "FINISHED:", localPath 		
			
			else:
				print "ALREADY CACHED:", localPath

		sleep(10)


RefreshQuestions();

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
