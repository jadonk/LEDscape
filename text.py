#!/usr/bin/python
# Draw images with PIL and send them to the display.
# Dual scrolling example with fixed time on each side and
# the date scrolling around.
#
import Image, ImageFont, ImageDraw
import socket
import time, datetime

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("localhost", 9999)

#print im.format, im.size, im.mode
# use a truetype font
font = ImageFont.truetype("spincycle.ttf", 18)
font_sm = ImageFont.truetype("pf_tempesta_seven.ttf", 8)

width = 32*5
height = 16
im = Image.new("RGB", (width,height), "black")
draw = ImageDraw.Draw(im)
i = 32*5

while True:
	im.paste((0,0,0), (0,0,width,height))
	#draw.text((i, 0), "This is a long bit of text to show what it looks like to scroll", font=font, fill=(255,255,255))
	draw.text((i, 0), "BeagleBoard.org BeagleBone Black running LEDscape on PRUs and a Python script", font=font, fill=(255,255,255))
	sock.sendto(chr(1) + im.tostring(), dest)
	time.sleep(0.01)
	i = i - 1;
	if i < -32*5*5:
		i = 32*5

