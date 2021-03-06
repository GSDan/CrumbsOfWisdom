import os
import random
import errno
import requests
import threading
import subprocess
import RPi.GPIO as GPIO
from time import sleep

 #GPIO pins
gBut = 7       #button

downloadsFolder = "./AdviceFiles"
serverAddress = "http://138.68.133.209:1337/"

def RemoveUnwantedFiles(advice):
    for fn in os.listdir(downloadsFolder):
        found = False
        thisPath = os.path.join(downloadsFolder, fn)
        print "Checking downloaded file", thisPath
        for ad in advice:
            localPath = os.path.join(downloadsFolder, os.path.basename(ad["filename"]))
            if localPath == thisPath:
                found = True
                break
        if not found:
            print "Deleting", thisPath
            os.remove(thisPath)

def RefreshAdvice():
    #Make the downloads folder if doesn't exist
    try:
            os.makedirs(downloadsFolder)
    except OSError as exception:
	    if exception.errno != errno.EEXIST:
		    raise

    while True:
        
	try:
		print "Connecting"
		result = requests.get(serverAddress + "advice")
        print "Connection result: " + str(result.status_code)

        RemoveUnwantedFiles(result.json())

        for advice in result.json():
        	localPath = os.path.join(downloadsFolder, os.path.basename(advice["filename"]))
       		#Download the file if it doesn't exist locally
       		if not os.path.isfile(localPath):
           		params = {"fd" : advice["filename"]}
           		r = requests.get(serverAddress + "file/download", params=params, stream=True)

                with open(localPath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024): 
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            f.flush()
                    print "FINISHED:", localPath
            else:
                print "ALREADY CACHED", localPath

	except requests.exceptions.RequestException as e:
		print e
           
    sleep(60)

try:

        # Check the server on a separate thread
	serverPollThread = threading.Thread(name="AdviceServer", target=RefreshAdvice)
	serverPollThread.setDaemon(True)
	serverPollThread.start()
	
        #initialising GPIO + pins + states
        GPIO.setmode (GPIO.BOARD)
        GPIO.setup (gBut, GPIO.IN, GPIO.PUD_UP)
        butState = 1
        
        while True:
                but = GPIO.input (gBut)
                if but != butState:
                        if but == 1:                            
                                print "printing image"

                                if os.listdir(downloadsFolder):
                                    thisAdvice = random.choice(os.listdir(downloadsFolder))
                                    localPath = os.path.join(downloadsFolder, thisAdvice)
			
                                    subprocess.call(["python", "pipsta.py", localPath])

                                else:
                                    print "No images to print"
                                
                                sleep(2)
                                
                butState = but
                sleep (0.1)

finally:
        GPIO.cleanup
    
