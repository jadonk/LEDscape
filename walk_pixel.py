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
im_pixels = im.load()
draw = ImageDraw.Draw(im)

while True:
	for y in range(0, height):
		for x in range(0, width):
			im.paste((0,0,0), (0,0,width,height))
			im_pixels[x, y] = (255,255,255)
			sock.sendto(chr(1) + im.tostring(), dest)
			i = y*width+x
			#print x, y, i
			#time.sleep(0.01)
		

