import os
import errno
import requests
import threading
from datetime import datetime
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
com_record = "arecord --duration=30 -f dat -r 48000 -D plughw:0,0 out.wav"
com_lame = "lame -b 320 out.wav question-%d.mp3" % rec_num
com_move = "mv question-%d.mp3 %s" % (rec_num, recordingsFolder)
com_play = "mpg123 %s/question-%d.mp3" % (recordingsFolder, rec_num)
com_kill = "killall -KILL arecord"
com_delete = "rm %s" % recordingsFolder

playingAudio = False
lock = threading.Lock()

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
			print "UPLOAD RETURN: " + str(res.json())
			return True
		else:
			print "Upload failed!!"
			return False

def sendQuestion():
	global rec_num
	global playingAudio
	global lock
	
	print "Waiting for uploads"

        shouldPlayMessage = False
	
	while True:
		rec_num = getRecNum()

                with lock:
                        if not playingAudio and shouldPlayMessage:
                                shouldPlayMessage = False
                                subprocess.call(['mplayer', thisDir + "/success.mp3"])
                                
		if rec_num > 0:
			print "[SERVER] %d recordings to upload" % rec_num
			path, dirs, files = os.walk(recordingsFolder).next()
			for file in files:
				localPath = recordingsFolder + "/" + file
				isUploaded = uploadQuestion(localPath)
				shouldPlayMessage = isUploaded
				# delete file if it was uploaded
				if isUploaded:
					fileDelete = com_delete + "/" + file
					subprocess.call(fileDelete, shell=True)
					print "%s deleted" % file
			# update number of recordings in folder
			rec_num = getRecNum()

                sleep(0.2)

def play_it(mp3file):
	com_playfile = "mpg123 %s" % mp3file
	subprocess.call(com_playfile, shell=True)

def record_message():
	return subprocess.Popen(com_record, shell=True)

def process_recording(pid):
        global playingAudio
        global lock
        
	# stop recording
	pid.terminate()
	pid.kill()
	subprocess.call(com_kill, shell=True)
	print "Kill Kill Kill!"
	# convert wav into mp3 
	subprocess.call(com_lame, shell=True)
	# move mp3 to Recordings-folder
	subprocess.call(com_move, shell=True)

        with lock:
                playingAudio = True
                # play message
                subprocess.call(com_play, shell=True)
                playingAudio = False

try:
	print "*** INTIALISING ***"
	# initialising GPIO + pins + states
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(gBut, GPIO.IN, GPIO.PUD_UP)
	GPIO.setup(gLed, GPIO.OUT)
	butState = 1
	ledState = False
        timeStarted = datetime.now()
	
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

                if ledState and (datetime.now() - timeStarted).seconds > 30:
                        print "Time's up! Finishing recording"
                        GPIO.output(gLed, GPIO.LOW)
                        process_recording(pid)
                        ledState = not(ledState)
                        
		if but != butState:
			if but == 0:
				# if button is pressed
				if ledState:
					GPIO.output(gLed, GPIO.LOW)
					print "off"
					# stop the recording and process the audio file
					process_recording(pid)
				else:
                                        with lock:
                                                playingAudio = True 
                                                subprocess.call(['mplayer', thisDir + "/start.mp3"])
                                                playingAudio = False
                                                
					GPIO.output(gLed, GPIO.HIGH)
					print "on"
					# start recording
					timeStarted = datetime.now()
					pid = record_message()
				ledState = not(ledState)
		butState = but
		sleep(0.1)
except Exception:
        subprocess.call(['mplayer', thisDir + "/error.mp3"])
finally:
	GPIO.cleanup()
