import os
import random
import errno
import requests
import threading
import subprocess
import RPi.GPIO as GPIO
from time import sleep, time

# GPIO pins
gLight = 16 # Light sensor

downloadsFolder = "./QuestionFiles"
serverAddress = "http://46.101.42.140:1337/"
pollIntervalMinutes = 5

currentLightLevel = 0;
closedLightLevel = 100;

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

# Checks the current light level and reports the average
# readings over a second long window. 
# RUN ON A SEPARATE THREAD
def CheckLightLevels():
	global currentLightLevel

	window = [0,0,0,0,0] # 1 second window
	lastReading = 0
	try:
		GPIO.setmode(GPIO.BOARD)

		while True:

			# Ground the pin to empty the capacitor
			GPIO.setup(gLight, GPIO.OUT)
			GPIO.output(gLight, GPIO.LOW)
			sleep(0.2)
	
			# Set as an input
			GPIO.setup(gLight, GPIO.IN)	

			startTime = time()	
			while GPIO.input(gLight) == GPIO.LOW: pass
			elapsed = int((time() - startTime) * 1000000)	
		
			# Add data to rolling window
			window.append(elapsed)
			del window[0]

			# Rest of the program is given the window's average
			currentLightLevel = (sum(window) / float(len(window)))
			
	finally:
		GPIO.cleanup()

try:
	# Check the server on a separate thread
	serverPollThread = threading.Thread(name="biscuitServer", target=RefreshQuestions)
	serverPollThread.setDaemon(True)
	serverPollThread.start()

	# Measure the light level on a separate thread
	lightLevelThread = threading.Thread(name="biscuitLight", target=CheckLightLevels)
	lightLevelThread.setDaemon(True)
	lightLevelThread.start()
	
	# If the light level shows the box is open, play an audio message
	# Only play the message again after the box has been closed
	hasPlayed = False
	
	while True:
		sleep(2)

		tinOpen = (currentLightLevel > closedLightLevel)

		if not tinOpen:
			hasPlayed = False

		if tinOpen and not hasPlayed and os.listdir(downloadsFolder):
			hasPlayed = True
			thisQ = random.choice(os.listdir(downloadsFolder))
			localPath = os.path.join(downloadsFolder, thisQ)
			subprocess.call(['mplayer', localPath])
	
finally:
	print "Finish"