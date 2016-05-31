import os
import errno
import requests
import threading
import subprocess
import RPi.GPIO as GPIO
from time import sleep

 #GPIO pins
gBut = 7       #button
gLED = 10      #LED

downloadsFolder = "./AdviceFiles"
serverAddress = "http://46.101.42.140:1337/"

def RefreshAdvice():
    #Make the downloads folder if doesn't exist
    try:
            os.makedirs(downloadsFolder)
    except OSError as exception:
	    if exception.errno != errno.EEXIST:
		    raise

    while True:
        result = requests.get(serverAddress + "advice")

        for advice in result.json():
            localPath = os.path.join(downloadsFolder, os.path.basename(advice["filename"]))

            #Download the file if it doesn't exist locally
            if not os.path.isfile(localPath):
                    params = {"fd" : advice["filename"]}
                    r = requests.get(serverAddress + "file/download", params=params, stream=True)

                    print "DOWNLOADING:", advice["filename"]

		    with open(localPath, 'wb') as f:
			    for chunk in r.iter_content(chunk_size=1024): 
				    if chunk: # filter out keep-alive new chunks
					    f.write(chunk)
					    f.flush()
				
		    print "FINISHED:", localPath

		    subprocess.call(["python", "pipsta.py", localPath])
           
        sleep(10)


RefreshAdvice();
