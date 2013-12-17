import logging
import binascii
import struct

from plot_data import *
from plotgui import *

ASDL_IDENTIFIER = 0x55
ASDL_END_TOKEN = 0x69

ASDL_CMD_DATA = 0x00
ASDL_CMD_ADD = 0x10
ASDL_CMD_GO = 0x20


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


data_channels = []

class SerialHandler:

  parse_pos = 0
  stop_pos = 0
  name = ""
  counter = 0
  command = 0
  channel = 0
  currentChannel = 0
  plotData = []
  analogPlot = None

  def __init__(self):
    self.parse_pos = 0
    self.stop_pos = 0
    self.counter = 0
    self.command = 0
    self.channel = 0
    currentChannel = 0

  def handle(self, inbyte):
    # expect identifier
    if self.parse_pos == 0:
      if inbyte == ASDL_IDENTIFIER:
        self.parse_pos += 1
        #print "ASDL_IDENTIFIER" # expect cmd | channel number
    elif self.parse_pos == 1:
      self.command = (inbyte & 0xF0)
      self.channel = (inbyte & 0x0F)
      if self.command == ASDL_CMD_DATA:
        if len(data_channels) == 0:
          logging.error("No data channels set up, please resart device!")
          self.parse_pos = 0
          return
        #print "DATA self.command, channel %d" % channel
        # get channel bytes to read
        try:
          self.stop_pos = data_channels[self.channel].data_size + 2
        except:
          logging.error("Error accessing channel, might not be set up correctly!")
        self.parse_pos += 1
      elif self.command == ASDL_CMD_ADD:
        print "ADD  self.command, channel %d" % self.channel
        self.currentChannel = ASDLChannel()
        self.parse_pos += 1
      elif self.command == ASDL_CMD_GO:
        print "GO   self.command"
        self.parse_pos += 1
      else:
        print "Unknown self.command %x" % (inbyte & 0xF0)
        self.parse_pos = 0
        # todo...
    else:
      # Received data
      if self.command == ASDL_CMD_DATA:
        # check if all data received
        if self.parse_pos == self.stop_pos:
          if inbyte == ASDL_END_TOKEN:
            newData = data_channels[self.channel].decodeDataStream()
            self.plotData[self.channel].add(newData)
            self.analogPlot.update(self.plotData)
          else:
            logging.error("Expected end token, got 0x%02X", inbyte)
          self.parse_pos = 0
        else:
          data_channels[self.channel].pushDataByte(inbyte)
          self.parse_pos += 1

      # Add channel
      elif self.command == ASDL_CMD_ADD:
        to_read = 0
        divisor = 0
        # read data type
        if self.parse_pos == 2:
          self.currentChannel.decodeType(inbyte)
          self.parse_pos += 1
        # read divisor
        elif self.parse_pos < 7:
          self.currentChannel.pushDivisorByte(inbyte)
          self.counter = 0
          self.parse_pos += 1
        # read strings
        else:

          if self.counter == 2:
            # self.command must be terminated with end token to be valid
            if inbyte == ASDL_END_TOKEN:
              print "CMD DONE!"
              # -> add channel
              print "--> Add channel..."
              data_channels.insert(self.channel, self.currentChannel)
              self.parse_pos = 0
              return
            # invalid self.command
            else:
              print "ERROR!"
              self.parse_pos = 0
              return

          # check for end of string
          elif chr(inbyte) == '\0':
            # end of string, switch to next
            # check if done 
            if self.counter == 0:
              self.currentChannel.setName(self.name)
            elif self.counter == 1:
              self.currentChannel.setUnit(self.name)
            self.counter += 1
            self.name = ""

          # concat characters to string
          else:
            self.name += chr(inbyte)
            if (self.parse_pos > 1024):
              print "Maximum self.command size exceeded. aborting"
              self.parse_pos = 0
              return

          self.parse_pos += 1

      elif self.command == ASDL_CMD_GO:
        if inbyte == ASDL_END_TOKEN:
          # -> start capturing
          print "--> Start capturing..."
          # plot parameters
          self.plotData = []
          for ch in data_channels:
            self.plotData.append(ChannelData(ch.vec_size, 100, ch.name, ch.unit, ch.divisor))
          self.analogPlot = AnalogPlot(self.plotData)
          pass
        else:
          print "Invalid GO self.command"
        self.parse_pos = 0

