#!/usr/bin/python
# Draw images with PIL and send them to the display.
# Dual scrolling example with fixed time on each side and
# the date scrolling around.
#
import Image, ImageFont, ImageDraw
import socket
import time, datetime
from colorsys import hsv_to_rgb
import cv, cv2
import numpy as np
from random import randint

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("localhost", 9999)

#print im.format, im.size, im.mode
# use a truetype font
font = ImageFont.truetype("spincycle.ttf", 18)
font_sm = ImageFont.truetype("pf_tempesta_seven.ttf", 8)

i = 0
width = 32*5
height = 16
im = Image.new("RGB", (width,height), "white")
im_draw = ImageDraw.Draw(im)
im_pixels = im.load()
bone = Image.open("bone.png")
capture = cv2.VideoCapture(-1)
capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, 160)
capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 100)
last_color = "Green"
show_color = 0
effect = 0

def rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb((i%256)/256.0,0.8,0.8)]
	return (rgb[0],rgb[1],rgb[2])

def myfill(i):
	if i < 100:
		return (0, 0, 0)
	return rainbow(i)

rainbowColors = [rainbow((i/180.0)*256.0) for i in range(0, 180)]

def r_array(cycle):
	color = cycle % 180
	for x in range(0, width):
		for y in range(0, height):
			index = int(color + x + y*10/4) % 180
			im_pixels[x, y] = rainbowColors[index];

spectrum = [randint(1,height) for i in range(0, width/2)]

def spec_an(i):
	im.paste((0,0,0), (0,0,width,height))
	for x in range(0, width/2):
		spectrum[x] = spectrum[x] + randint(-2,2)
		if spectrum[x] >= height:
			spectrum[x] = height
		elif spectrum[x] <= 0:
			spectrum[x] = 0
		im_draw.line((x*2, height, x*2, spectrum[x]), fill=rainbow(i))

def getColor():
	(status, cam) = capture.read()
	cvect = cv2.mean(cam)
	if cvect[0] < 80:
		color = 10
		cname = "Red"
	elif cvect[0] < 170:
		color = 90
		cname = "Green"
	else:
		color = 150
		cname = "Blue"
	return (cvect, color, cname)

sock.sendto(chr(1) + im.tostring(), dest)

