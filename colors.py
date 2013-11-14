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
twidth = 128
width = 32
height = 16
disp = Image.new("RGB", (width,height), "black")
im = Image.new("RGB", (twidth,height), "black")
im_draw = ImageDraw.Draw(im)
disp_draw = ImageDraw.Draw(disp)
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
		color = 10 # "Red"
	elif cvect[0] < 170:
		color = 90 # "Green"
	else:
		color = 150 # "Blue"
	return (cvect, color)

while True:
	(cvect, color) = getColor()
	im.paste(dark_rainbow(color), (0,0,twidth,height))
	now = datetime.datetime.now()
	d = now.strftime("%a %d %b %Y")
	t = now.strftime("%H:%M")

	# Draw the date 
	im_draw.text((0, 0), d, font=font, fill=rainbow(i))

	# Make it scroll
	disp.paste(im.crop((0,0,i,height)), (width-i,0))
	disp.paste(im.crop((i+1,0,twidth-1,height)), (0,0))

	# Send it to the drawing server
	sock.sendto(chr(1) + disp.tostring(), dest)
	i += 1
	if i > twidth:
		i = -32

