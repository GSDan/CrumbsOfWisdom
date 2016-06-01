# CrumbsOfWisdom
A biscuit built, tea fuelled, Raspberry Pi powered system for student advice.

The system's codebase is split into 4 sections: a program which records audio messages, a program which plays these messages and photographs written responses, a program which prints these photographs onto labels, and a simple server which stores the messages and photographs.

## AdviceServer

A simple REST service, built using Sails.js and MongoDB. Used to add and retrieve both new audio messages and photos of responses. All responses are in JSON format.

#### Routes available:

* __/Question__ Get all questions logged on the server
* __/Question/upload__ Add a new question
  * Must attach an audio file under a "recording" field
* __/Question/getNew__ Gets all questions which haven't been responded to yet

* __/Advice__ Get all advice responses logged on the server
* __/Advice/upload__ Add a new response
  * Must attach an image file under an "image" field

* __/File/Download/?fd=FD__ Retrieve a file with this file descriptor


## MoanBox

A Python script which runs on a RPi 3 hooked up to a microphone. Records students' questions with a microphone and then uploads them to the AdviceServer.

#### Main components:
* Raspberry Pi 3
* Speaker
* Microphone
* Button
* LED

## BiscuitBox

A Python script which runs on a RPi Zero embedded in a biscuit tin/box. Downloads students' questions from the AdviceServer and plays them when the enclosing box is opened (checked via a photoresistor). Written responses are then photographed upon a button press and uploaded back to the server.

#### Main components:
* Raspberry Pi Zero
* Phat DAC + speaker
* RPi night vision camera (with RPi zero flex cable)
* WiFi adapter
* Photoresistor
* Button
* LED

## PrinterBox

A Python script which runs on a RPi 3 hooked up to a Pipsta printer. Downloads the BiscuitBox's photo responses from the AdviceServer and prints them out onto sticky labels upon a button press.

#### Main components:
* Raspberry Pi 3
* Pipsta Printer
* Button