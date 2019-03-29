#!/usr/bin/python3

# Student name and No.:
# Student name and No.:
# Development platform:
# Python version:
# Version:


from tkinter import *
import sys
import socket
import select
import time, threading

#
# Global variables
#
rmAddr = str(sys.argv[1])
rmPort = int(sys.argv[2])
myPort = int(sys.argv[3])
username = ""
roomname = ""
roomhash = 0
myHashID = 0
fwdLink = []
# storing list of backward link as tuple: (socket, (username, IP, Port))
bwdLinks=[]
msgID = 0
gList=[]
s = socket.socket()
f = socket.socket()
b = socket.socket()


#
# Function to set up connection to chatserver
#
def connectServer():
	try:
		s.bind(('', 0))
	except socket.error as err:
		print("connectServer(): Socket bind error: ", err)
		sys.exit(1)

	try:
		s.connect((rmAddr,rmPort))
	except socket.error as err:
		print("connectServer(): Socket accept error: ", err)
		sys.exit(1)
	return

#
# Thread function for accepting the backward link
#
def tryBackwardLink(client):
	peer, conn = client

	# receive respond from peer, max size 100 (?)
	try:
		rmsg = (peer.recv(100)).decode("ascii")
		CmdWin.insert(1.0, "\n[TESTING ONLY] received P2P handshake respond="+rmsg)
	except socket.error as err:
		print("acceptTCP(): Socket recv error: ", err)
		return

	# a tuple to store user name, IP, port
	memberinfo = ""
	# Logic to check if the peer is authenticated from room server

	#if yes send P2P handshake respond to peer (if no --> peer.close())
	smsg = "S:"+str(msgID)+"::\r\n"
	peer.send(smsg.encode("ascii"))
	CmdWin.insert(1.0, "\n[TESTING ONLY] acceptTCP(): send out respond"+smsg)

	# Add the link to list of backward links
	bwdLinks.append((peer, memberinfo))
	print("[TESTING ONLY] Backward links: ", str(bwdLinks))
	tempS = bwdLinks[0]
	print ("[TESTING ONLY] First backward link is:"+tempS.getsockname()[0]+":"+str(tempS.getsockname()[1]))
#
# Thread function for accepting incoming connection
#
def acceptTCP():
	CmdWin.insert(1.0, "\nListening to incoming TCP connection")
	while (True):
		client = b.accept()
		newbk=threading.Thread(target=tryBackwardLink,args=(client,))
		newbk.start()


#
# Function to set up listening socket for incoming TCP connection
#
def listeningSocket():
	# create socket and bind
	try:
		b.bind(('', myPort))
	except socket.error as err:
		print("Socket bind error: ", err)
		sys.exit(1)

	# try connecting to room server
	try:
		b.listen(5)
	except socket.error as err:
		print("Socket accept error: ", err)
		sys.exit(1)

	CmdWin.insert(1.0, "\n[TESTING ONLY] Set up listening socket"+b.getsockname()[0]+":"+str(b.getsockname()[1]))

	t=threading.Thread(target=acceptTCP,args=[])
	t.start()
	return

#
# Function to send Join request
#
def joinRequest(rmname):
	smsg = "J:"+rmname+":"+username+":"+s.getsockname()[0]+":"+str(myPort)+"::\r\n"
	s.send(smsg.encode())

	# receive respond from Room sever, max size 100 (?)
	try:
		rmsg = (s.recv(100)).decode("ascii")
	except socket.error as err:
		print("joinRequest(): Socket recv error: ", err)
		sys.exit(1)

	# parse and return respond
	results = rmsg.split(":")
	return results

