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
# rmAddr = str(sys.argv[1])
# rmPort = int(sys.argv[2])
myPort = int(sys.argv[3])
username = ""
roomname = ""
roomhash = 0
myHashID = 0
connected = 0
fwdLink = ()
# storing list of backward link as tuple: (socket, (username, IP, Port))
bwdLinks=[]
msgID = 0
gList=[]
s = socket.socket()
f = socket.socket()
b = socket.socket()


#
# Function to boardcast message to all backward links, used by do_send() and listen_backward_Message()
#
def send_forward_Message(smsg):
	print("do_Send: send message via forward link:", smsg)
	try:
		f.send(smsg.encode("ascii"))
	except socket.error as err:
		print("[Send] Message cannot be boardcasted: ", err)
	return

#
# Thread to listen on backward links on incoming message, called by p2p_handshake
# Messages received on backward link are only directed to forward link
#
def listen_backward_Message(peer):
	print("[System] Listening to incoming message")
	while (True):
		# receive message boardcast from peer, max size 100 (?)
		try:
			rmsg = (peer.recv(100)).decode("ascii")

			if rmsg == "":
				print ("[message listener] backward link is broken")
				#TODO logic to remove this backward link
				break
			else:
				print("Received message:"+str(rmsg))
				MsgWin.insert(1.0, "\nReceived message:"+str(rmsg))
				# direct message to backward links
				send_forward_Message(rmsg)
				print("[backward link] Connection state: ", peer)
		except socket.error as err:
			print("[backward link] Socket recv error: ", err)
			break
	return

#
# Thread for peer-to-peer handshake with incoming connection, called by incoming_TCP()
#
def p2p_handshake(client):
	peer, conn = client

	# receive respond from peer, max size 100 (?)
	try:
		rmsg = (peer.recv(100)).decode("ascii")
	except socket.error as err:
		print("[p2p_handshake] Socket recv error: ", err)
		return

	# parse respond
	results = rmsg.split(":")
	print("[p2p_handshake] receive P2P handshake Request from ", results[2])

	if results[0] == 'P':
		# Check if the chatroom is my connected chatroom
		if results[1] != roomname :
			print("[p2p_handshake] P2P handshake Request is not from my chatroom, reject connection")
			peer.close()
			return

		# Logic to check if the peer is in the member list
		# recall gList structure: [tuple(hash, username, ip, port)]
		if any(ip[2] == results[3] for ip in gList) and any(port[3] == results[4] for port in gList) :
			print ("[p2p_handshake] this peer is known in member list, accept connection")
		else:
			# send Join request and update member list, then check again
			members = join_Request(roomname)
			update_Member(members)

			if any(ip[2] == results[3] for ip in gList) and any(port[3] == results[4] for port in gList) :
				print ("[p2p_handshake] this peer is known in member list, accept connection")
			else:
				print ("[p2p_handshake] this peer is not known in member list, reject connection")
				peer.close()
				return

		# send P2P handshake respond to peer
		smsg = "S:"+str(msgID)+"::\r\n"
		peer.send(smsg.encode("ascii"))
		print("[p2p_handshake] sent out P2P Respond to", results[2])

		# store as tuple (user name, IP, port)
		memberinfo = (results[2], results[3], int(results[4]))

		# Add the link to list of backward links
		bwdLinks.append((peer, memberinfo))
		CmdWin.insert(1.0, "\n"+results[2]+" has linked to me")
		print("[p2p_handshake] "+results[2]+" has linked to me")

		# Call new thread to listen on incoming message from this backward links
		t=threading.Thread(target=listen_backward_Message,args=(peer,))
		t.start()

	else:
		# if encounters error, print error message
		print ("[p2p_handshake] unable to recognise message")

#
# Thread for accepting incoming connection as backward links, called by do_Join()
#
def incoming_TCP():
	CmdWin.insert(1.0, "\nListening to incoming TCP connection for p2p handshake")
	while (True):
		client = b.accept()
		newbk=threading.Thread(target=p2p_handshake,args=(client,))
		newbk.start()

