from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    SWITCH = 3
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    DESCRIBE = 4

    # Use for analyze
    startClock = 0
    sumOfTime = 0
    sumData = 0
    packetLoss = 0
    stop = True

    describeState = False
    # Initiation..

    def __init__(self, master, serveraddr, serverport, rtpport):
        # File list
        self.fileList = ["movie.Mjpeg", "movie2.Mjpeg"]
        # Initialize the GUI
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        # Input from user
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = ''
        # Parameters
        self.rtspSeq = 0  # CSeq
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0  # seqnum of Rtp packet
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.timeInterval = 0
        self.isUpTime = 1
        self.isLost = 0

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI

    def createWidgets(self):
        """Build GUI."""
        self.master.configure(bg='black')
        # Create Play button
        self.start = Button(self.master, activeforeground="#00B49D", activebackground="#00B49D", fg="#00B49D",
                            highlightbackground="#00B49D", highlightthickness=1,
                            height=2, width=12, padx=5, pady=10)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=1, padx=5, pady=0)

        # Create Pause button
        self.pause = Button(self.master, activeforeground="#3CB9FC", activebackground="#3CB9FC", fg="#3CB9FC",
                            highlightbackground="#3CB9FC", highlightthickness=1,
                            height=2, width=12, padx=5, pady=10)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=5, pady=0)

        # Create Teardown button
        self.teardown = Button(self.master, activeforeground="#fc7400", activebackground="#fc7400", fg="#fc7400",
                               highlightbackground="#fc7400", highlightthickness=1,
                               height=2, width=12, padx=5, pady=10)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=3, padx=5, pady=0)

        #Create Describe Button
        self.setup = Button(self.master, activeforeground = "#9D72FF", activebackground = "#9D72FF", fg = "#9D72FF", highlightbackground= "#9D72FF", highlightthickness= 1,
        height = 2, width=12, padx=5, pady=10)
        self.setup["text"] = "Describe"
        self.setup["command"] = self.describe
        self.setup.grid(row=2, column=0, padx=5, pady=0)

        # Create a label to display the movie
        self.label = Label(self.master, width=60, height=20)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=2)

        # Create status bar for time line 
        self.status_bar = Label(self.master, text = '--:--', width=60, height=1, bd = 1, relief=GROOVE, anchor = E)
        self.status_bar.grid(row=1, columnspan=4, sticky=W + E + N + S, padx=5, pady=2)


        # Create listing panel
        self.panel = Listbox(self.master, height=26)
        self.panel.grid(row=0, rowspan=3, column=4, padx=1, pady=1)
        self.panel.bind('<<ListboxSelect>>', self.switchMovie)
        for item in range(len(self.fileList)):
            self.panel.insert(END, self.fileList[item])
            self.panel.itemconfig(item, bg="#bdc1d6")
            # Setup basic operations
        # Send request -> get response (if the command is PLAY -> there will be responses) -> Display

    def switchMovie(self, event):
        """Setup button handler."""
        # TODO
        self.fileName = str(self.panel.get(ANCHOR))
        if self.state == self.INIT:
            self.timeInterval = 0
            self.sendRtspRequest(self.SETUP)
            return
        self.timeInterval = 0
        self.state = self.SWITCH
        self.sendRtspRequest(self.TEARDOWN)
        self.sendRtspRequest(self.SETUP)
        self.state = self.READY

    def exitClient(self):
        """Teardown button handler."""
        # TODO
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui 
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
        except:
            print("No cache file to delete.")
        if not self.stop:
            self.sumOfTime += time.time() - self.startClock
        if self.sumOfTime>0:
            print('-'*40)
            print("\nAnalyze Statistics:")
            rateData = float(int(self.sumData)/int(self.sumOfTime))
            print("\nVideo Data Rate: " + str(rateData))
            rateLoss = float(self.packetLoss/self.frameNbr)
            print("\nRTP Packet Loss Rate: " + str(rateLoss) + "\n")
            print('-'*40)

    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)
            self.isUpTime = 0

    def describe(self):
        """Describe button handler."""
        if self.describeState:
            self.sendRtspRequest(self.DESCRIBE)

    def playMovie(self):
        """Play button handler."""
        # TODO
        if self.state == self.READY:
            self.describeState = True
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)
            self.timeLastPlay = time.time()
            self.updateBar()



    #for display Current time
    def updateBar(self):
        self.converted_timeInterval = time.strftime('%M:%S', time.gmtime(self.frameNbr * 0.05))
        self.converted_timeLength = time.strftime('%M:%S', time.gmtime(500 * 0.05))
        self.status_bar.config(text= self.converted_timeInterval + " / " + self.converted_timeLength)
        
        self.status_bar.after(1, self.updateBar)
        

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    def listenRtp(self):
        """Listen for RTP packets."""
        self.startClock = time.time()
        self.stop = False
        # TODO
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:                    
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    self.sumData += len(data)
                    curFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(curFrameNbr))
                    try:
                        if (self.frameNbr + 1) != curFrameNbr:
                            self.packetLoss += 1
                            print("\nFound the Packet Loss")
                    except:
                        print("segNum() error\n")
                        traceback.print_exc(file=sys.stdout)

                    if curFrameNbr > self.frameNbr: #Discard the late packet
                        self.frameNbr = curFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
                      
            except:
                print("No data received")
                self.sumOfTime += time.time() - self.startClock
                self.stop = True
                #stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                #receive ACK for TEARDOWN request,
                #close the RTP socket
                if self.teardownAcked == 1:
                    try:
                        self.rtpSocket.shutdown(socket.SHUT_RDWR)
                        self.rtpSocket.close()
                    finally:
                        break
        self.sumOfTime += time.time() - self.startClock
        self.stop = True

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
        self.label.configure(image=photo, height=288)
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
        if requestCode == self.SETUP and (self.state == self.INIT or self.state == self.SWITCH):
            threading.Thread(target=self.recvRtspReply).start()
            # update RTPS sequence number
            self.rtspSeq = 1

            # write the RTPS request to be sent.
            request = "SETUP " + self.fileName + " RTPS/1.0\nCseq: " + str(
                self.rtspSeq) + "\nTransport: RTP/UDP; clent_port= " + str(self.rtpPort)
            self.rtspSocket.send(request.encode("utf-8"))

            # keep track of the sent request
            self.requestSent = self.SETUP

        # PLAY request
        elif requestCode == self.PLAY and self.state == self.READY:
            # update RTPS sequence number
            self.rtspSeq += 1

            # write the RTPS request to be sent.
            request = "PLAY " + str(self.fileName) + " RTPS/1.0\nCseq: " + str(self.rtspSeq) + "\nSession: " + str(
                self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))

            # keep track of the sent request
            self.requestSent = self.PLAY

        # PAUSE request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # update RTPS sequence number
            self.rtspSeq += 1

            # write the RTPS request to be sent.
            request = "PAUSE " + str(self.fileName) + " RTPS/1.0\nCseq: " + str(self.rtspSeq) + "\nSession: " + str(
                self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))

            # keep track of the sent request
            self.requestSent = self.PAUSE

        # TEARDOWN request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(
                self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN

        elif requestCode == self.DESCRIBE:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "DESCRIBE " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId)
            self.rtspSocket.send(request.encode("utf-8"))
            self.requestSent = self.DESCRIBE

        else:
            return

        # send the RTSP request using rtspSocket

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
