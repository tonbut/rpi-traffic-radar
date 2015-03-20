import alsaaudio, math, wave, numpy, time, sys
from httplib2 import Http

#global variables used by setNoiseProfile
noiseProfile=[]
noiseSum=9999999
noisePoll=0

# periodically looks at signal and determines if it can use it for reference noise
def setNoiseProfile(data,rate):
	global noisePoll, noiseSum, noiseProfile
	if (noisePoll==0):
		n=data.size*2+1
		sum=numpy.sum(data)
		if (sum<noiseSum*1.05):
			noiseSum=sum
			noiseProfile=data
		noisePoll=64
	noisePoll=noisePoll-1

# processes a block of samples to determine dominant frequency
# then converts this into speed and direction
# returns a tuple of signal magnitude, speed (mph), away or towards boolean, and mean signal level
def process(data,rate):
	fft=numpy.fft.fft(data)
	n=fft.size
	s=n/2-1;
	C=numpy.absolute(fft);
	
	#filter out anything below 50Hz	
	highPassFreq=60
	bucket50Hz=highPassFreq*n/rate

	D=C[bucket50Hz+1:s+1:1]+C[n-bucket50Hz-1:s+1:-1]
	setNoiseProfile(D,rate)
	global noiseProfile
	D=D-noiseProfile
	
	c=numpy.argmax(D)+bucket50Hz
	mag1=C[c+1]
	mag2=C[n-c-1]
	m=(mag1+mag2)*0.5
	freq=(c)*(rate/n)	
	speed=freq*0.0225*0.621371	
	away=mag1>mag2
	mean=numpy.mean(C)
	return (m,speed,away,mean)			

# this function writes events to standard out in CSV format and also posts to REST web service		
def reportEvent(speed,away,count,avgAmplitude,maxAmplitude):
	dir=("Up" if away else "Down")
	print "{:14.0f}".format(time.time()*1000),",",time.strftime('%d-%m-%y %H:%M:%S'),",","{:4.1f}".format(speed),",",dir,",",count,",","{:4.0f}".format(avgAmplitude),",","{:4.0f}".format(maxAmplitude)
	sys.stdout.flush()
	
	#also post to event polestar
	msg="<traffic><mph>{:03.1f}</mph><dir>{:s}</dir><count>{:02.0f}</count></traffic>".format(speed,dir,count)
	try:
		http_obj = Http( disable_ssl_certificate_validation=True )
		resp, content = http_obj.request(
			uri="https://192.168.2.129:8443/polestar/scripts/execute/E91A568D39D303AB",
			method='POST',
			body=msg,
		)
	except:
		print "Unexpected error:", sys.exc_info()[0]

#global variables used by findEvents				
avgMean=0.2
lastDetected=False
lastAway=False
maxSpeed=0
avgMean=0.2
count=0
amplitudeSum=0
maxAmplitude=0

# statefully analyse data from process method() to detect movements		
def findEvents(v):

    COUNT_THRESHOLD=3 # number of data points before we consider it a proper detection
    SPEED_THRESHOLD=3.0 # speed below which we ignore

    m=v[0]
    speed=v[1]
    away=v[2]
    mean=v[3]
    global avgMean, lastDetected, lastAway, maxSpeed, count, amplitudeSum, maxAmplitude
    
    #determine a threshold above the noise floor for a real signal
    avgMean=avgMean*0.995+mean*0.005
    threshold=avgMean*15;
    
    startDetect=False
    endDetect=False	
    detected=m>threshold and speed>SPEED_THRESHOLD
    if (detected and not lastDetected):
    	startDetect=True
    if (not detected and lastDetected):
    	endDetect=True
    if (detected and lastDetected and lastAway!=away):
    	#new vehicle in opposite direction
    	startDetect=True
    	endDetect=True
    if (detected and lastDetected and math.fabs(speed-maxSpeed)>10):
    	#big change in speed
    	startDetect=True
    	endDetect=True
    #print startDetect," ",endDetect," ",detected	
    if (endDetect):
    	if (count>COUNT_THRESHOLD):
    		reportEvent(maxSpeed,lastAway,count,amplitudeSum/count,maxAmplitude)
    if (startDetect):
    	maxSpeed=0
    	maxAmplitude=0
    	count=0
    	amplitudeSum=0
       	lastAway=away
    if (detected):
    	if (speed>maxSpeed):
    		maxSpeed=speed
    	if (m>maxAmplitude):
    		maxAmplitude=m
       	count=count+1
       	amplitudeSum=amplitudeSum+m
    lastDetected=detected
				

# loops reading samples from ALSA and then processing them	
def readInput():

	sampleRate=22050 # this is high enough to capture the range of frequencies of interest
	period=4096 # the total number of samples to capture. The higher this is the finer frequency granularity

	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NORMAL)
	inp.setchannels(2)
	inp.setrate(sampleRate)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	inp.setperiodsize(period)
	div=sampleRate/(period)
	D=1/65536.0

	#last=time.time();
	while True:
		len=0;
		buf=[];
		while (len<period):
			l, data = inp.read()
			if (l>0):
				a = numpy.fromstring(data, dtype='int16')
				b = D*1j*a[1::2]
				b += D*a[0::2]
				buf.append(b)
				len+=l
			time.sleep(0.001)
			
		buf=numpy.concatenate(buf);	
		v=process(buf,sampleRate)
		findEvents(v)	
				
readInput()