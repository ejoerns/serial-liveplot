################################################################################
# showdata.py
#
# Display analog data from Arduino using Python (matplotlib)
# 
# electronut.in
#
################################################################################

import sys, serial
import numpy as np
from time import sleep
import logging

from serial_decoder import *
from plot_data import *
from plotgui import *


# main() function
def main():

  # expects 1 arg - serial port string
  if(len(sys.argv) != 2):
    print 'Example usage: python showdata.py "/dev/tty.usbmodem411"'
    exit(1)

 #strPort = '/dev/tty.usbserial-A7006Yqh'
  strPort = sys.argv[1];

  print 'Starting logger...'

  # open serial port
  try:
    ser = serial.Serial(strPort, 38400)
  except:
    print "Failed opening %s" % (strPort)
    sys.exit(1)
    
  handler = SerialHandler()
  while True:
    try:
      inbyte = ord(ser.read())
      handler.handle(inbyte)
    except KeyboardInterrupt:
      print 'exiting'
      break
  # close serial
  ser.flush()
  ser.close()

# call main
if __name__ == '__main__':
  main()

