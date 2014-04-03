#! /usr/bin/env python

################################################################################
#
# AVR serial data logger (ASDL)
#
# To be used with the avr-logger library
#
# (c) 2013 by Enrico Joerns
#
################################################################################

import sys, serial
import numpy as np
from time import sleep
import logging
import argparse

from serial_decoder import SerialReceiver
from serial_decoder import ASDLDecoder
from plot_data import ChannelPlotData
from plotgui import ASDLPlotter
from file_logger import ASDLFileLogger


# main() function
def main():

  parser = argparse.ArgumentParser(description="AVR serial data logger")
  
  parser.add_argument('port', default='/dev/ttyUSB0',
      help='Serial port the device is connected to. Default: /dev/ttyUSB0')
  parser.add_argument('-b, --braudrate', dest='baudrate', type=int, default=38400,
      help='Baudrate of device. Default: 38400')
  parser.add_argument('-s, --samples', dest='samples', type=int, default=100,
      help='Number of displayed samples. Default: 100')
  parser.add_argument('-f, --file', dest='logfile', default=None,
      help='File to log data')
  parser.add_argument('--nogui', help='Deactivates graphical output', action="store_true")
  
  args = parser.parse_args()

  print 'Starting logger...'

  # shared plot data list
  ch_data = []

  ser_recv = SerialReceiver(args.port, args.baudrate)
  ser_dec = ASDLDecoder(ch_data, samples=args.samples)
  
  # register handler
  ser_recv.handler.append(ser_dec)

  # setup gui (if not disabled)
  if not args.nogui:
    plotter = ASDLPlotter()
    ser_dec.onStartHandler.append(plotter.setup)
    ser_dec.onDataUpdateHandler.append(plotter.new_data)

  if args.logfile != None:
    print "Logging to file..."
    file_logger = ASDLFileLogger(args.logfile)
    ser_dec.onStartHandler.append(file_logger.setup)
    ser_dec.onDataUpdateHandler.append(file_logger.new_data)


  # Start receiver worker Thread
  ser_recv.start()

  if not args.nogui:
    # Start gui on main Thread
    plotter.show()

  ser_recv.close()
  print "Done!"

# call main
if __name__ == '__main__':
  main()

