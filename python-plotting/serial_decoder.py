################################################################################
#
# AVR serial data logger (ASDL)
#
# To be used with the avr-logger library
#
# (c) 2013 by Enrico Joerns
#
################################################################################

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

import serial
import threading
import time

class SerialReceiver(threading.Thread):
    """ This class has been written by
        Philipp Klaus and can be found on
        https://gist.github.com/4039175 .  """
    def __init__(self, device, port, *args):
        self._target = self.read
        self._args = args
        self.__lock = threading.Lock()
        self.ser = serial.Serial(device, port)
        self.data_buffer = ""
        self.closing = False # A flag to indicate thread shutdown
        self.sleeptime = 0.00005
        threading.Thread.__init__(self)
        self.handler = []

    def run(self):
        self._target(*self._args)

    def read(self):
        while not self.closing:
            time.sleep(self.sleeptime)
            if not self.__lock.acquire(False):
                continue
            try:
                inbyte = ord(self.ser.read(1))
                for h in self.handler:
                  h.handle(inbyte)
            finally:
                self.__lock.release()
        self.ser.close()

    def pop_buffer(self):
        # If a request is pending, we don't access the buffer
        if not self.__lock.acquire(False):
            return ""
        buf = self.data_buffer
        self.data_buffer = ""
        self.__lock.release()
        return buf

    def write(data):
        self.ser.write(data)

    def close(self):
        self.closing = True

class ASDLChannelDecoder:
  '''
  Extracts channel information from data provided by an 'add' command.
  Then allows to decode data sent for this channel
  '''

  # decoding from signedness | type to struct modules names
  dec_types = {
    (0 << 3) | 0x0 : ['b', 1], # int8
    (0 << 3) | 0x1 : ['h', 2], # int16
    (0 << 3) | 0x2 : ['i', 4], # int32
    (0 << 3) | 0x3 : ['l', 8], # int64
    (1 << 3) | 0x0 : ['B', 1], # uint8
    (1 << 3) | 0x1 : ['H', 2], # uint16
    (1 << 3) | 0x2 : ['I', 4], # uint32
    (1 << 3) | 0x3 : ['L', 8]  # uint64
  }

  def __init__(self):
    # total size of data payload
    self.data_size = 0
    # vector size
    self.vec_size = 0
    # data divisor to match 'unit'
    self.__divisor = 0
    self.__range_l = ""
    self.__range_h = ""
    # string name of channel
    self.name = ""
    # string unit of channel
    self.unit = ""
    #
    self.data = ""
    self._decodeString = ""
    # DEBUG: set logging level
    #logging.basicConfig(level=logging.DEBUG)

  def decodeType(self, inbyte):
    # upper 4 bits encode vector size - 1
    self.vec_size = ((inbyte & 0xF0) >> 4) + 1
    # bit 0x08 encodes signedness, bits 0x07 encode base type
    try:
      c_type, t_size = self.dec_types[inbyte & 0x0F]
    except KeyError:
      raise Exception("Invalid data type")

    self.data_size = self.vec_size * t_size
    # concat full decode string
    self._decodeString = c_type * self.vec_size
    logging.debug("decodeString: %s", self._decodeString)

  def pushDivisorByte(self, inbyte):
    # TODO: throw exception when called too often?
    self.__divisor = self.__divisor << 8
    self.__divisor = self.__divisor | inbyte

  def pushRangeLByte(self, inbyte):
    self.__range_l += chr(inbyte)

  def pushRangeHByte(self, inbyte):
    self.__range_h += chr(inbyte)

  def setName(self, name):
    self.name = name

  def setUnit(self, unit):
    self.unit = unit

  def getPlotDataInstance(self, samples):
    range_l, = struct.unpack('>l', self.__range_l)
    range_h, = struct.unpack('>l', self.__range_h)
    return ChannelPlotData(
        self.vec_size, 
        samples, 
        label=self.name, 
        unit=self.unit, 
        divisor=self.__divisor, 
        data_range=(range_l, range_h))


  def pushDataByte(self, byte):
    self.data += chr(byte)

  def decodeDataStream(self):
    logging.debug("raw data: " + binascii.hexlify(self.data))
    retval = struct.unpack(self._decodeString, self.data)
    #print "decoded: ", retval
    self.data = ""
    return retval


