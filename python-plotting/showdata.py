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
  
  # Expect port as first argument
  strPort = sys.argv[1];

  print 'Starting logger...'

  # to add channels to...
  ch_data = []
  ser_recv = SerialReceiver(strPort, 38400)
  my_queue = mp.Queue()
  ser_dec = ASDLDecoder(ch_data, my_queue)
  
  # register handler
  ser_recv.handler.append(ser_dec)

  #plotter.setup()
  #ser_dec.onStartHandler.append(plotter.setup)
  #ser_dec.registerHandler(plotter)

  plotter = ASDLPlotter(ch_data, my_queue)
  ser_dec.onStartHandler.append(plotter.setup)

  # Start receiver worker Thread
  ser_recv.start()

  # Start gui on main Thread
  plotter.show()

  ser_recv.close()
  print "Done!"

# call main
if __name__ == '__main__':
  main()

