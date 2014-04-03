#!/usr/bin/env python
import alsaaudio
import audioop
import Image, ImageFont, ImageDraw
import socket
from colorsys import hsv_to_rgb

inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, '1')
inp.setchannels(2)
inp.setrate(16000)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize(500)
max = 0
quiet_threshold = 3000
quiet_time = 10000
i = 0
max_ratio = 800
a = 300

width = 32*5
height = 16
j = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("localhost", 9999)
font = ImageFont.truetype("spincycle.ttf", 18)
font_sm = ImageFont.truetype("pf_tempesta_seven.ttf", 8)
im = Image.new("RGB", (width,height), "black")
draw = ImageDraw.Draw(im)
pixels = im.load()

def rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb((i%256)/256.0,0.8,0.8)]
	return (rgb[0],rgb[1],rgb[2])

rainbowColors = [rainbow((i/180.0)*256.0) for i in range(0, 180)]


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
		#print rms, max/max_ratio, i
		im.paste((0,0,0), (0,0,width,height))
		if max > quiet_threshold:
			draw.text((1,0), str(max/max_ratio), font=font_sm, fill=(0,255,0))
			draw.line((20,8,20+rms/a,8), width=14, fill=(0,0,255))
			draw.line((20+max/a,0,20+max/a,16), width=4, fill=(255,0,0))
		else:
			draw.text((20, 0), "BeagleBone", font=font, fill=rainbow(j))
		sock.sendto(chr(1) + im.tostring(), dest)
		if i % 10 == 0:
			j = j + 1
		if j > 65536:
			j = 0

