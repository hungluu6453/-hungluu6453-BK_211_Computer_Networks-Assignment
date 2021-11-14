from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    SWITCH = 0
    READY = 1
    PLAYING = 2
    state = SWITCH

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
        self.RtpThread = 0
        self.RtspThread = 0

        self.frameNbr = 0  # seqnum of Rtp packet

        #additional
        self.isDescribeSent = False
        self.description = ''
        self.isLost = 0
        self.isNewMovie = False
        self.totalFrame = 0
        self.isPlayed = False 

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI

    def createWidgets(self):
        """Build GUI."""
        self.master.configure(bg='black')
        # Create Play button
        self.start = Button(self.master, activeforeground="#00B49D", activebackground="#00B49D", fg="#00B49D",
                            highlightbackground="#00B49D", highlightthickness=1,
                            height=3, width=10, padx=8, pady=20)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=1, padx=5, pady=0)

        # Create Pause button
        self.pause = Button(self.master, activeforeground="#3CB9FC", activebackground="#3CB9FC", fg="#3CB9FC",
                            highlightbackground="#3CB9FC", highlightthickness=1,
                            height=3, width=10, padx=8, pady=20)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=5, pady=0)

        # Create Teardown button
        self.teardown = Button(self.master, activeforeground="#fc7400", activebackground="#fc7400", fg="#fc7400",
                               highlightbackground="#fc7400", highlightthickness=1,
                               height=3, width=10, padx=8, pady=20)
        self.teardown["text"] = "Stop"
        self.teardown["command"] = self.stopMovie
        self.teardown.grid(row=2, column=3, padx=5, pady=0)

        #Create Describe Button
        self.setup = Button(self.master, activeforeground = "#9D72FF", activebackground = "#9D72FF", fg = "#9D72FF", highlightbackground= "#9D72FF", highlightthickness= 1,
        height=3, width=10, padx=8, pady=15)
        self.setup["text"] = "Describe"
        self.setup["command"] = self.describe
        self.setup.grid(row=2, column=0, padx=5, pady=0)

        # Create a label to display the movie
        self.label = Label(self.master, width=60, height=20)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=2)

        # Create status bar for time line 
        self.status_bar = Label(self.master, text = '--/--', width=60, height=1, bd = 1, relief=GROOVE, anchor = E)
        self.status_bar.grid(row=1, columnspan=4, sticky=W + E, padx=1, pady=1)

        # Create desciption for GUI
        self.description_gui = Label(self.master, text = '(^0-0^)', width=28, height=8, bd = 1, relief=GROOVE)
        self.description_gui.grid(row=1, column=4, rowspan=2, sticky=W + E + N + S, padx=1, pady=1)


        # Create listing panel
        self.panel = Listbox(self.master, width=30, height=22)
        self.panel.grid(row=0, rowspan=1, column=4, padx=1, pady=1)
        self.panel.bind('<<ListboxSelect>>', self.switchMovie)
        for item in range(len(self.fileList)):
            self.panel.insert(END, self.fileList[item])
            self.panel.itemconfig(item, bg="#bdc1d6")
            # Setup basic operations
        # Send request -> get response (if the command is PLAY -> there will be responses) -> Display

    def switchMovie(self, event):
        """Setup button handler."""
        # TODO
        #Initialize connection
        if not self.fileName:
            self.fileName = str(self.panel.get(ANCHOR))  
            self.sendRtspRequest(self.SETUP)
            return

        #Stop if you choose different file and automatically intialize new connection (in recvRtspReply)
        oldFileName = self.fileName
        self.fileName = str(self.panel.get(ANCHOR))  
        #print (oldFileName + " And " + self.fileName)
        if oldFileName != self.fileName:
            print("Set True isnewMovie")
            self.isNewMovie = True
            self.stopMovie()
        

    def exitClient(self):
        """Teardown button handler."""
        # TODO
        if self.state != self.SWITCH:
            #print ("Run TEARDOWN")
            self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui


    def pauseMovie(self):
        """Pause button handler."""
        # TODO
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def stopMovie(self):
        if self.state != self.SWITCH:
            self.sendRtspRequest(self.TEARDOWN)

    def describe(self):
        """Describe button handler."""
        if self.describeState:
            self.sendRtspRequest(self.DESCRIBE)
            self.isDescribeSent = True
            

    def playMovie(self):
        """Play button handler."""
        # TODO
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)


    #for display Current time
    def updateBar(self):
        self.converted_timeInterval = time.strftime('%M:%S', time.gmtime(self.frameNbr * self.TPF))
        self.converted_timeLength = time.strftime('%M:%S', time.gmtime(self.totalFrame * self.TPF))
        self.status_bar.config(text= self.converted_timeInterval + " / " + self.converted_timeLength)
        
        #self.status_bar.after(1, self.updateBar)
        

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    def listenRtp(self):
        """Listen for RTP packets."""
        self.startClock = time.time()
        self.stop = False
        self.isPlayed = True
        self.isPaused = False
        # TODO
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data == 0:
                    print("No frame received")
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
                        self.updateBar()
                      
            except:
                print("No data received")
                self.sumOfTime += time.time() - self.startClock
                self.stop = True

                # receive ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    print("TEARDOWN in ListenRTP")
                    self.rtpSocket.close()
                    self.teardownAcked = 0
                    self.rtspThread.join()
                    if self.isNewMovie: 
                        self.sendRtspRequest(self.SETUP)
                    else: 
                        self.fileName = ''
                    break

                #stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
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
        self.label.configure(image=photo, height = 288) #OG: height = 288
        self.label.image = photo
        print("Update frame " + str(self.frameNbr))
        if self.totalFrame == self.frameNbr:
            print("Paused since end of mv")
            self.frameNbr = 0
            self.sendRtspRequest(self.PAUSE)

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
        if requestCode == self.SETUP and self.state == self.SWITCH:
            self.connectToServer()
            self.rtspThread = threading.Thread(target=self.recvRtspReply)
            self.rtspThread.start()
            # update RTPS sequence number
            self.rtspSeq = 1
            self.describeState = True
            self.isPlayed = False
            self.isPaused = False
            self.isNewMovie = False
            self.description_gui.config(text= '(^o_o^)')
            self.status_bar.config(text= "--/--" )

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
        elif requestCode == self.TEARDOWN:
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

            if reply:
                print("\nReceive Reply")
                self.parseRtspReply(reply.decode("utf-8"))

            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()   

                if not self.stop:
                    self.sumOfTime += time.time() - self.startClock
                if self.sumOfTime > 0:
                    print('-' * 40)
                    print("\nAnalyze Statistics:")
                    print("\nTotal time: " + str(self.sumOfTime))
                    rateData = float(int(self.sumData) / int(self.sumOfTime))
                    print("\nVideo Data Rate: " + str(rateData))
                    if self.frameNbr != 0:
                        rateLoss = float(self.packetLoss / self.frameNbr)
                        print("\nRTP Packet Loss Rate: " + str(rateLoss) + "\n")
                    else:
                        print("Cannot calculate Loss Rate since frameNbr = 0.")
                    print('-' * 40)
                self.frameNbr = 0
                self.sumOfTime = 0

                try:
                    os.remove(
                        CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
                except:
                    print("No cache file to delete.")
                
                print ("End RTSP.")

                #When listen Thread does not run
                if not self.isPlayed or self.isPaused:
                    if self.isPaused:
                        self.rtpSocket.close()
                        self.teardownAcked = 0
                    print("Run when not played.")
                    if self.isNewMovie: 
                        self.sendRtspRequest(self.SETUP)
                    else:
                        print("Set file name for normal TEARDOWN")
                        self.fileName = ''
                break

    #  Use for response message

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server.
            slpit the response into line (an array of line)"""
        print("\nData received:\n")
        lines = data.split('\n')
        response_SeqNum = int(lines[1].split(' ')[1])
        response_Code = int(lines[0].split(' ')[1])
        print(lines[0] + '\n' + lines[1] + '\n' + lines[2])

        if response_SeqNum == self.rtspSeq:
            response_session = int(lines[2].split(' ')[1])

            # Check case for SETUP
            if self.sessionId == 0 or self.sessionId != response_session:
                self.sessionId = response_session

            if response_session == self.sessionId and not self.isDescribeSent:
                if response_Code == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        self.openRtpPort()
                        self.totalFrame = int(lines[3].split(' ')[1])
                        self.TPF = float(lines[4].split(' ')[1])
                    if self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    if self.requestSent == self.PAUSE:
                        self.state = self.READY
                        self.isPaused = True
                        self.playEvent.set()
                    if self.requestSent == self.TEARDOWN:
                        self.state = self.SWITCH
                        self.teardownAcked = 1
            
        #Update description pane when successfully received responses
        if self.isDescribeSent and response_Code == 200:
            count = 5
            self.description = lines[4]
            while lines[count]:
                self.description = self.description + '\n' + lines[count]
                count = count + 1
            self.isDescribeSent = False
            self.describeState = False
            self.description_gui.config(text= self.description)

    #  Initialize the socket

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)

        try:
            self.state = self.READY
            self.rtpSocket.bind((self.serverAddr, self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        
        if tkinter.messagebox.askyesno("Quit message", "Do you want to quit ?"):
            self.exitClient()
        elif self.state == self.PLAYING:
            self.playMovie()

    #python Server.py 554
    #python ClientLauncherv2.py 192.168.1.17 554 888
    #python ClientLauncher.py 192.168.1.17 554 888 movie.Mjpeg