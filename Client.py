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
        self.rtspSeq = 0  # CSeq
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0  # seqnum of Rtp packet
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI


    def createWidgets(self):
        """Build GUI."""
        self.master.configure(bg='black')
        # Create Setup button
        self.setup = Button(self.master, activeforeground = "#9D72FF", activebackground = "#9D72FF", fg = "#9D72FF", highlightbackground= "#9D72FF", highlightthickness= 1,
        height = 2, width=20, padx=10, pady=10)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=10, pady=10)

        # Create Play button
        self.start = Button(self.master, activeforeground ="#00B49D", activebackground = "#00B49D", fg = "#00B49D", highlightbackground= "#00B49D", highlightthickness= 1,
        height = 2, width=20, padx=10, pady=10)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=10, pady=10)

        # Create Pause button
        self.pause = Button(self.master, activeforeground = "#3CB9FC", activebackground = "#3CB9FC", fg = "#3CB9FC", highlightbackground= "#3CB9FC", highlightthickness= 1,
        height = 2, width=20, padx=10, pady=10)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=10, pady=10)

        # Create Teardown button
        self.teardown = Button(self.master, activeforeground = "#fc7400", activebackground = "#fc7400", fg = "#fc7400", highlightbackground= "#fc7400", highlightthickness= 1,
        height = 2, width=20, padx=10, pady=10)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=10, pady=10)

        # Create a label to display the movie
        self.label = Label(self.master, width=90, height=30)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=10, pady=10)

        # Setup basic operations
        # Send request -> get response (if the command is PLAY -> there will be responses) -> Display


    def setupMovie(self):
        """Setup button handler."""
        # TODO
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)


    def exitClient(self):
        """Teardown button handler."""
        # TODO
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy() # Close the gui window
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video
        except:
            print("Video was not loaded.")


    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)


    def playMovie(self):
        """Play button handler."""
        # TODO
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    def listenRtp(self):
        """Listen for RTP packets."""
        # TODO
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    curFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(curFrameNbr))

                    if curFrameNbr > self.frameNbr: #Discard the late packet
                        self.frameNbr = curFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                #stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                #receive ACK for TEARDOWN request,
                #close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        # TODO
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        # TODO
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image= photo, height= 288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
    # TODO
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
            print("Connected successfully")
        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)


    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # requestCode is the method name (SETUP,PLAY,...)
        # Return the response message code
        # -------------
        # TO COMPLETE
        # -------------
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            #update RTPS sequence number
            self.rtspSeq = 1

            #write the RTPS request to be sent.
            request = "SETUP " + str(self.fileName) + " RTPS/1.0\nCseq: " + str(self.rtspSeq) + "\nTransport: RTP/UDP; clent_port= " + str(self.rtpPort)
            self.rtspSocket.send(request.encode("utf-8"))

            #keep track of the sent request
            self.requestSent = self.SETUP

        #PLAY request
        elif requestCode == self.PLAY and self.state == self.READY:
            #update RTPS sequence number
            self.rtspSeq += 1

            #write the RTPS request to be sent.
            request = "PLAY " + str(self.fileName) + " RTPS/1.0\nCseq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))

            #keep track of the sent request
            self.requestSent = self.PLAY

        #PAUSE request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            #update RTPS sequence number
            self.rtspSeq += 1

            #write the RTPS request to be sent.
            request = "PAUSE " + str(self.fileName) + " RTPS/1.0\nCseq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))

            #keep track of the sent request
            self.requestSent = self.PAUSE

        #TEARDOWN request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN
        else:
            return

        #send the RTSP request using rtspSocket
        
        print('\nData sent:\n' + request)


    #  Operations when receive a package
    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)
            print("Receive Reply")

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    #  Use for response message


    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server.
            slpit the response into line (an array of line)"""
        print("\nData received:\n" + data)
        lines = data.split('\n')
        response_SeqNum = int(lines[1].split(' ')[1])
        response_Code = int(lines[0].split(' ')[1])

        if response_SeqNum == self.rtspSeq:
            response_session = int(lines[2].split(' ')[1])

            # Check case for SETUP
            if self.sessionId == 0:
                self.sessionId = response_session

            if response_session == self.sessionId:
                if response_Code == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        self.openRtpPort()
                    if self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    if self.requestSent == self.PAUSE:
                        self.state = self.READY
                        self.playEvent.set()
                    if self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        self.teardownAcked = 1

    #  Initialize the socket


    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        self.rtpSocket.settimeout(0.5)

        try:
            self.state = self.READY
            self.rtpSocket.bind((self.serverAddr, self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        self.pauseMovie()
        if tkinter.messagebox.askyesno("Quit message", "Do you want to quit ?"):
            self.exitClient()
        else:
            self.playMovie()
