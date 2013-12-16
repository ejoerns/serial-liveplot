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
import struct
import binascii
import logging

class ASDLChannel:
  ''' Holds information related to a data channel. '''
  # total size of data payload
  data_size = 0
  # vector size
  vec_size = 0
  # 0 = signed, 1 = unsigned
  signedness = 0
  c_type = ""
  t_size = 0
  # data divisor to match 'unit'
  divisor = 0
  # string name of channel
  name = ""
  # string unit of channel
  unit = ""
  #
  data = ""
  decodeString = ""

  INT8 = 0
  INT16 = 1
  INT32 = 2
  INT64 = 3

  def __init__(self):
    #logging.basicConfig(level=logging.DEBUG)
    pass

  def decodeType(self, inbyte):
    # upper 4 bits encode vector size - 1
    self.vec_size = ((inbyte & 0xF0) >> 4) + 1
    # bit 0x08 encodes signedness
    self.signedness = (inbyte & 0x08)
    # bits 0x07 encode base type
    data_t = (inbyte & 0x07)
    if data_t == self.INT8:
      self.t_size = 1
      if (self.signedness == 0):
        c_type = 'b'
      else:
        c_type = 'B'
    elif data_t == self.INT16:
      self.t_size = 2
      if (self.signedness == 0):
        c_type = 'h'
      else:
        c_type = 'H'
    elif data_t == self.INT32:
      self.t_size = 4
      if (self.signedness == 0):
        c_type = 'i'
      else:
        c_type = 'I'
    elif data_t == self.INT64:
      self.t_size = 8
      if (self.signedness == 0):
        c_type = 'l'
      else:
        c_type = 'L'
    else:
      raise
    self.data_size = self.vec_size * self.t_size
    for i in range (0, self.vec_size):
      self.decodeString += c_type
    logging.debug("decodeString: %s", self.decodeString)


  def pushDivisorByte(self, inbyte):
    # TODO: throw exception when called too often?
    self.divisor = self.divisor << 8
    self.divisor = self.divisor | inbyte

  def setName(self, name):
    self.name = name

  def setUnit(self, unit):
    self.unit = unit

  def pushDataByte(self, byte):
    self.data += chr(byte)

  def decodeDataStream(self):
    logging.debug("raw data: " + binascii.hexlify(self.data))
    #logging.debug("decoded:  ", struct.unpack(self.decodeString, self.data))
    retval = struct.unpack(self.decodeString, self.data)
    self.data = ""
    return retval


class ChannelData:
  ''' 
  Holds data for a single channel 
  '''
  # constr
  def __init__(self, vec_size, maxLen):
    self.vec_size = vec_size 
    self.maxLen = maxLen
    self.data = [deque([0.0]*maxLen) for x in xrange(vec_size)]

  # ring buffer
  def addToBuf(self, buf, val):
    if len(buf) < self.maxLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)

  # add data
  def add(self, data):
    print "add: ", data
    for idx in range(0, len(data)):
      self.addToBuf(self.data[idx], data[idx])


# plot class
class AnalogPlot:
  lines = []
  # constr
  def __init__(self, plotData):
    # set plot to animated
    plt.ion()
    for idx in xrange(len(plotData)):
      self.lines.insert(idx, [])
      for jdx in xrange(len(plotData[idx].data)):
        self.lines[idx].insert(jdx, plt.plot(plotData[idx].data[jdx]))
    plt.ylim([0, 1023])

  # update plot
  def update(self, plotData):
    for idx in xrange(len(plotData)):
      for jdx in xrange(len(plotData[idx].data)):
        self.lines[idx][jdx][0].set_ydata(plotData[idx].data[jdx])
    plt.draw()

ASDL_IDENTIFIER = 0x55
ASDL_END_TOKEN = 0x69

ASDL_CMD_DATA = 0x00
ASDL_CMD_ADD = 0x10
ASDL_CMD_GO = 0x20


data_channels = []

# main() function
def main():
  # expects 1 arg - serial port string
  if(len(sys.argv) != 2):
    print 'Example usage: python showdata.py "/dev/tty.usbmodem411"'
    exit(1)

 #strPort = '/dev/tty.usbserial-A7006Yqh'
  strPort = sys.argv[1];


  print 'plotting data...'

  # open serial port
  try:
    ser = serial.Serial(strPort, 38400)
  except:
    print "Failed opening %s" % (strPort)
    sys.exit(1)
    
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
          #print "ASDL_IDENTIFIER" # expect cmd | channel number
      elif parse_pos == 1:
        command = (inbyte & 0xF0)
        channel = (inbyte & 0x0F)
        if command == ASDL_CMD_DATA:
          if len(data_channels) == 0:
            logging.error("No data channels set up, please resart device!")
            parse_pos = 0
            continue
          print "DATA command, channel %d" % channel
          # get channel bytes to read
          try:
            stop_pos = data_channels[channel].data_size + 2
          except:
            logging.error("Error accessing channel, might not be set up correctly!")
          parse_pos += 1
        elif command == ASDL_CMD_ADD:
          print "ADD  command, channel %d" % channel
          newChannel = ASDLChannel()
          parse_pos += 1
        elif command == ASDL_CMD_GO:
          print "GO   command"
          parse_pos += 1
        else:
          print "Unknown command %x" % (inbyte & 0xF0)
          parse_pos = 0
          # todo...
      else:
        # Received data
        if command == ASDL_CMD_DATA:
          # check if all data received
          if parse_pos == stop_pos:
            if inbyte == ASDL_END_TOKEN:
              newData = data_channels[channel].decodeDataStream()
              plotData[channel].add(newData)
              analogPlot.update(plotData)
            else:
              logging.error("Expected end token, got 0x%02X", inbyte)
            print "--> evaluate"
            parse_pos = 0
          else:
            data_channels[channel].pushDataByte(inbyte)
            parse_pos += 1

        # Add channel
        elif command == ASDL_CMD_ADD:
          to_read = 0
          divisor = 0
          # read data type
          if parse_pos == 2:
            newChannel.decodeType(inbyte)
            parse_pos += 1
          # read divisor
          elif parse_pos < 7:
            newChannel.pushDivisorByte(inbyte)
            counter = 0
            parse_pos += 1
          # read strings
          else:

            if counter == 2:
              # command must be terminated with end token to be valid
              if inbyte == ASDL_END_TOKEN:
                print "CMD DONE!"
                # -> add channel
                print "--> Add channel..."
                data_channels.insert(channel, newChannel)
                parse_pos = 0
                continue
              # invalid command
              else:
                print "ERROR!"
                parse_pos = 0
                continue

            # check for end of string
            elif chr(inbyte) == '\0':
              # end of string, switch to next
              # check if done 
              if counter == 0:
                newChannel.setName(name)
              elif counter == 1:
                newChannel.setUnit(name)
              counter += 1
              name = ""

            # concat characters to string
            else:
              name += chr(inbyte)
              if (parse_pos > 1024):
                print "Maximum command size exceeded. aborting"
                parse_pos = 0
                continue

            parse_pos += 1

        elif command == ASDL_CMD_GO:
          if inbyte == ASDL_END_TOKEN:
            # -> start capturing
            print "--> Start capturing..."
            # plot parameters
            plotData = []
            for ch in data_channels:
              plotData.append(ChannelData(ch.vec_size, 10))
            analogPlot = AnalogPlot(plotData)
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

