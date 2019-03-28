#!/usr/bin/python3

# Student name and No.:
# Student name and No.:
# Development platform:
# Python version:
# Version:


from tkinter import *
import sys
import socket
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
s = socket.socket()


#
# Function to set up connection
#
def connectTCP():
	# create socket and bind
	# s = socket.socket()
	try:
		s.bind(('', myPort))
	except socket.error as err:
		print("Socket bind error: ", err)
		sys.exit(1)

	# try connecting to room server
	try:
		s.connect((rmAddr,rmPort))
	except socket.error as err:
		print("Socket accept error: ", err)
		sys.exit(1)
	return

#
# Function to send Join request
#
def joinRequest():
	smsg = "J:"+roomname+":"+username+":"+s.getsockname()[0]+":"+str(s.getsockname()[1])+"::\r\n"
	CmdWin.insert(1.0, "\n[TESTING ONLY] joinRequest(): "+smsg)
	s.send(smsg.encode())

	# receive respond from Room sever, max size 100 (?)
	try:
		rmsg = (s.recv(100)).decode("ascii")
	except socket.error as err:
		print("Socket recv error: ", err)
		sys.exit(1)

	# parse respond
	results = rmsg.split(":")
	return results

#
# Function to updateMember
#
def updateMember(newhash):
	if (roomhash != newhash):
		CmdWin.insert(1.0, "\n[TESTING ONLY] updateMember(): new member joined")
		roomhash = newhash



def keepAlive():
	print("keepalive at", time.ctime())
	results = joinRequest()
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

	if input == "":
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
		connectTCP()

	# send LIST request to Room server
	smsg = "L::\r\n"
	s.send(smsg.encode())

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

# TODO  Stop user already in a chat room to enter chat room again
# TODO  StayAlive
def do_Join():
	#changing global variable chatroom
	global roomhash
	global roomname

	CmdWin.insert(1.0, "\n[Testing] Joined pressed, chatroom ="+str(roomhash))

	# esablish connection if there isnt one
	if (s.getsockname() == ("0.0.0.0",0)):
		connectTCP()

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
			# send JOIN request to Room server
			roomname = input
			results = joinRequest()

			# interpret respond
			if (results[0] == 'M'):

				# successfully joined, set chatroom as the chatroom hash, and start keepAlive in 20s
				CmdWin.insert(1.0, "\nKeepalive thread - Start execution")
				threading.Timer(20, keepAlive).start()

				roomhash=results[1]
				CmdWin.insert(1.0, "\n[TESTING ONLY] initial room hash:" +str(roomhash))

				#Establish a forward link [still working]
				CmdWin.insert(1.0, "\n[TESTING ONLY] member size:" +str((len(results)-4)/3))
				gList=[]

				# for each member, calculate Hash ID then store info in gList as tuple(hash, name, addr, port)
				for i in range(0, int((len(results)-4)/3)):
					name = results[(i*3)+2]
					addr = results[(i*3)+3]
					port = results[(i*3)+4]
					hash = sdbm_hash(name+addr+port)

					CmdWin.insert(1.0, "\n[TESTING ONLY] [i]="+str(i)+" name="+name+" addr="+addr+" port="+port+" hash="+str(hash))

					gList.append((hash, name, addr, port))

				CmdWin.insert(1.0, "\n[TESTING ONLY] Before sort: gList="+str(gList))

				# sort list according to ascending order of memebr hash
				gList.sort(key = lambda t: int(t[0]))

				CmdWin.insert(1.0, "\n[TESTING ONLY] After sort: gList="+str(gList))




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