#
# Function to establish forward link
#
def tryForwardLink(results):
	global fwdLink
	global f

	memberSize = int(len(results)-4)/3

	if memberSize == 1:
		CmdWin.insert(1.0, "\nForward link is not established as you are the only member")
		return

	else:
		# for each member, calculate Hash ID then store info in gList as tuple(hash, name, addr, port)
		for i in range(0, int(memberSize)):
			name = results[(i*3)+2]
			addr = results[(i*3)+3]
			port = results[(i*3)+4]
			hash = sdbm_hash(name+addr+port)
			gList.append((hash, name, addr, port))

		CmdWin.insert(1.0, "\n[TESTING ONLY] tryFowardLink(): Before sort: gList="+str(gList))

		# sort list according to ascending order of memebr hash
		gList.sort(key = lambda t: int(t[0]))

		CmdWin.insert(1.0, "\n[TESTING ONLY] tryFowardLink(): After sort: gList="+str(gList))

		# locate this program's index on the sorted list, set start as its next
		start = (([x[0] for x in gList].index(myHashID))+1) % len(gList)
		CmdWin.insert(1.0, "\n[TESTING ONLY] tryFowardLink(): my next index on gList="+str(start))

		# bind socket for forward link
		try:
			f.bind(('', 0))
		except socket.error as err:
			print("tryFowardLink(): Socket bind error: ", err)
			# TODO try forward link later
			return

		while gList[start][0] != myHashID:
			# TODO logic to check backward link exist


			bkLink = 0
			if bkLink:
				start = (start + 1) % len(gList)
			else:
				try:
					f.connect((gList[start][2],int(gList[start][3])))
				except socket.error as err:
					print("tryFowardLink(): Socket accept error: ", err)

				# if connection is established
				if (f.getsockname() != ("0.0.0.0",0)):
					CmdWin.insert(1.0, "\n[TESTING ONLY] TCP connection from "+f.getsockname()[0]+":"+str(f.getsockname()[1]))
					CmdWin.insert(1.0, "\n[TESTING ONLY] TCP connection to "+f.getpeername()[0]+":"+str(f.getpeername()[1])+" successed, proceed to peer to peer handshaking")

					#run Peer-to-peer handshaking, send request to peer
					smsg = "P::"+roomname+":"+username+":"+f.getsockname()[0]+":"+str(f.getsockname()[1])+":"+str(msgID)+"::\r\n"
					f.send(smsg.encode("ascii"))

					# try to receive respond from peer, set time out as 8s; if timeout try next peer
					f.setblocking(0)
					ready = select.select([f], [], [], 8)
					if ready[0]:
						rmsg = (f.recv(100)).decode("ascii")
						CmdWin.insert(1.0, "\n[TESTING ONLY] P2P handshaking success, received respond="+rmsg)
						fwdLink.append(f)
						break
					else:
						print("cannot connect to this peer, increment to next")
						f.close()
						start = (start + 1) % len(gList)
				else:
					print("cannot connect to this peer, increment to next")
					f.close()
					start = (start + 1) % len(gList)

	CmdWin.insert(1.0, "\n tryFowardLink(): after establishing, forwardlinks:"+str(fwdLink))



#
# Function to updateMember
#
def updateMember(newhash):
	global roomhash

	if (roomhash != newhash):
		CmdWin.insert(1.0, "\n[TESTING ONLY] updateMember(): member list has updated")
		roomhash = newhash

def keepAlive():
	print("keepalive at", time.ctime())
	results = joinRequest(roomname)
	updateMember(results[1])
	threading.Timer(10, keepAlive).start()

#
# This is the hash function for generating a unique
# Hash ID for each peer.
# Source: http://www.cse.yorku.ca/~oz/hash.html
#
# Concatenate the peer's username, str(IP address),
# and str(Port) to form a string that be the input
# to this hash function
#
def sdbm_hash(instr):
	hash = 0
	for c in instr:
		hash = int(ord(c)) + (hash << 6) + (hash << 16) - hash
	return hash & 0xffffffffffffffff

def do_User():
	global username
	input = userentry.get()

	if roomhash != 0:
		# prevent user from changing name
		CmdWin.insert(1.0, "\nYou cannot change your username anymore because you already joinned a chatroom")
	elif input == "":
		# handle empty input
		CmdWin.insert(1.0, "\nPlease input username before pressing user button")
	elif ':' in input:
		# handle illegal character ':'
		CmdWin.insert(1.0, "\nYou have an illegal character in your username, please input another one again ")
		userentry.delete(0, END)
	else:
		# set username
		username = input
		CmdWin.insert(1.0, "\n[User] username: "+username)
		userentry.delete(0, END)

def do_List():
	# esablish connection if there isnt one
	if (s.getsockname() == ("0.0.0.0",0)):
		connectServer()

	# send LIST request to Room server
	smsg = "L::\r\n"
	s.send(smsg.encode("ascii"))

	# receive respond from Room sever, max size 100 (?)
	try:
		rmsg = (s.recv(100)).decode("ascii")
	except socket.error as err:
		print("Socket recv error: ", err)
		sys.exit(1)

	# extract and interpret respond
	results = rmsg.split(":")
	if (results[0] == 'G'):
		if (len(results) > 3):
			# if has one or more chatroom groups, display the rooms
			for i in range(1, len(results)-2):
				CmdWin.insert(1.0, "\n\t" + results[i])
		else:
			# if no chatroom group
			CmdWin.insert(1.0, "\nNo active chatrooms")
	else:
		# if encounters error
		print ("[Error] ", results[1])

	CmdWin.insert(1.0, "\nConnect to server at "+s.getpeername()[0]+":"+str(s.getpeername()[1]))

