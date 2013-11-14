import cv, cv2
import numpy as np

def main():
 capture = cv2.VideoCapture(-1)
 capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, 160)
 capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 100)
 cv2.namedWindow('Circles')
 while True:
  (status, im) = capture.read()
  im = cv2.cvtColor(im, cv.CV_BGR2GRAY)
  #im = cv2.medianBlur(im, 3)
  im = cv2.Canny(im, 30, 50)
  im = cv2.GaussianBlur(im, (0, 0), 1)

  circles = cv2.HoughCircles(im, cv2.cv.CV_HOUGH_GRADIENT, 10, 32, np.array([]), 100, 30, 15, 150)
  im = cv2.cvtColor(im, cv.CV_GRAY2BGR)
  if circles is not None:
    for i in circles[0][:2]:
      #print "Circle found at %d x %d" % (i[0], i[1])
      cv2.circle(im, (i[0],i[1]), i[2], (0,255,0), 2)

  cv2.imshow('Circles', im)
  cv2.waitKey(10)

if __name__ == '__main__':
  main()
