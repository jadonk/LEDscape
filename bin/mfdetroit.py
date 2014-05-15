#!/usr/bin/env python
try:
	import alsaaudio
	import audioop
except:
	print "Unable to load audio"

import Image, ImageFont, ImageDraw
import socket
import time
import collections
from colorsys import hsv_to_rgb

try:
	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, '1')
except:
	inp = 0

if inp:
	inp.setchannels(1)
	inp.setrate(8000)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	inp.setperiodsize(128)

width = 128
height = 128

udp = socket.getprotobyname('udp')
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
#dest = ("10.13.0.107", 9999)
dest = ("localhost", 9999)
font = ImageFont.truetype("fonts/spincycle.ttf", 18)
font_sm = ImageFont.truetype("fonts/pf_tempesta_seven.ttf", 8)

def rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb((i%256)/256.0,0.8,0.8)]
	return (rgb[0],rgb[1],rgb[2])

rainbowColors = [rainbow((i/180.0)*256.0) for i in range(0, 180)]

box = (0, 0, 128, 128)
images = []
titles = []
text = []
images.append(Image.open("images/boris.png"))
titles.append("BeagleBoard.org")
images.append(Image.open("images/i3.png"))
titles.append("i3 Detroit")
# BeagleBone Black
images.append(Image.open("images/oshw.png"))
titles.append("Open Source H/W")
images.append(Image.open("images/boris_cape.png"))
titles.append("BeagleBone Capes")
images.append(Image.open("images/android.png"))
titles.append("Android")
# Cloud9 IDE
images.append(Image.open("images/cylon.png"))
titles.append("JavaScript")
# Python
images.append(Image.open("images/gobot.png"))
titles.append("Go language")
images.append(Image.open("images/artoo.png"))
titles.append("Ruby language")
images.append(Image.open("images/freebsd.png"))
# Education
# Books
# OpenCV (moustache)
titles.append("FreeBSD")
images.append(Image.open("images/ArduinoBeaglebone_BBO_NO_16-9.png"))
titles.append("Arduino partnership")
# Gaming cape
# OpenROV
# MachineKit
# PRUs
# OpenSprinkler
# Octoscroller

index = 0
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
			l = 0
		if l:
			samples.append(rms)

	im = Image.new("RGBA", (width,height), "black")
	draw = ImageDraw.Draw(im)

	x = 0
	for i in list(samples):
		draw.line((x,128,x,128-i), width=2, fill=(0,0,0x10))
		x = x + 1

	draw.text((32, 4), titles[index], font=font_sm, fill=(222,114,36))
	rotated = images[index].resize((96, 96)).crop(box).offset(16,16).rotate(angle)
	im = Image.composite(rotated, im, rotated)

	if(frame > 100 and frame < 100+90):
		angle = angle + 4
		if(angle >= 360):
			angle = 0
	else:
		angle = 0

	data0 = chr(0) + im.convert("RGB").tostring()
	sock.sendto(data0, dest)

	frame = frame + 1
	if(frame >= 300):
		frame = 0
		index = index + 1
		if(index >= len(images)):
			index = 0

