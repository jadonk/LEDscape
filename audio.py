#!/usr/bin/env python
import alsaaudio
import audioop

inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, '1')
inp.setchannels(2)
inp.setrate(16000)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize(500)
max = 0
quiet_threshold = 4000
quiet_time = 10000
i = 0
max_ratio = 800

while True:
	l, data = inp.read()
	if l:
		rms = audioop.rms(data, 2)
		if rms < quiet_threshold:
			i = i + 1
		if i > quiet_time:
			max = 0
		if rms > max:
			max = rms
			i = 0
		print rms, max/max_ratio, i

