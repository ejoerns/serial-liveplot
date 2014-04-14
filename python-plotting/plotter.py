#! /usr/bin/env python

################################################################################
#
# AVR serial data logger (ASDL)
#
# To be used with the avr-logger library
#
# (c) 2013-2014 by Enrico Joerns
#
################################################################################

import sys, serial
import numpy as np
from time import sleep
import logging
import argparse
import socket

from base_reader import ReaderError
from serial_reader import SerialReceiver
from socket_reader import SocketReceiver
from serial_decoder import ASDLDecoder
from plot_data import ChannelPlotData
from plotgui import ASDLPlotter
from file_logger import ASDLFileLogger

def hostname_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False

# main() function
def main():

  parser = argparse.ArgumentParser(description="AVR serial data logger")
  parser.add_argument('host', default='/dev/ttyUSB0',
      help='Serial port or host the device is connected to. Default: /dev/ttyUSB0')
  parser.add_argument('port', nargs='?', type=int, default='60001',
      help='Port to connect to. Default: 60001')

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

  # determine if we use socket or serial backend
  try:
    if hostname_resolves(args.host):
      print "Connect to", args.host, "port", args.port
      receiver = SocketReceiver(host=args.host, port=args.port)
    else:
      print "Connect to", args.host
      receiver = SerialReceiver(port=args.host, baudrate=args.baudrate)
  except ReaderError as err:
    print err
    return

  ser_dec = ASDLDecoder(ch_data, samples=args.samples)
  
  # register data handler
  receiver.dataHandler.append(ser_dec.handle)
  receiver.closeHandler.append(ser_dec.stop)

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
    ser_dec.onStopHandler.append(file_logger.close)


  # Start receiver worker Thread
  receiver.start()

  if not args.nogui:
    # Start gui on main Thread
    #plotter.show()
    try:
      plotter.show()
    except KeyboardInterrupt:
      print "Aborted by KeyboardInterrupt"

  receiver.close()
  print "Done!"

# call main
if __name__ == '__main__':
  main()

