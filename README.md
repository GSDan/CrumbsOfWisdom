# CrumbsOfWisdom
A biscuit built, tea fuelled, Raspberry Pi powered system for student advice.

The system's codebase is split into 4 sections: a program which records audio messages, a program which plays these messages and photographs written responses, a program which prints these photographs onto labels, and a simple server which stores the messages and photographs.

## AdviceServer

A simple REST service, built using Sails. Used to add and retrieve both new audio messages and photos of responses. All responses are in JSON format.

### Routes available:

* __/Question__ Get all questions logged on the server
* __/Question/upload__ Add a new question
  * Must attach an audio file under a "recording" field
* __/Question/getNew__ Gets all questions which haven't been responded to yet

* __/Advice__ Get all advice responses logged on the server
* __/Advice/upload__ Add a new response
  * Must attach an image file under a "image" field

* __/Files/Download/#FD__ Retrieve a file with this file descriptor