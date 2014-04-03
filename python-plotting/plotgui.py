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

import gtk, gobject

import matplotlib
# Note: GTK requries special thread handling,
# see http://unpythonic.blogspot.de/2007/08/using-threads-in-pygtk.html
#matplotlib.use('GTkAgg')

import multiprocessing as mp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.widgets import Button
from collections import deque

import matplotlib.animation as animation
import Queue
import time
import time

# plot class
class ASDLPlotter(animation.TimedAnimation):
  ''' 
  Plots data provided by a list of ChannelPlotData.
  '''

  # This is the time interval between two data points in the plot data
  DATA_INTERVAL = 10     # [ms]
  # This is the total time interval for which the data is stored
  DISPLAY_RANGE = 10000  # [ms]
  # This is the (minimum) interval for updating the plot visualization
  DRAW_INTERVAL = 50    # [ms]

  # This is the number of elements to store for maintaining the data information as described above
  DATA_SIZE = int(DISPLAY_RANGE / DATA_INTERVAL)

  # constr
  def __init__(self, plotData):
    ''' 
    plotData: is expected to be a list of ChannelPlotData
    '''
    self.channelSetup = plotData
    self.event_queue = mp.Queue()
    self.fig = plt.figure()
    self.win = self.fig.canvas.manager.window
    self.lines = []
    self.plotData = None
    self.lastData = []
    # Time since start of plot [ms]
    self.startTime = 0
    self.plotTime = None
    # Holds last element read from event queue, must be stored over subsequent calls of _draw_frame()
    self.last_element = None
    #self.lastData = [() for x in xrange(len(plotData))] # Array of tuples
    #print "plotData is size: ", len(plotData)
    animation.TimedAnimation.__init__(self, self.fig, interval=self.DRAW_INTERVAL, blit=True)

  def setup(self, dummyPlotData):
    '''
    Notify about channel set up complete.
    thread safe to be called from worker
    '''
    self.lastData = [() for x in self.channelSetup] # Array of tuples
    # Create Array of channels of subchannel dequeues to hold sensor data
    self.plotData = [[deque([0.0]*self.DATA_SIZE) for x in xrange(ch.vec_size)] for ch in self.channelSetup]
    print ">>> SETUP!"
    self.event_queue.put( ("<setup>", None) )

  def new_data(self, plot_tuple):
    '''
    Nofity about new data
    thread safe to be called form worker
    '''
    #print "Adding data from time", plot_tuple[0], "to idx", plot_tuple[1], ":", plot_tuple[2]
    #self.lastData[plot_tuple[1]] = (plot_tuple[0], plot_tuple[2])
    #print ">>> NEW DATA! (channel",plot_tuple[1],")"
    self.event_queue.put( ("<new_data>", plot_tuple ) )

  def _setup(self):
    # clear figure
    plt.clf()
    # rebuild figure
    for channel in xrange(len(self.channelSetup)):
      self.lines.insert(channel, [])
      spl = self.fig.add_subplot(len(self.channelSetup), 1, channel+1)
      ax = plt.gca() # get Axes instance as it does not force redraw for each call
      plt.title(self.channelSetup[channel].plotLabel)
      plt.xlabel('samples')
      plt.ylabel(self.channelSetup[channel].plotUnit)
      plt.ylim(self.channelSetup[channel].data_range)
      # Iterate over data vector
      for subchannel in xrange(len(self.channelSetup[channel].data)):
        # set vector label to vecLabels if available
        lbl = '%d' % subchannel if (self.channelSetup[channel].vecLabels == None) else self.channelSetup[channel].vecLabels[subchannel]
        self.lines[channel].insert(subchannel, plt.plot(self.plotData[channel][subchannel], label=lbl))
      # place legend right of subplot by decreasing plot width to 90%
      box = spl.get_position()
      spl.set_position([box.x0, box.y0, box.width * 0.9, box.height])
      plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
      # init deque to save plot y data
      #self.data = [deque([0.0]*maxLen) for x in xrange(vec_size)]
      self.plotTime = 0
      self.startTime = int(time.time() * 1000)

  def show(self):
    plt.show()

  # TOOD: can we use it?...
  # @Override
  def _init_draw(self):
    pass

  # @Override
  # executed every t ms if no data available
  def new_frame_seq(self):
      return iter("x");

  # executed if new_frame_seq generated sequence
  def _draw_frame(self, framedata):


    # Check for <setup> command if not set up yet...
    if self.plotTime == None:
      try:
        if self.event_queue.get_nowait()[0] == "<setup>":
          print "Setup plot..."
          self.last_element = None
          self._setup()
          return
      except Queue.Empty:
        return

    # get time since last call
    now_time = int(time.time() * 1000) - self.startTime
    plot_interval = now_time - self.plotTime
    self.plotTime = now_time
    # get elements to add
    num_elements = plot_interval / self.DATA_INTERVAL

    #print "--- Will accept times up to ", (now_time + plot_interval)
    #print "--- Will add", num_elements, "elements"

    # We generate a sequence of 'num_elements' new samples
    frame_nr = 0;
    while frame_nr < num_elements:

      # get new item from queue if we do not have one already
      if (self.last_element == None):
        try:
          self.last_element = self.event_queue.get_nowait()
          #print "Read new data! (",self.event_queue.qsize(),"items left)"
        except Queue.Empty:
          self.last_element = None

      # if we have data, process it, otherwise continue with old data
      if (self.last_element != None):

        # process setup command
        if self.last_element[0] == "<setup>":
          logging.info("Setup plot...")
          self.last_element = None
          self._setup()
          return
        
        # process data command
        elif self.last_element[0] == "<new_data>":
          evt_time = self.last_element[1][0]
          # if event time is smaller than our new item, 
          # update and continue as we might get more events
          if (evt_time < now_time + frame_nr * self.DATA_INTERVAL):
            up_channel = self.last_element[1][1]
            up_data = self.last_element[1][2]
            #print "Update channel", up_channel, "with data", up_data
            self.lastData[up_channel] = up_data
            # invalidate to mark as 'used'
            self.last_element = None
            continue

        # process unknown command
        else:
          logger.error("Unknown command from queue")

      # Here we have the most recent data stored in self.lastData.
      # So we can safely update our plot data list by one element,
      # i.e. delete right and append left a new element (keeps queue size fixed)
      #print "Add frame",frame_nr,"to queue.."
      for channel in xrange(len(self.plotData)):
        for subchannel in xrange(len(self.plotData[channel])):
          x = self.plotData[channel][subchannel].pop()
          self.plotData[channel][subchannel].appendleft(self.lastData[channel][subchannel])
      frame_nr += 1

    # once we updated all our plot data, print it to screen
    for idx in xrange(len(self.plotData)):
      for jdx in xrange(len(self.plotData[idx])):
        self.lines[idx][jdx][0].set_ydata(self.plotData[idx][jdx])

