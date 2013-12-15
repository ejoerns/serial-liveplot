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
from collections import deque
from matplotlib import pyplot as plt

# class that holds analog data for N samples
class AnalogData:
  # constr
  def __init__(self, maxLen):
    self.ax = deque([0.0]*maxLen)
    self.ay = deque([0.0]*maxLen)
    self.maxLen = maxLen

  # ring buffer
  def addToBuf(self, buf, val):
    if len(buf) < self.maxLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)

  # add data
  def add(self, data):
    assert(len(data) == 2)
    self.addToBuf(self.ax, data[0])
    self.addToBuf(self.ay, data[1])
    
# plot class
class AnalogPlot:
  # constr
  def __init__(self, analogData):
    # set plot to animated
    plt.ion() 
    self.axline, = plt.plot(analogData.ax)
    self.ayline, = plt.plot(analogData.ay)
    plt.ylim([0, 1023])

  # update plot
  def update(self, analogData):
    self.axline.set_ydata(analogData.ax)
    self.ayline.set_ydata(analogData.ay)
    plt.draw()

ASDL_IDENTIFIER = 0x55
ASDL_END_TOKEN = 0x69

ASDL_CMD_DATA = 0x00
ASDL_CMD_ADD = 0x10
ASDL_CMD_GO = 0x20

INT8 = 0
INT16 = 1
INT32 = 2
INT64 = 3

# main() function
def main():
  # expects 1 arg - serial port string
  if(len(sys.argv) != 2):
    print 'Example usage: python showdata.py "/dev/tty.usbmodem411"'
    exit(1)

 #strPort = '/dev/tty.usbserial-A7006Yqh'
  strPort = sys.argv[1];

  # plot parameters
  analogData = AnalogData(100)
  analogPlot = AnalogPlot(analogData)

  print 'plotting data...'

  # open serial port
  ser = serial.Serial(strPort, 38400)
  parse_pos = 0
  stop_pos = 0
  name = ""
  counter = 0
  while True:
    try:
      inbyte = ord(ser.read())
      # expect identifier
      if parse_pos == 0:
        if inbyte == ASDL_IDENTIFIER:
          parse_pos += 1
          #print "ASDL_IDENTIFIER"
      # expect cmd | channel number
      elif parse_pos == 1:
        command = (inbyte & 0xF0)
        channel = (inbyte & 0x0F)
        if command == ASDL_CMD_DATA:
          print "DATA command, channel %d" % channel
          # get channel bytes to read
          # stop_pos = ...
          parse_pos += 1
        elif command == ASDL_CMD_ADD:
          print "ADD  command, channel %d" % channel
          parse_pos += 1
        elif command == ASDL_CMD_GO:
          print "GO   command"
          parse_pos += 1
        else:
          print "Unknown command %x " % (inbyte & 0xF0)
          parse_pos = 0
          # todo...
      else:
        if command == ASDL_CMD_DATA:
          if parse_pos == stop_pos:
            # -> evaluate data 
            pass
          #
        elif command == ASDL_CMD_ADD:
          to_read = 0
          divisor = 0
          # read data type
          if parse_pos == 2:
            # upper 4 bits encode vector size - 1
            v_size = ((inbyte & 0xF0) >> 4) + 1
            # bit 0x08 encodes signedness
            signedness = (inbyte & 0x08)
            # bits 0x07 encode base type
            data_t = (inbyte & 0x07)
            if data_t == INT8:
              t_size = 8
            elif data_t == INT16:
              t_size = 16
            elif data_t == INT32:
              t_size = 32
            elif data_t == INT64:
              t_size = 64
            else:
              t_size = 0
            to_read = v_size * t_size
            print "%d * %d = %d" % (v_size, t_size, to_read)
            parse_pos += 1
          # read divisor
          elif parse_pos < 7:
            divisor = divisor << 8
            divisor = divisor | inbyte
            parse_pos += 1
            counter = 0
          # read strings
          else:
            # check if done 
            if counter == 2:
              # command must be terminated with end token to be valid
              if inbyte == ASDL_END_TOKEN:
                print "CMD DONE!"
                # -> add channel
                parse_pos = 0
                continue
              # invalid command
              else:
                print "ERROR!"
                parse_pos = 0
                continue
            # end of string, switch to next
            if chr(inbyte) == '\0':
              counter += 1
              print name
              name = ""
            # concat characters to string
            else:
              name += chr(inbyte)
            parse_pos += 1
          #
        elif command == ASDL_CMD_GO:
          if inbyte == ASDL_END_TOKEN:
            # -> start capturing
            pass
          else:
            print "Invalid GO command"
          parse_pos = 0

    except KeyboardInterrupt:
      print 'exiting'
      break
  # close serial
  ser.flush()
  ser.close()

# call main
if __name__ == '__main__':
  main()