#
# Function to boardcast message to all backward links, used by do_send() and listen_forward_Message()
#
def send_backward_Message(smsg):
	print("do_Send: send message:", smsg)

	# send message to all backwardLink
	print("do_Send: my backward link:", len(bwdLinks))
	for i in range (0, len(bwdLinks)):
		peer = bwdLinks[i][0]
		try:
			peer.send(smsg.encode("ascii"))
		except socket.error as err:
			print("[Send] Message cannot be boardcasted: ", err)
	return

#
# Thread to listen on forward link on incoming message, called by connect_Room()
# Messages received on forward link are only directed to backward link
#
def listen_forward_Message():
	print("[System] Listening to incoming message")
	peer = fwdLink[0]
	peer.setblocking(1)

	while (True):
		# receive message boardcast from peer, max size 100 (?)
		try:
			rmsg = (peer.recv(100)).decode("ascii")
			if rmsg == "":
				print ("[message listener] forward link is broken, re-establish forward link to connect to room")
				connect_Room()
				break
			else:
				MsgWin.insert(1.0, "\nReceived message:"+str(rmsg))
				# direct message to backward links
				send_backward_Message(rmsg)
		except socket.error as err:
			print("[message listener] Forward link socket recv error: ", err)
			break
	return

#
# Function connect room by establishing forward link, called by do_Join() and update_Member()
#
def connect_Room(results):
	global fwdLink
	global connected
	global f

	memberSize = len(gList)

	if memberSize == 1:
		CmdWin.insert(1.0, "\nForward link is not established as you are the only member")
		connected = 1
		return
	else:
		# sort list according to ascending order of memebr hash
		gList.sort(key = lambda t: int(t[0]))

		# locate this program's index on the sorted list, set start as its next
		start = (([x[0] for x in gList].index(myHashID))+1) % len(gList)

		# bind socket for forward link
		try:
			f.bind(('', 0))
		except socket.error as err:
			CmdWin.insert(1.0, "\n Cannot be linked to the group, try again in")
			print("[P2P] Socket bind error: ", err+" try again in")
			# TODO try forward link later
			return

		while gList[start][0] != myHashID:
			# logic to check if backward link from this peer exists
			if any(ip[1][1] == gList[start][2] for ip in bwdLinks) and any(port[1][2] == gList[start][3] for port in bwdLinks):
				print ("[P2P] This peer has a backward link to me already")
				start = (start + 1) % len(gList)
			else:
				try:
					f.connect((gList[start][2],int(gList[start][3])))
				except socket.error as err:
					print("[P2P] Socket accept error: ", err)

				#run Peer-to-peer handshaking, send request to peer
				try:
					smsg = "P:"+roomname+":"+username+":"+f.getsockname()[0]+":"+str(myPort)+":"+str(msgID)+"::\r\n"
					f.send(smsg.encode("ascii"))
					f.setblocking(0)
					ready = select.select([f], [], [], 8)

					if ready[0]:
						rmsg = (f.recv(100)).decode("ascii")

						# store as tuple (f, (username, IP, port))
						memberinfo = (gList[start][1], gList[start][2], gList[start][3])
						fwdLink = (f, memberinfo)

						print("[P2P] P2P handshaking success, linked to the group - via "+gList[start][1])
						print("[testing] forwardLink:"+str(fwdLink))
						CmdWin.insert(1.0, "\nSuccessfully linked to the group - via "+gList[start][1])
						connected = 1

						t=threading.Thread(target=listen_forward_Message,args=[])
						t.start()
						break
					else:
						# timeout or connection error
						print("[P2P] Connection error: cannot receive respond. Try forward link to next peer")
						f.close()
						start = (start + 1) % len(gList)

				except socket.error as err:
					print("[P2P] Connection error: "+err+". Try forward link to next peer")


			CmdWin.insert(1.0, "\n Cannot be linked to the group, try again in")
			print("[P2P] Cannot find any peer to P2P handshake, trying again in ")
			# TODO logic to try again

