#!/usr/bin/env python
import alsaaudio
import audioop
import Image, ImageFont, ImageDraw
import socket
import time
import collections
from colorsys import hsv_to_rgb

inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, '1')
if inp:
	inp.setchannels(1)
	inp.setrate(8000)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	inp.setperiodsize(128)

width = 128
height = 128

udp = socket.getprotobyname('udp')
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
dest = ("localhost", 9999)
font = ImageFont.truetype("fonts/spincycle.ttf", 18)
font_sm = ImageFont.truetype("fonts/pf_tempesta_seven.ttf", 8)

def rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb((i%256)/256.0,0.8,0.8)]
	return (rgb[0],rgb[1],rgb[2])

rainbowColors = [rainbow((i/180.0)*256.0) for i in range(0, 180)]

box = (0, 0, 128, 128)
im2 = Image.open("images/boris.png").resize((96, 96)).crop(box).offset(16,16)

angle = 0
frame = 0
samples = collections.deque(maxlen=128)
while True:
	l = 0
	if inp:
		l, data = inp.read()
	if l:
		try:
			rms = audioop.rms(data, 1)
		except:
			rms = 0
		if rms:
			samples.append(rms)

	im = Image.new("RGBA", (width,height), "black")
	draw = ImageDraw.Draw(im)
	#im.paste(rainbow(frame), box)

	x = 0
	for i in list(samples):
		#print i
		draw.line((x,96,x,96-i), width=2, fill=(0,0,255))
		x = x + 1

	draw.text((24, 0), "BeagleBoard.org", font=font_sm, fill=(222,114,36))
	rotated = im2.rotate(angle)
	im = Image.composite(rotated, im, rotated)

	if(frame > 360*2 and frame < 360*3):
		angle = angle + 2
		if(angle == 360):
			angle = 0
	else:
		angle = 0

	data0 = chr(0) + im.convert("RGB").tostring()
	sock.sendto(data0, dest)

	frame = frame + 1
	if(frame >= 10000):
		frame = 0

	time.sleep(0.01)

