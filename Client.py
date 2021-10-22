from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		# Initialize the GUI
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		# Input from user
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		# Parameters
		self.rtspSeq = 0 # CSeq
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0 # seqnum of Rtp packet

	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)

		# Create Play button
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)

		# Create Pause button
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)

		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)

	# Setup basic operations
	# Send request -> get response (if the command is PLAY -> there will be responses) -> Display
	def setupMovie(self):
		"""Setup button handler."""
	#TODO

	def exitClient(self):
		"""Teardown button handler."""
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
	#TODO

	def playMovie(self):
		"""Play button handler."""
	#TODO
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	#
	def listenRtp(self):
		"""Listen for RTP packets."""
		#TODO

	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO

	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		# self.openRtpPort() ?
		# self.rtspSocket.connect((self.serverAddr, self.serverPort)) ?
	#TODO

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""
		# requestCode is the method name (SETUP,PLAY,...)
		# Return the response message code
		#-------------
		# TO COMPLETE
		#-------------

	#  Operations when receive a package
	def recvRtspReply(self):
		"""Receive RTSP reply from the server.
			Return the data (response or RtpPacket)"""
		return self.rtspSocket.recv(256)

	#  Use for response message
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server.
			slpit the response into line (an array of line)"""
		return data.split('\n')

	# Use for Rtp packet (in play)
	def parseRtpPacket(self, data):
		""" Decode the Rtp packet
			Change appropriate parameters
			Return the video data"""
		rtpPacket = RtpPacket()
		rtpPacket.decode(data)
		self.frameNbr = rtpPacket.seqNum()

		return rtpPacket.getPayload()

	#  Initialize the socket
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.rtspSocket.settimeout(0.5)


	#  Additional handler
	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO

		# auto TEARDOWN the session when the user explicily close the window -> Display a messagebox