import math, time

class Track:

	__InactivityPeriod=5 #samples
	__MinCapturePeriod=15 #samples
	__SpeedThreshold=3 #speed units
	
	nextId=0
	
	def __init__(self, start, dir):
		self.start=start
		self.dir=dir
		self.last=start
		self.maxSpeed=0
		self.speeds=[]
		self.id=Track.nextId
		Track.nextId=Track.nextId+1

	def addPoint(self,n,speed):
		self.speeds.append(speed)
		self.last=n
		if (speed>self.maxSpeed):
			self.maxSpeed=speed
			
	def matchPoint(self,n,rec):
		match= (n-self.last <= self.__InactivityPeriod and rec["d"]==self.dir and math.fabs(rec["s"]-self.speeds[-1])<self.__SpeedThreshold);
		return match
		
	def isOld(self,n):
		return n-self.last > self.__InactivityPeriod;
		
	def isSignificant(self):
		return len(self.speeds)>=self.__MinCapturePeriod;
		
	def summary(self):
		dir = "down" if self.dir else "up"
		t = time.strftime('%d-%m-%y %H:%M:%S')
		ss=""
		for s in self.speeds:
			ss=ss+(" {:2.0f}".format(s));
		return "{:s} {:2.0f} samples, {:4.1f}mph {:s} {:s}".format(t,len(self.speeds),self.maxSpeed,dir,ss)