def do_Join():
	#changing global variables
	global roomhash
	global roomname
	global myHashID

	# Check if user already joined a chatroom, reject request if so
	if (roomhash != 0):
		CmdWin.insert(1.0, "\nYour request is denied, you already joined a chatroom")
		return

	# Check if user set up username
	if (username == ""):
		CmdWin.insert(1.0, "\nPlease set up username first before joining a chat room")
		userentry.delete(0, END)
	else:
		# Check if user input chatroom name
		input = userentry.get()
		if (input == ""):
			CmdWin.insert(1.0, "\nPlease enter a name for the chatroom")
		else:
			# esablish connection if there isnt one
			if (s.getsockname() == ("0.0.0.0",0)):
				connectServer()

			# send JOIN request to Room server, and received parsed respond
			results = joinRequest(input)

			# interpret respond
			if (results[0] == 'M'):

				# successfully joined, set roomhash, roomname and myHashID
				CmdWin.insert(1.0, "\n[TESTING] join request success, recived: "+str(results))
				roomname=input
				roomhash=results[1]
				myHashID = sdbm_hash(username+s.getsockname()[0]+str(myPort))

				# start keepAlive in 20s
				CmdWin.insert(1.0, "\nKeepalive thread - Start execution")
				threading.Timer(20, keepAlive).start()

				#Establish a forward link if there is not one
				if (f.getsockname() == ("0.0.0.0",0)):
					tryForwardLink(results)

				# continue listen to incoming connection (backward links)
				listeningSocket()


			else:
				# if encounters error
				print ("[Error] ", results[1])





def do_Send():
	CmdWin.insert(1.0, "\nPress Send")


def do_Poke():
	CmdWin.insert(1.0, "\nPress Poke")


def do_Quit():
	CmdWin.insert(1.0, "\nPress Quit")
	sys.exit(0)


#
# Set up of Basic UI
#
win = Tk()
win.title("MyP2PChat")

#Top Frame for Message display
topframe = Frame(win, relief=RAISED, borderwidth=1)
topframe.pack(fill=BOTH, expand=True)
topscroll = Scrollbar(topframe)
MsgWin = Text(topframe, height='15', padx=5, pady=5, fg="red", exportselection=0, insertofftime=0)
MsgWin.pack(side=LEFT, fill=BOTH, expand=True)
topscroll.pack(side=RIGHT, fill=Y, expand=True)
MsgWin.config(yscrollcommand=topscroll.set)
topscroll.config(command=MsgWin.yview)

#Top Middle Frame for buttons
topmidframe = Frame(win, relief=RAISED, borderwidth=1)
topmidframe.pack(fill=X, expand=True)
Butt01 = Button(topmidframe, width='6', relief=RAISED, text="User", command=do_User)
Butt01.pack(side=LEFT, padx=8, pady=8);
Butt02 = Button(topmidframe, width='6', relief=RAISED, text="List", command=do_List)
Butt02.pack(side=LEFT, padx=8, pady=8);
Butt03 = Button(topmidframe, width='6', relief=RAISED, text="Join", command=do_Join)
Butt03.pack(side=LEFT, padx=8, pady=8);
Butt04 = Button(topmidframe, width='6', relief=RAISED, text="Send", command=do_Send)
Butt04.pack(side=LEFT, padx=8, pady=8);
Butt06 = Button(topmidframe, width='6', relief=RAISED, text="Poke", command=do_Poke)
Butt06.pack(side=LEFT, padx=8, pady=8);
Butt05 = Button(topmidframe, width='6', relief=RAISED, text="Quit", command=do_Quit)
Butt05.pack(side=LEFT, padx=8, pady=8);

#Lower Middle Frame for User input
lowmidframe = Frame(win, relief=RAISED, borderwidth=1)
lowmidframe.pack(fill=X, expand=True)
userentry = Entry(lowmidframe, fg="blue")
userentry.pack(fill=X, padx=4, pady=4, expand=True)

#Bottom Frame for displaying action info
bottframe = Frame(win, relief=RAISED, borderwidth=1)
bottframe.pack(fill=BOTH, expand=True)
bottscroll = Scrollbar(bottframe)
CmdWin = Text(bottframe, height='15', padx=5, pady=5, exportselection=0, insertofftime=0)
CmdWin.pack(side=LEFT, fill=BOTH, expand=True)
bottscroll.pack(side=RIGHT, fill=Y, expand=True)
CmdWin.config(yscrollcommand=bottscroll.set)
bottscroll.config(command=CmdWin.yview)

def main():
	if len(sys.argv) != 4:
		print("P2PChat.py <server address> <server port no.> <my port no.>")
		sys.exit(2)

	win.mainloop()

if __name__ == "__main__":
	main()
