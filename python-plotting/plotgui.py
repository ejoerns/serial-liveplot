################################################################################
#
# AVR serial data logger (ASDL)
#
# To be used with the avr-logger library
#
# (c) 2013-2014 by Enrico Joerns
#
################################################################################

import logging

import gtk, gobject

import matplotlib
# Note: GTK requries special thread handling,
# see http://unpythonic.blogspot.de/2007/08/using-threads-in-pygtk.html
#matplotlib.use('GTkAgg')
matplotlib.use('TkAgg')
#matplotlib.use('Qt4Agg')

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
  def __init__(self):
    self.event_queue = mp.Queue()
    self.figure = plt.figure()
    self.win = self.figure.canvas.manager.window
    self.lines = []
    self.plotData = None
    self.lastData = []
    # Time since start of plot [ms]
    self.startTime = 0
    self.plotTime = None
    # Holds last element read from event queue, must be stored over subsequent calls of _draw_frame()
    self.last_element = None
    animation.TimedAnimation.__init__(self, self.figure, interval=self.DRAW_INTERVAL, blit=True)
    #self.fig.canvas.mpl_connect('key_press_event', self.onClick)

  #def onClick(self, event):
  #  print 'button=%s, x=%d, y=%d'%(
  #      event.key, event.x, event.y)

  def setup(self, plotData):
    '''
    Notify about channel set up complete.
    thread safe to be called from worker
    '''
    self.channelSetup = plotData
    self.lastData = [() for x in self.channelSetup] # Array of tuples
    # Create Array of channels of subchannel dequeues to hold sensor data
    self.plotData = [[deque([0.0]*self.DATA_SIZE) for x in xrange(ch.vec_size)] for ch in self.channelSetup]
    self.event_queue.put( ("<setup>", None) )

  def new_data(self, plot_tuple):
    '''
    Nofity about new data
    thread safe to be called form worker
    '''
    self.event_queue.put( ("<new_data>", plot_tuple ) )

  def _setup(self):
    # clear figure
    self.figure.clear()
    # rebuild figure
    for channel in xrange(len(self.channelSetup)):
      self.lines.insert(channel, [])
      # add as subplot
      ch_axes = self.figure.add_subplot(len(self.channelSetup), 1, channel + 1)
      # setup axes
      ch_axes.set_title(self.channelSetup[channel].plotLabel)
      ch_axes.set_xlabel('samples')
      ch_axes.set_ylabel(self.channelSetup[channel].plotUnit)
      ch_axes.set_ylim(self.channelSetup[channel].data_range)
      # Iterate over data vector to add data lines
      for subchannel in xrange(len(self.channelSetup[channel].data)):
        # set subchannel label to subchannel index or vecLabels if available
        lbl = '%d' % subchannel if (self.channelSetup[channel].vecLabels == None) else self.channelSetup[channel].vecLabels[subchannel]
        # Add lines for this plot to lines array
        self.lines[channel].insert(subchannel, ch_axes.plot(self.plotData[channel][subchannel], label=lbl)[0])
      # place legend right of subplot by decreasing plot width to 90%
      box = ch_axes.get_position()
      ch_axes.set_position([box.x0, box.y0, box.width * 0.9, box.height])
      ch_axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))
      # init deque to save plot y data
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
        self.lines[idx][jdx].set_ydata(self.plotData[idx][jdx])

