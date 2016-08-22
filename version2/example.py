from radar import Radar
import alsaaudio, math, wave, numpy, time, sys


def radarRealtimeStatus(rec):
	if (rec["m"]>5):
		msg="{:3.0f} {:3.0f}".format(rec["m"],rec["s"])
		print msg

def radarTrack(track):
	#print track.summary()
	
	dir=("Down" if track.dir else "Up")
	count=len(track.speeds)
	print "{:14.0f}".format(time.time()*1000),",",time.strftime('%d-%m-%y %H:%M:%S'),",","{:4.1f}".format(track.maxSpeed),",",dir,",",count
	sys.stdout.flush()
	
	
def radarTrackDebug(track,start):
	if (start):
		dir = "down" if track.dir else "up"
		print track.id,"new track",dir
	else:
		print track.id,"end",len(track.speeds),track.maxSpeed,"mph"
	
def status(msg):
	sys.stderr.write(msg)
	sys.stderr.write("\n")

r=Radar(
	sampleRate=44100,
	alsaPeriod=1024,
	sampleBuffer=2048,
	#realtimeCallback=radarRealtimeStatus,
	#trackDebugCallback=radarTrackDebug,
	trackCallback=radarTrack
	)

try:
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
	
