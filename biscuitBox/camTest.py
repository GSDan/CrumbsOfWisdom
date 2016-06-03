from PIL import Image, ImageEnhance
import picamera
import subprocess

camera = picamera.PiCamera()

subprocess.call(['mplayer', "camera-snap.wav"])

camera.sharpness = 30
camera.contrast = 100
camera.saturation = -100
camera.hflip = True
camera.vflip = True

camera.capture('image.jpg')

original = Image.open("image.jpg")
contrast = ImageEnhance.Contrast(original)
original = contrast.enhance(3)

width, height = original.size   # Get dimensions
left = int(width/3.3)
top = height/6
right = int(width - width/3.3)
bottom = height - height/6
original.crop((left, top, right, bottom)).save("image.jpg")