class ASDLDecoder:
  '''
  Used to decode input data

  To react on new decodes, register handler functions
  '''

  def __init__(self, ch_data, samples=100):
    self.samples = samples
    self.__parse_pos = 0
    self.stop_pos = 0
    self.name = ""
    self.counter = 0
    # hold channel and command for current received bytes
    self.curr_command = 0
    self.curr_channel = 0
    curr_ch_decoder = 0
    self.plotData = ch_data
    self.analogPlot = None
    self.channel_decoders = [] # Holds decoder class for each channel
    # Handler functions
    self.onChannelAddHandler = []
    self.onStartHandler = []
    self.onDataUpdateHandler = []

    #logging.basicConfig(level=logging.DEBUG)

  def handle(self, inbyte):
    # First byte: expect identifier
    if self.__parse_pos == 0:
      if inbyte == ASDL_IDENTIFIER:
        self.__parse_pos += 1

    # Second byte: expect command | channel
    elif self.__parse_pos == 1:
      self.curr_command = (inbyte & 0xF0)
      self.curr_channel = (inbyte & 0x0F)

      if self.curr_command == ASDL_CMD_DATA:
        logging.info("got DATA command for channel %d" % self.curr_channel)
        if len(self.channel_decoders) == 0:
          logging.error("No data channels set up, please resart device!")
          self.__parse_pos = 0
          return 1
        # get channel bytes to read (data_size + 2 bytes)
        try:
          self.stop_pos = self.channel_decoders[self.curr_channel].data_size + 2
          self.__parse_pos += 1
        except:
          logging.error("Error accessing channel %d, might not be set up correctly!" % self.curr_channel)
          raise

      elif self.curr_command == ASDL_CMD_ADD:
        logging.info("got ADD  command for channel %d" % self.curr_channel)
        self.curr_ch_decoder = ASDLChannelDecoder()
        self.__parse_pos += 1

      elif self.curr_command == ASDL_CMD_GO:
        logging.info("got GO   command")
        self.__parse_pos += 1

      else:
        logging.error("got Unknown command 0x%02x" % (inbyte & 0xF0))
        self.__parse_pos = 0

    # Other bytes: handle based on command
    else:
      # Received data
      if self.curr_command == ASDL_CMD_DATA:
        # check if all data received
        if self.__parse_pos == self.stop_pos:
          if inbyte == ASDL_END_TOKEN:
            # add new data to channels queue
            newData = self.channel_decoders[self.curr_channel].decodeDataStream()
            self.plotData[self.curr_channel].add(newData)
            # TODO: call plotter?
          else:
            logging.error("Expected end token, got 0x%02X", inbyte)
          self.__parse_pos = 0
        # new data byte
        else:
          self.channel_decoders[self.curr_channel].pushDataByte(inbyte)
          self.__parse_pos += 1

      # Add channel
      elif self.curr_command == ASDL_CMD_ADD:
        # read data type
        if self.__parse_pos == 2:
          self.curr_ch_decoder.decodeType(inbyte)
          self.__parse_pos += 1
        # read divisor
        elif self.__parse_pos < 7:
          self.curr_ch_decoder.pushDivisorByte(inbyte)
          self.counter = 0
          self.__parse_pos += 1
        # read divisor
        elif self.__parse_pos < 11:
          self.curr_ch_decoder.pushRangeLByte(inbyte)
          self.counter = 0
          self.__parse_pos += 1
        elif self.__parse_pos < 15:
          self.curr_ch_decoder.pushRangeHByte(inbyte)
          self.counter = 0
          self.__parse_pos += 1
        # read strings
        else:
          if self.counter == 2:
            # command must be terminated with end token to be valid
            if inbyte == ASDL_END_TOKEN:
              # -> add channel
              logging.info("Adding channel, %d" % self.curr_channel)
              self.channel_decoders.insert(self.curr_channel, self.curr_ch_decoder)
              self.__parse_pos = 0
              return
            # invalid command
            else:
              logging.error("Expected ASDL_END_TOKEN, got 0x%02X" % (inbyte))
              self.__parse_pos = 0
              return
          # check for end of string
          elif chr(inbyte) == '\0':
            # end of string, switch to next
            # check if done 
            if self.counter == 0:
              self.curr_ch_decoder.setName(self.name)
            elif self.counter == 1:
              self.curr_ch_decoder.setUnit(self.name)
            self.counter += 1
            self.name = ""
          # concat characters to string
          else:
            self.name += chr(inbyte)
            if (self.__parse_pos > 1024):
              print "Maximum command size exceeded. aborting"
              self.__parse_pos = 0
              return
          self.__parse_pos += 1
      
      # Start data capturing
      elif self.curr_command == ASDL_CMD_GO:
        if inbyte == ASDL_END_TOKEN:
          logging.info("Start capturing...")
          # get instance from each decoder 
          del self.plotData[:]
          for ch in self.channel_decoders:
            self.plotData.append(ch.getPlotDataInstance(self.samples))
          # Call onStartHandlers
          for sh in self.onStartHandler:
            sh(self.plotData)
        else:
          logging.error("Invalid go command")
        self.__parse_pos = 0

