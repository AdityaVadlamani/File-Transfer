Developer: Aditya Vadlamani

This project is for CSE 3461 with Dave Ogle.

The application was written in Python3 and makes use of both standard and non-standard libraries.

The non-standard library which I had installed for this project was the **bidict** library. To install this library I simply ran the following commands:

**First install pip if you don't have it**
	curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
	python get-pip.py

**Then install bidict**
	pip install bidict

### Some things to note about the program:
- When a task is executed on the client side there may be a slight delay that occurs as there is a non-zero timeout on all of the select calls in the client program
- ftps.py needs to be run first
