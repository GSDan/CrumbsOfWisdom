import os
import errno
import requests
import threading
import RPi.GPIO as GPIO
from time import sleep
import subprocess

# GPIO pins
gBut = 7	# button 
gLed = 10	# LED

# recordings
rec_num = 0
thisDir = os.path.dirname(os.path.abspath(__file__))
recordingsFolder = thisDir + "/Recordings"
serverAddress = "http://46.101.42.140:1337/"

# commands
com_record = "arecord -f dat -r 48000 -D plughw:0,0 out.wav"
com_lame = "lame -b 320 out.wav question-%d.mp3" % rec_num
com_move = "mv question-%d.mp3 %s" % (rec_num, recordingsFolder)
com_play = "mpg123 %s/question-%d.mp3" % (recordingsFolder, rec_num)
com_kill = "killall -KILL arecord"
com_delete = "rm %s" % recordingsFolder

def getRecNum():
	path, dirs, files = os.walk(recordingsFolder).next()
	return len(files)

def folderCheck():
	#Make the downloads folder if doesn't exist
    try:
		os.makedirs(recordingsFolder)
    except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

def uploadQuestion(localPath):
	print "Uploading " + localPath
	with open(localPath, 'rb') as payload:
		files = {"recording" : payload}
		res = requests.post(serverAddress + "Question/upload", files = files)
		
		if res.status_code == 200:
			print "UPLPOAD RETURN: " + str(res.json())
			subprocess.call(['mplayer', thisDir + "/success.mp3"])
			return True
		else:
			print "Upload failed!!"
			return False

def sendQuestion():
	global rec_num
	print "Start SERVER THREAD"
	while True:
		rec_num = getRecNum()
		if rec_num > 0:
			print "[SERVER] %d recordings to upload" % rec_num
			path, dirs, files = os.walk(recordingsFolder).next()
			for file in files:
				localPath = recordingsFolder + "/" + file
				isUploaded = uploadQuestion(localPath)
				# delete file if it was uploaded
				if isUploaded:
					fileDelete = com_delete + "/" + file
					subprocess.call(fileDelete, shell=True)
					print "%s deleted" % file
			# update number of recordings in folder
			rec_num = getRecNum()

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
	# move mp3 to Recordings-folder
	subprocess.call(com_move, shell=True)
	# play message
	subprocess.call(com_play, shell=True)

try:
	print "*** INTIALISING ***"
	# initialising GPIO + pins + states
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(gBut, GPIO.IN, GPIO.PUD_UP)
	GPIO.setup(gLed, GPIO.OUT)
	butState = 1
	ledState = False
	
	folderCheck()
	
	# get number of recordings in folder
	rec_num = getRecNum()
	print "rec_num: %d" % rec_num
	
	# check for new questions to upload in separate thread 
	serverThread = threading.Thread(name="moanServer", target = sendQuestion)
	serverThread.setDaemon(True)
	serverThread.start()
	
	# listen for button presses
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
					subprocess.call(['mplayer', thisDir + "/start.mp3"])
					GPIO.output(gLed, GPIO.HIGH)
					print "on"
					# start recording
					pid = record_message()
				ledState = not(ledState)
		butState = but
		sleep(0.1)
	
finally:
	GPIO.cleanup()
	subprocess.call(['mplayer', thisDir + "/error.mp3"])