#
# Function to update members info to gList, called by do_Join() and keep_Alive()
#
def update_Member(results):
	global roomhash
	global fwdLink
	newhash = results[1]


	if (roomhash != newhash):
		print("[System] Memberlist has updated")

		# update roomhash and update gList
		roomhash = newhash
		memberSize = int(len(results)-4)/3

		#clear previous gList
		gList.clear()

		# for each member, calculate Hash ID then store info in gList as tuple(hash, name, addr, port)
		for i in range(0, int(memberSize)):
			name = results[(i*3)+2]
			addr = results[(i*3)+3]
			port = results[(i*3)+4]
			hash = sdbm_hash(name+addr+port)
			gList.append((hash, name, addr, port))

		# if established a forward link
		# and forward link peer is not in new member list, establish new forward link
		if fwdLink != ():
			fwdIp = fwdLink[1][1]
			fwdPort = fwdLink[1][2]

			if any(ip[2] == fwdIp for ip in gList) and any(port[3] == fwdPort for port in gList) :
				print("[System] Foward link is still intact")
			else:
				print("[System] Forward link is broken, try to re-establish forward link")
				CmdWin.insert(1.0, "\nForward link is broken, try to re-establish forward link")
				fwdLink = ()
				connect_Room(roomname)
	return

#
# Function to send Join request, called by do_Join() and keep_Alive()
#
def join_Request(rmname):
	smsg = "J:"+rmname+":"+username+":"+s.getsockname()[0]+":"+str(myPort)+"::\r\n"
	s.send(smsg.encode())

	# receive respond from Room sever, max size 100 (?)
	try:
		rmsg = (s.recv(100)).decode("ascii")
	except socket.error as err:
		print("join_Request(): Socket recv error: ", err)
		sys.exit(1)

	# parse and return respond
	results = rmsg.split(":")
	return results

#
# keep alive thread, called by do_Join() and itself
#
def keep_Alive():
	print("keepalive at", time.ctime())
	results = join_Request(roomname)
	update_Member(results)
	threading.Timer(10, keep_Alive).start()

#
# Function for TCP connection to chat server, used by do_List() & do_Join()
#
def connect_Server():
	rmAddr = str(sys.argv[1])
	rmPort = int(sys.argv[2])

	try:
		s.bind(('', 0))
	except socket.error as err:
		print("connect_Server(): Socket bind error: ", err)
		sys.exit(1)

	try:
		s.connect((rmAddr,rmPort))
	except socket.error as err:
		print("connect_Server(): Socket accept error: ", err)
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
		connect_Server()

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
				connect_Server()

			# send JOIN request to Room server, and received parsed respond
			results = join_Request(input)

			# interpret respond
			if (results[0] == 'M'):

				# successfully joined, set roomname and myHashID
				roomname=input
				myHashID = sdbm_hash(username+s.getsockname()[0]+str(myPort))

				# called update_Member() to store member list in gList[]
				update_Member(results)

				# start keepAlive in 20s
				CmdWin.insert(1.0, "\nKeepalive thread - Start execution")
				threading.Timer(20, keep_Alive).start()

				# Establish a forward link if there is not one
				if (f.getsockname() == ("0.0.0.0",0)):
					connect_Room(results)

				# Set up listener for backward links
				try:
					b.bind(('', myPort))
				except socket.error as err:
					print("[incomingTCP listener] Socket bind error: ", err)
					sys.exit(1)

				# try connecting to room server
				try:
					b.listen(5)
				except socket.error as err:
					print("[incomingTCP listener] Socket accept error: ", err)
					sys.exit(1)
				t=threading.Thread(target=incoming_TCP,args=[])
				t.start()

			else:
				# if encounters error, print error message
				print ("[Error] ", results[1])

def do_Send():
	global msgID

	input = userentry.get()

	# ignore empty user input
	if input == "":
		return

	# send message if the chat program is connected
	if connected == 0:
		CmdWin.insert(1.0, "\nSorry you have not been connected to the chatroom network")
	else:
		msgLength = len(input)
		smsg = "T:"+roomname+":"+str(myHashID)+":"+username+":"+str(msgID)+":"+str(msgLength)+":"+input+"::\r\n"
		send_backward_Message(smsg)
		send_forward_Message(smsg)
		msgID = msgID + 1

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
