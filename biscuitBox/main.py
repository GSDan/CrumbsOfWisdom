import os
import random
import errno
import requests
import picamera
import sys
import threading
import subprocess
from PIL import Image, ImageEnhance
import RPi.GPIO as GPIO
from time import sleep, time

# GPIO pins
gLight = 16 # Light sensor
gCamBut = 15 # Take photo button
gSkipBut = 22 # Skip question button
gLED = 7 # LED

thisDir = os.path.dirname(os.path.abspath(__file__))
downloadsFolder = thisDir + "/QuestionFiles"
serverAddress = "http://138.68.133.209:1337/"
pollIntervalMinutes = 1

currentLightLevel = 0;
closedLightLevel = 100;
lastQuestionId = "";
lastPlayed = "";
canTakePhoto = False;
hasTakenPhoto = False;
tempImageFile = thisDir + "/image.jpg"

lock = threading.Lock()

def TakeAndCropPhoto():
	camera = picamera.PiCamera()
	camera.sharpness = 30
	camera.contrast = 100
	camera.saturation = -100
	camera.rotation = 90
	camera.capture(tempImageFile)
	
	subprocess.call(['mplayer', thisDir + "/camera-snap.wav"])

	# Crop image& up the contrast
	original = Image.open(tempImageFile)
	contrast = ImageEnhance.Contrast(original)
	original = contrast.enhance(3)

	width, height = original.size 
	left = int(width/3.6)
	top = int(height/12)
	right = int(width - width/7)
	bottom = int(height - height/12)
	original.crop((left, top, right, bottom)).save(tempImageFile)

def Error(e):
	print e
	subprocess.call(['mplayer', thisDir + "/error.mp3"])
	GPIO.cleanup()
	os._exit()

def UploadImage():
	print "Uploading " + tempImageFile
	try:
		with open(tempImageFile, 'rb') as payload:
			files = {"image" : payload}
			data = {"questionId" : lastQuestionId }
			res = requests.post(serverAddress + "advice/upload", files = files, data = data)
			
			if res.status_code == 200:
				print "UPLOAD RETURN: " + str(res.json())
				subprocess.call(['mplayer', thisDir + "/success.mp3"])
				return True
			else:
				print "Upload failed!!"
				return False
	except requests.exceptions.RequestException as e:    # This is the correct syntax
		Error(e);
		return False

# Checks for new questions on the server
# If a question doesn't exist locally, download it
# RUN ON A SEPARATE THREAD
def RefreshQuestions():
	while True:
		print "POLLING SERVER"

		try:
			res = requests.get(serverAddress + "question/getnew")

			RemoveUnwantedFiles(res.json())

			for question in res.json():
				localPath = os.path.join(downloadsFolder, os.path.basename(str(question["id"]) + ".mp3"))
				
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
		except requests.exceptions.RequestException as e:    # This is the correct syntax
			print e

		sleep(60 * pollIntervalMinutes)

def RemoveUnwantedFiles(questions):
	for fn in os.listdir(downloadsFolder):
		found = False
		thisPath = os.path.join(downloadsFolder, fn)
		print "Checking downloaded file", thisPath
		for question in questions:
			localPath = os.path.join(downloadsFolder, os.path.basename(question["id"] + ".mp3"))
			if localPath == thisPath:
				found = True
				break
		if not found:
			print "Deleting", thisPath
			os.remove(thisPath)

# Checks the current light level and reports the average
# readings over a second long window. 
# RUN ON A SEPARATE THREAD
def CheckLightLevels():
	global currentLightLevel

	try:
		window = [0,0,0,0,0] # 1 second window
		lastReading = 0
		
		GPIO.setup(gLED, GPIO.OUT)

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

			with lock:
				# Rest of the program is given the window's average
				currentLightLevel = (sum(window) / float(len(window)))

			# Update the LED - light if there are files available
			GPIO.output(gLED, len(os.listdir(downloadsFolder)));
	finally:
		Error("Light level err");
		
# Checks whether or not the buttons have been pressed
# If gCamBut has been and if permitted, take a photo and upload it
# If gSkipBut has been pressed, skip the last played question and play the next if able
def CheckButtonStatus():
	global canTakePhoto
	global hasTakenPhoto
	global lastQuestionId

	try:
		GPIO.setup (gCamBut, GPIO.IN, GPIO.PUD_UP)
		GPIO.setup (gSkipBut, GPIO.IN, GPIO.PUD_UP)
		camButPrevState = 1
		skipButPrevState = 1
		
		while True:
			camButCurrState = GPIO.input (gCamBut)
			if camButCurrState != camButPrevState:
				if camButCurrState == 1:
					if canTakePhoto and not hasTakenPhoto:
						print "Taking photo"
						TakeAndCropPhoto()
						
						success = UploadImage()
						if success:
							print "Deleting file:", lastPlayed
							os.remove(lastPlayed)
							lastQuestionId = ""
					else:
						print "Can't take a photo right now"
			skipButCurrState = GPIO.input (gSkipBut)
			if skipButCurrState != skipButPrevState:
				if skipButCurrState == 1:
					print "Skip button!"
					if lastQuestionId != "":
						data = {"questionId" : lastQuestionId }
						res = requests.post(serverAddress + "question/dismiss", data = data)
						os.remove(lastPlayed)
						if os.listdir(downloadsFolder):
							PlayQuestion()
						else:
							print "No more messages"
							subprocess.call(['mplayer', thisDir + "/noQuestions.mp3"])
			camButPrevState = camButCurrState
			skipButPrevState = skipButCurrState
			sleep (0.1)
	finally:
		Error(sys.exc_info()[0])

# Play a random downloaded question audio file
def PlayQuestion():
	global canTakePhoto
	global hasTakenPhoto
	global lastPlayed
	global lastQuestionId

	canTakePhoto = False
	hasTakenPhoto = False
	thisQ = random.choice(os.listdir(downloadsFolder))
	lastPlayed = os.path.join(downloadsFolder, thisQ)
	lastQuestionId = os.path.splitext(thisQ)[0]
	subprocess.call(['mplayer', lastPlayed])
	subprocess.call(['mplayer', thisDir + "/takePhoto.mp3"])

try:
	GPIO.setmode(GPIO.BOARD)

	try:
		# Make the downloads folder if it doesn't exist
		os.makedirs(downloadsFolder)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	print "Setting volume to 90%"
	subprocess.call(["amixer", "cset", "numid=1", "--", "90%"])


	# CREATE ALL THE THREADS!!
	# Check the server on a separate thread
	serverPollThread = threading.Thread(name="biscuitServer", target=RefreshQuestions)
	serverPollThread.setDaemon(True)
	serverPollThread.start()

	# Measure the light level on a separate thread
	lightLevelThread = threading.Thread(name="biscuitLight", target=CheckLightLevels)
	lightLevelThread.setDaemon(True)
	lightLevelThread.start()

	# Check the take photo button
	buttonThread = threading.Thread(name="biscuitButton", target=CheckButtonStatus)
	buttonThread.setDaemon(True)
	buttonThread.start()
	
	# If the light level shows the box is open, play an audio message
	# Only play the message again after the box has been closed
	hasPlayed = False
	
	subprocess.call(['mplayer', thisDir + "/start.mp3"])

	while True:
		sleep(1.5)

		with lock:
			tinOpen = (currentLightLevel > closedLightLevel)

		if not tinOpen:
			if hasPlayed:
				canTakePhoto = True
			hasPlayed = False

		if tinOpen and not hasPlayed and os.listdir(downloadsFolder):
			hasPlayed = True
			PlayQuestion()
	
finally:
	print "Finish"
	GPIO.cleanup()
