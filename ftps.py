import socket
import pickle
from bidict import bidict

HOST = '127.0.0.1'       #localhost
PORT = 5001              # Arbitrary non-privileged port

#Global variable for the client-side DGRAM socket  
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#Function which calls the appropariate helper functions to complete tasks
def executeTask(client_addr, data, availableFiles):
	if(data == "list"):
                #Send the list of the files which are the keys in the avaiableFiles bidict    
		if list(availableFiles.keys()):
			packet = pickle.dumps(list(availableFiles.keys()))
			server_socket.sendto(packet, client_addr)
		else:
			server_socket.sendto(b"No available files", client_addr)
	elif(data == "sharing"):
		#Get list of files being shared
		sharedFiles, addr = server_socket.recvfrom(1024)
		sharedFiles = pickle.loads(sharedFiles)
		if(client_addr == addr):
			#Add the files to the approriate tuple in the availableFiles bidict
			if(client_addr in availableFiles.values()):
				files = availableFiles.inverse[client_addr]
				files = files + tuple(sharedFiles)
				availableFiles.inverse[client_addr] = files
			else:
				availableFiles[tuple(sharedFiles)] = client_addr
	elif(data == "search"):
		#Get file to be searched from client
		fName, addr = server_socket.recvfrom(1024)
		fName = fName.decode()
		if(client_addr == addr):
			#Look through all the connections in the bidict and see if any of them
			#have the file being searched for in their tuple
			for conn in availableFiles.values():
				if(fName in availableFiles.inverse[conn]):
					if(conn != client_addr):
						packet = fName + " is available for download"
					else: 
						packet = "You own the file"
					server_socket.sendto(packet.encode(), client_addr)
					return;
			server_socket.sendto(b"File does not exist", client_addr)
	elif(data == "request"):
		#Get request file name
		fName, addr = server_socket.recvfrom(1024)
		ownerConn = None
		if(client_addr == addr):
			#Look to see if a client has the file being searched for
			for conn in availableFiles.values():
				if(conn != client_addr and fName.decode() in availableFiles.inverse[conn]):
					#Make note of that connection to then send back to the client
					ownerConn = conn
					break
			if(ownerConn != None):
				server_socket.sendto(pickle.dumps(ownerConn), client_addr)
			else:
				server_socket.sendto(pickle.dumps(["File does not exist"]), client_addr)
	elif(data == "quit"):
		#Since client quit, other clients can't access their files
		if(client_addr in availableFiles.inverse):
			del availableFiles.inverse[client_addr]
#Main function
def main():
	#A bidirectional dictionary for connecting usernames and socket connection
	availableFiles = bidict()
	try:
		#Configure server socket to bind to the HOST and PORT
		server_socket.bind((HOST, PORT))
		#Allow socket to reuse address
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	except socket.error:
		print("Failed to create socket")
		sys.exit()
	#Continuously check to see if any data is being sent to server
	while 1:
		try:
			data, client_addr = server_socket.recvfrom(1024)
			if data:
				data = data.decode()
				#Execute proper task
				executeTask(client_addr, data, availableFiles)		
		except ConnectionResetError:
			server_socket.close()
				
if __name__ == "__main__":
	main()
