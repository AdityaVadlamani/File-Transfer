import socket
from os import system, name
import pickle
import select
import sys

HOST = '127.0.0.1' 	#localhost
PORT = 5001		#Arbitary non-priveleged port
ADDR = (HOST, PORT)	#Variable to store (HOST, PORT) tuple

#Global variable for the client-side DGRAM socket  
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#Function which clears the terminal window
def clear(): 
    if name == 'nt': 
        _ = system('cls') 
    else: 
        _ = system('clear') 

#Function which shares the file names with the server
def Share():
	#Put all file names in a list
	listOfFiles = []
	n = int(input("How many files do you have to share: "))
	print("Enter the name of each file on a new line: ")
	for i in range(0, n):
		f = input()
		listOfFiles.append(f)

	#Tell the server you are about to send a list of files
	client_socket.sendto(b"sharing", ADDR)
	#Send the list to the server
	client_socket.sendto(pickle.dumps(listOfFiles), ADDR)

#Function which lists files available for download
def List():
	#Send a request to server and get response back
	client_socket.sendto(b"list", ADDR)
	data, addr = client_socket.recvfrom(2048)
	
	#Output the list of files and remove duplicates
	try:
		availableFiles = list(pickle.loads(data))
		allFiles = tuple()
		for f in availableFiles:
			allFiles += f
		allFiles = list(dict.fromkeys(list(allFiles)))
		print("\tAvailable files: ")
		print("\t-----------------")
		for f in allFiles:
			print("\t    " + f)
	except:
		print(data.decode())

#Function which allows you to search for a file
def Search():
	f = input("What file are you looking for? ")
	#Tell server you want to search for a file
	client_socket.sendto(b"search", ADDR)
	#Tell server the name of the file
	client_socket.sendto(f.encode(),ADDR)
	#Get response and print it to the screen
	resp, addr = client_socket.recvfrom(1024)
	print(resp.decode())

#Function which allows you to request a download a file
def RequestDownload():
	fName = input("What file do you want to download? ")
	#Tell the server you want to request a file for download
	#giving the file name
	client_socket.sendto(b"request", ADDR)
	client_socket.sendto(fName.encode(), ADDR)
	#The server will send back either a message saying the file
	#does not exist, or it will send the address of the first client
	#who has it
	resp, addr = client_socket.recvfrom(1024)
	if(pickle.loads(resp)[0] == "File does not exist"):
		print(resp.decode())
		return
	fileOwnerAddr = pickle.loads(resp)

	#Send the owner of the desired file a request 
	client_socket.sendto(b"request", fileOwnerAddr)
	#Wait for an ACK back
	resp, addr = client_socket.recvfrom(1024)
	if(resp.decode() == "ACK"):
		#Open file for writing
		f = open(fName, "wb")
		#Send the file name to owner and wait for data
		client_socket.sendto(fName.encode(), fileOwnerAddr)
		#The data will be send in 2K byte chunks until the client_socket
		#gets no new data after 2 secs, at which point it will stop waiting
		resp,addr = client_socket.recvfrom(2048)
		try:
			while(resp):
				f.write(resp)
				client_socket.settimeout(2)
				resp,addr = client_socket.recvfrom(2048)
		except socket.timeout:
			f.close()
			print("Download completed.")

#Function which handles requests for files
def RespondToDownloads():
	#Check if the client_socket as something to read for 1 second
	read, write, error = select.select([client_socket],[],[], 1)
	#If so, read what was sent and check if it was a "request"
	if(client_socket in read):
		resp, addr = client_socket.recvfrom(1024)
		if(resp == b"request"):
			#Send back an ACK
			client_socket.sendto(b"ACK", addr)
			#Wait for fileName
			fName, addr = client_socket.recvfrom(1024)
			#Open file for reading and send 2K byte size chunks to the
			#requestor until the end of file is reached
			f = open(fName.decode(), "rb")
			try:
				data = f.read(2048)
				while (data):
					if(client_socket.sendto(data, addr)):
						data = f.read(2048)
			except IOError: 
				print("File not accessible")
			finally:
				f.close()
#Function to quit client
def Quit():
	client_socket.sendto(b"quit", ADDR)
#Function which prints what the user can do
def Menu():
	print('  What you can do:  ')
	print('------------------------')
	print('(a) Share a file')
	print('(b) List files available for download')
	print('(c) Search for a file')
	print('(d) Download a file')
	print('(e) Quit program\n')
	
#Main function
def main(): 
	print("  Welcome to Aditya's File Sharing service!")
	print("--------------------------------------------------\n")
	
	#Try statement to catch any possible EOFErrors from input() calls
	try:	
		Menu()
		choice = input('What would you like to do?')
		#Loop until requested to quit
		while 1:
			#Based on the choice, do the appropriate action
			if(choice.lower().strip() == 'a'):
				Share()
				validChoice = True
			elif(choice.lower().strip() == 'b'):
				List()
				validChoice = True
			elif(choice.lower().strip() == 'c'):
				Search()
				validChoice = True
			elif(choice.lower().strip() == 'd'):
				RequestDownload()
				validChoice = True
			elif(choice.lower().strip() == 'e'):
				Quit()
				break
			elif(choice != ''):
				validChoice = False	
			choice = ''
			#If the choice was valid ask or another, else ask them to fix choice
			if(validChoice):
				print('What would you like to do?')
				#While the user hasn't entered anything
				while (choice == ''):
					#Check if the user typed something
					i, o, e = select.select([sys.stdin],[],[], 2)
					#If so, that is now their choice, otherwise
					#check if anyone wants to download a file you own
					if(sys.stdin in i): 
						choice = sys.stdin.readline()
					else:
						RespondToDownloads()
			else:
				print("\nPlease enter a valid option:")
				#Same logic as above
				while (choice == ''):
					i, o, e = select.select([sys.stdin],[],[], 2)
					if(sys.stdin in i):
						choice = sys.stdin.readline()
					else:
						RespondToDownloads()
	#If any EOFErrors occur print the error message	
	except EOFError as e: print(e)
	finally:
		client_socket.close()
		clear()
if __name__ == "__main__":
	main()
