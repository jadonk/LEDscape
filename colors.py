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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("localhost", 9999)

#print im.format, im.size, im.mode
# use a truetype font
font = ImageFont.truetype("spincycle.ttf", 18)
font_sm = ImageFont.truetype("pf_tempesta_seven.ttf", 8)

i = 0
width = 32
height = 16
im = Image.new("RGB", (width,height), "black")
im_draw = ImageDraw.Draw(im)
capture = cv2.VideoCapture(-1)
capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, 160)
capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 100)

def rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb(i/256.0,0.8,0.9)]
	return (rgb[0],rgb[1],rgb[2])

def dark_rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb(i/256.0,0.8,0.1)]
	return (rgb[0],rgb[1],rgb[2])

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

while True:
	(cvect, color, cname) = getColor()
	im.paste(dark_rainbow(color), (0,0,width,height))
	im_draw.text((2, 0), cname, font=font_sm, fill=rainbow(i))
	sock.sendto(chr(1) + im.tostring(), dest)
	i += 1
	if i > 256:
		i = 0

