class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0			
		self.totalframeNum = 0
		self.totalframeNum = self.totalFrame()
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits

		if data: 
			framelength = int(data)

			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
	
	def totalFrame(self):
		"""Count total frame."""
		try:
			tempFile = open(self.filename, 'rb')
		except:
			print ("Cannot open file.")
		totalframeNum = 0
		dataTemp = tempFile.read(5) # Get the framelength from the first 5 bits
		while dataTemp: 
			tempFramelength = int(dataTemp)

			# Read the current frame
			dataTempContent = tempFile.read(tempFramelength)
			if dataTempContent:
				totalframeNum += 1
			dataTemp = tempFile.read(5)
		return totalframeNum
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	