import alsaaudio, math, wave, numpy, time, sys
from track import Track

class Radar:

	#class variables used by setNoiseProfile
	noiseProfile=[]
	noiseSum=9999999
	noisePoll=0
	
	#class variables for findEvents
	lastDetected=0
	lastAway=0
	maxSpeed=0
	count=0
	amplitudeSum=0
	maxAmplitude=0

	def __init__(self,
		sampleRate=44100,
		alsaPeriod=1024,
		sampleBuffer=2048,
		speedMergeDiff=5,
		magnitudeThreshold=7,
		speedMultiplier=0.0225*0.621371, #mph
		lowFreq=144,
		highFreq=6000,
		trackInactivityPeriod=5, #samples
		trackMinCapturePeriod=15, #samples
		trackSpeedThreshold=3, # in units of speed
		realtimeCallback=None,
		trackCallback=None,
		trackDebugCallback=None
		):
	
		self.sampleRate=sampleRate
		self.buffer=sampleBuffer
		self.speedMergeDiff=speedMergeDiff
		self.magnitudeThreshold=magnitudeThreshold
		self.speedMultiplier=speedMultiplier
		self.lowFreq=lowFreq
		self.highFreq=highFreq
		
		self.realtimeCallback=realtimeCallback
		self.trackCallback=trackCallback
		self.trackDebugCallback=trackDebugCallback
		
		Track.__InactivityPeriod=trackInactivityPeriod
		Track.__MinCapturePeriod=trackMinCapturePeriod
		Track.__SpeedThreshold=trackSpeedThreshold
		
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NORMAL)
		inp.setchannels(2)
		inp.setrate(sampleRate)
		inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
		inp.setperiodsize(alsaPeriod)
		self.inp=inp
		self.div=sampleRate/(alsaPeriod)
		self.D=1/65536.0
		self.n=0
		
		
	def computeNoiseProfile(self,data):
	
		if (self.noisePoll==0):
			n=data.size*2+1
			sum=numpy.sum(data)
			if (sum<self.noiseSum*1.05):
				self.noiseSum=sum
				try:
					self.noiseProfile=numpy.add(numpy.multiply(noise,0.1),numpy.multiply(self.noiseProfile,0.9))
				except:
					self.noiseProfile=data
			self.noisePoll=16
		self.noisePoll=self.noisePoll-1
		
		
	def process(self,data):
		#speedMergeDiff is speed difference that multiple buckets will be merged
		#threshold is magnitude of signal that is significant
		fft=numpy.fft.fft(data)
		n=fft.size
		s=n/2-1;
		C=numpy.absolute(fft);
	
		#filter out anything below or above
		bucketLow=self.lowFreq*n/self.sampleRate
		bucketHigh=self.highFreq*n/self.sampleRate

		D=numpy.abs(C[bucketLow+1:bucketHigh:1]+C[n-bucketLow-1:n-bucketHigh:-1])
		self.computeNoiseProfile(D)
		D=D-self.noiseProfile
		
		#find set of maxima
		large_values = D > self.magnitudeThreshold
		speedDiff=(self.speedMergeDiff/self.speedMultiplier)*n/self.sampleRate
		
		lastIndex=0
		lastDir=False
		lastMaxMag=0
		lastMaxIndex=0
		recs=[]
		for i in range(1,len(large_values)-1,1):
			if (large_values[i]):
				c2=i+bucketLow;
				mag1=C[c2+1]
				mag2=C[n-c2-1]
				dir=mag1<mag2
				mag=D[i]
				if ((i-lastIndex)<speedDiff and dir==lastDir):
					#another
					if (mag>lastMaxMag):
						lastMaxMag=mag
						lastMaxIndex=i
				else:
					#store last
					if (lastMaxIndex!=0):
						freq=(lastMaxIndex+bucketLow)*self.sampleRate/n
						speed=freq*self.speedMultiplier
						rec={"s":speed,"d":lastDir,"m":lastMaxMag}
						recs.append(rec)
					#new group
					lastDir=dir
					lastMaxMag=mag
					lastMaxIndex=i
				lastIndex=i
				
		if (lastMaxIndex!=0):
			freq=(lastMaxIndex+bucketLow)*self.sampleRate/n
			speed=freq*self.speedMultiplier
			rec={"s":speed,"d":lastDir,"m":lastMaxMag}
			recs.append(rec)
			
		if self.realtimeCallback != None:
			c=numpy.argmax(D)
			c2=c+bucketLow
			mag1=C[c2+1]
			mag2=C[n-c2-1]
			m=D[c]
			freq=(c2)*(self.sampleRate/n)	
			speed=freq*self.speedMultiplier
			dir=mag1<mag2
			rec={"s":speed,"d":dir,"m":m}
			self.realtimeCallback(rec)
			
		return recs
		
	__tracking=[]
	def findEvents(self,records,sampleIndex):
	
		#match records to existing tracks
		for track in self.__tracking:
			for rec in records:
				if (track.matchPoint(sampleIndex,rec)):
					track.addPoint(sampleIndex,rec["s"])
					records.remove(rec)
	
		#create new tracking for unused recs
		for rec in records:
			track=Track(sampleIndex,rec["d"])
			track.addPoint(sampleIndex,rec["s"])
			self.__tracking.append(track)
			if self.trackDebugCallback!=None:
				self.trackDebugCallback(track,True)
			
		#end old tracks
		for track in self.__tracking:
			if track.isOld(sampleIndex):
				if track.isSignificant():
					self.trackCallback(track)
				elif self.trackDebugCallback!=None:
					self.trackDebugCallback(track,False)
				self.__tracking.remove(track)
				
		
		
	def sample(self):
		length=0;
		buf=[]
		while (length<self.buffer):
			l, data = self.inp.read()
			if (l>0):
				a = numpy.fromstring(data, dtype='int16')
				b = self.D*1j*a[1::2]
				b += self.D*a[0::2]
				buf.append(b)
				length+=l
			time.sleep(0.001)
		buf=numpy.concatenate(buf);
		recs=self.process(data=buf)
		
		#if (self.realtimeCallback != None and len(recs)>0 ):
		#	bestRec=recs[0]
		#	for rec in recs:
		#		if (rec["m"]>bestRec["m"]):
		#			bestRec=rec
		#	self.realtimeCallback(bestRec)
		
		#for rec in recs:
		#	print n," mag=","{:3.0f}".format(rec["m"])," ","{:4.1f}".format(rec["s"]),"mph ",rec["d"]					
		#if (len(recs)>0):
		#	print " "
		
		if (self.trackCallback != None):
			self.findEvents(records=recs,sampleIndex=self.n)
			self.n=self.n+1