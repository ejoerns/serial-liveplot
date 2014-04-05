################################################################################
#
# AVR serial data logger (ASDL)
#
# To be used with the avr-logger library
#
# (c) 2014 by Enrico Joerns
#
################################################################################

import logging
import os.path
import threading
import multiprocessing as mp

class ASDLFileLogger():

  def __init__(self, filename):
    self.event_queue = mp.Queue()
    self.lastData = []
    self.filename = filename
    self.channelInfo = None

    if os.path.isfile(filename):
      logging.warning("File already exists, will be overwritten :)")


  def setup(self, plotData):
    '''
    plotData: expected to be an array of plot channel information
    '''
    self.channelInfo = plotData
    self.lastData = [(0,)*channel.vec_size for channel in plotData] # Array of tuples
    # Start worker thread
    self.workerthread = threading.Thread(target=self._worker)
    self.workerthread.start()


  def new_data(self, plot_tuple):
    '''
    Add new data to log
    plot_tuple: tuple of values for one channel
    '''
    self._addToQueue(plot_tuple)


  def close(self):
    self._addToQueue(None)


  def _addToQueue(self, item):
    self.event_queue.put(item)


  def _worker(self):
    close = False

    # Open log file
    try:
      # This will create a new file or **overwrite an existing file**.
      logfile = open(self.filename, "w")
      logging.warning("Opened file '%s' for writing log data" % self.filename)
    except IOError:
      logging.warning("Failed opening file '%s'. Aborting..." % self.filename)
      return

    # Write log file header
    line = "# time"
    for channel in self.channelInfo:
      for label in channel.vecLabels:
        line += ", "
        line += channel.get_label()
        line += "."
        line += label
    line += "\n"
    logfile.write(line)

    # process all our items
    while not close:
      item = self.event_queue.get() # get item (tstamp, channel, data tuple)

      # can be aborted by sending a None item
      if item == None:
        close = True
        continue

      up_time = item[0]
      up_channel = item[1]
      up_data = item[2]
      #print "Update channel", up_channel, "with data", up_data
      self.lastData[up_channel] = up_data

      # Concat line
      line = str(up_time)
      for channel in self.lastData:
        for subchannel in channel:
          line += ", "
          line += str(subchannel)
      line += "\n"
      # Write line to file
      logfile.write(line)

    # close file
    logfile.close()
    logging.warning("Closed log file")

