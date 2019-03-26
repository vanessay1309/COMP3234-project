#!/usr/bin/python3

# Student name and No.:
# Student name and No.:
# Development platform:
# Python version:
# Version:


from tkinter import *
import sys
import socket

#
# Global variables
#
rmAddr = str(sys.argv[1])
rmPort = int(sys.argv[2])
myPort = int(sys.argv[3])
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


#
# Functions to handle user input
#

def do_User():
	outstr = "\n[User] username: "+userentry.get()
	CmdWin.insert(1.0, outstr)
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
			# if has one or more chatroom groups
			CmdWin.insert(1.0, "\nHere are the active chatrooms:")
			for i in range(1, len(results)-2):
				CmdWin.insert(1.0, "\n\t", results[i])
		else:
			# if no chatroom group
			CmdWin.insert(1.0, "\nNo active chatrooms")
	else:
		# if encounters error
		print ("Error: ", results[1])

	CmdWin.insert(1.0, "\nConnect to server at "+s.getpeername()[0]+":"+str(s.getpeername()[1]))


def do_Join():
	CmdWin.insert(1.0, "\nPress JOIN")


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
