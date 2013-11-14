import cv, cv2
import numpy as np

def main():
 capture = cv2.VideoCapture(-1)
 capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, 160)
 capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 100)
 #cv2.namedWindow('Color')
 last_color = ""
 while True:
  (status, im) = capture.read()
  cvect = cv2.mean(im)
  #if cvect[0] < 45:
  if cvect[0] < 80:
   color = "Red"
  #elif cvect[0] < 90:
  # color = "Orange"
  #elif cvect[0] < 135:
  # color = "Yellow"
  elif cvect[0] < 180:
   color = "Green"
  else:
  #elif cvect[0] < 225:
   color = "Blue"
  #else:
  # color = "Violet"
  if color is not last_color:
   print color
   last_color = color
  #cv2.imshow('Color', im)
  #cv2.waitKey(100)

if __name__ == '__main__':
  main()
