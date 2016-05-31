import os
import random
import errno
import requests
import threading
import subprocess
import RPi.GPIO as GPIO
from time import sleep

# GPIO pins
gBut = 7	# button 
gLed = 10	# LED

downloadsFolder = "./QuestionFiles"
serverAddress = "http://46.101.42.140:1337/"
pollIntervalMinutes = 5

# Checks for new questions on the server
# If a question doesn't exist locally, download it
# RUN ON A SEPARATE THREAD
def RefreshQuestions():
	
	try:
		# Make the downloads folder if it doesn't exist
		os.makedirs(downloadsFolder)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	while True:
		print "POLLING SERVER"
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

		sleep(60 * pollIntervalMinutes)

try:
	# Check the server on a separate thread
	serverPollThread = threading.Thread(name="steam", target=RefreshQuestions)
	serverPollThread.setDaemon(True)

	serverPollThread.start()

	# initialising GPIO + pins + states
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(gBut, GPIO.IN, GPIO.PUD_UP)
	#GPIO.setup(gLed, GPIO.OUT)
	butState = 1
	ledState = False
	
	while True:
		but = GPIO.input(gBut)
		if but != butState:
			if but == 0:
				# if button is pressed and there are audio files to play
				if os.listdir(downloadsFolder):
					thisQ = random.choice(os.listdir(downloadsFolder))
					localPath = os.path.join(downloadsFolder, thisQ)
					subprocess.call(['mplayer', localPath])

				else:
					print "No files to play"

		butState = but
		sleep(0.1)
	
finally:
	GPIO.cleanup
