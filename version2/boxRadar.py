from radar import Radar
from hd44780 import hd44780 
import alsaaudio, math, wave, numpy, time, sys

lcd=hd44780()
#lcd.customChar(0,[0x00,0x00,0x00,0x1F,0x00,0x00,0x00,0x00])
lcd.customChar(0,[0x10,0x10,0x10,0x1F,0x10,0x10,0x10,0x10])
lcd.customChar(1,[0x18,0x18,0x18,0x1F,0x18,0x18,0x18,0x18])
lcd.customChar(2,[0x1C,0x1C,0x1C,0x1F,0x1C,0x1C,0x1C,0x1C])
lcd.customChar(3,[0x1E,0x1E,0x1E,0x1F,0x1E,0x1E,0x1E,0x1E])
#lcd.customChar(5,[0x1F,0x1F,0x1F,0x1F,0x1F,0x1F,0x1F,0x1F])

def generateBar(v,len):
	r=[]
	v2=int(v*6*len)
	for i in range(len):
		if (v2>=5):
			r.append('\xFF')
		elif (v2<=0):
			r.append('-')
		else:
			r.append(str(unichr(v2-1)))
		v2=v2-5
	return "".join(r)

realtimeStatus=""
realtimeTTL=0

def radarRealtimeStatus(rec,radar):
	global realtimeStatus, realtimeTTL
	m=rec["m"]
	#print m
	if (m>radar.magnitudeThreshold ):
		s="\x7F" if rec["d"] else "\x7E"
		realtimeStatus="{:4.1f}mph {:s}".format(rec["s"],s)
		realtimeTTL=20
	else:
		realtimeTTL=realtimeTTL-1;
		if (realtimeTTL==0):
			realtimeStatus=""
			
	bar=generateBar( math.log(m)*0.16 if m>0 else 0.0, 6 )
	
	msg="{:6s} {:s}".format(bar,realtimeStatus)
	lcd.line1(msg)

def radarTrack(track):
	#print track.summary()
	t=time.strftime('%H:%M:%S')
	s="\x7F" if track.dir else "\x7E"
	msg="{:s}{:s}{:4.1f}mph".format(t,s,track.maxSpeed)
	lcd.line2(msg)
		
def status(msg):
	lcd.line1(msg)

try:
	r=Radar(
		sampleRate=44100,
		alsaPeriod=1024,
		sampleBuffer=2048,
		lowFreq=40,
		realtimeCallback=radarRealtimeStatus,
		#trackDebugCallback=radarTrackDebug,
		trackCallback=radarTrack
		)

	status("Listening...")
	while (True):
		r.sample()
		
except alsaaudio.ALSAAudioError:
	status("No soundcard!")
except KeyboardInterrupt:
	status("Interrupted!")
except:
	status("Unexpected error!")
	raise
	
