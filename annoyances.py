import sys
import socket
import urllib, urllib2
from colorsys import hsv_to_rgb

'''
annoyances.py
Things to annoy people with.

Each function is in the table-o-annoyances and is called with the doAlarm method
THESE WILL NEED EDITING FOR YOUR CONFIGURATION. All of these are specific to our network
'''
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("localhost", 9999)
#font = ImageFont.truetype("spincycle.ttf", 18)
#font_sm = ImageFont.truetype("pf_tempesta_seven.ttf", 8)

i = 0
width = 32
height = 16
#disp = Image.new("RGB", (width,height), "black")
#im = Image.new("RGB", (256,height), "black")
#im_draw = ImageDraw.Draw(im)
#disp_draw = ImageDraw.Draw(disp)

def rainbow(i):
	rgb = [int(x*256) for x in hsv_to_rgb(i/256.0,0.8,0.8)]
	return (rgb[0],rgb[1],rgb[2])

class alarms:
	#first annoyance
	def first(self, state):
		if state:
			print "The sink has stuff in it"

	#second annoyance
	def second(self, state):
		if state:
			print "The sink *still* has washing up in it"

	#third annoyance
	def third(self,state):
		if state:
			print "FFS the sink needs cleaning, someone sort it out!"

	#build a function list to call from doAlarm
	alarmList = [first, second, third]
	
	def __init__ (self):
		#I used to ping things to the serial port until I decided that the traffic lights were a better idea
		print "serial port not available, using IRC and traffic lights"
	
	#trigger an alarm, first stop all other alarms, then start our requested one
	def doAlarm(self, level):
		if 0 <= level < len(self.alarmList):
			for a in self.alarmList:
				a(self, False)
			self.alarmList[level](self, True)

	#cycle through all alarm methods and run the "stop" command
	def stopAllAlarms(self):
		for a in self.alarmList:
			a(self, False)
		#the next line got annoying
#		self.ircSpeak("The sink has been cleared, happy days")

