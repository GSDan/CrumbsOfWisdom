from PIL import Image, ImageEnhance
import picamera
import subprocess
import os

camera = picamera.PiCamera()

subprocess.call(['mplayer', "camera-snap.wav"])

camera.sharpness = 30
camera.contrast = 100
camera.saturation = -100
camera.rotation = 90

camera.capture('image.jpg')

original = Image.open("image.jpg")
contrast = ImageEnhance.Contrast(original)
original = contrast.enhance(3)

width, height = original.size   # Get dimensions
left = int(width/3.8)
top = int(height/12)
right = int(width - width/11)
bottom = int(height)
original.crop((left, top, right, bottom)).save("image.jpg")
#original.save("image.jpg")

thisDir = os.path.dirname(os.path.abspath(__file__))
downloadsFolder = thisDir + "/QuestionFiles"

for fn in os.listdir(downloadsFolder):
	found = False
	print "Checking file", fn