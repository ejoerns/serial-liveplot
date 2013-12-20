import gtk, gobject

import matplotlib
# Note: GTK requries special thread handling,
# see http://unpythonic.blogspot.de/2007/08/using-threads-in-pygtk.html
#matplotlib.use('GTkAgg')

import multiprocessing as mp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import Queue
import time
import time

# plot class
class ASDLPlotter(animation.TimedAnimation):


  # constr
  def __init__(self, plotData, my_queue):
    ''' 
    plotData: is expected to be a list of ChannelPlotData
    '''
    self.plotData = plotData
    self.my_queue = my_queue
    self.fig = plt.figure()
    self.win = self.fig.canvas.manager.window
    self.lines = []
    animation.TimedAnimation.__init__(self, self.fig, interval=40, blit=True)

  def setup(self, dummyPlotData):
    '''
    Notify about channel set up complete.
    thread safe to be called from worker
    '''
    self.my_queue.put("<setup>")

  def new_data(self):
    '''
    Nofity about new data
    thread safe to be called form worker
    '''
    self.my_queue.put("<new_data>")

  def _setup(self):
    # clear figure
    plt.clf()
    # rebuild figure
    for idx in xrange(len(self.plotData)):
      self.lines.insert(idx, [])
      spl = self.fig.add_subplot(len(self.plotData), 1, idx+1)
      ax = plt.gca() # get Axes instance as it does not force redraw for each call
      plt.title(self.plotData[idx].plotLabel)
      plt.xlabel('samples')
      plt.ylabel(self.plotData[idx].plotUnit)
      plt.ylim(self.plotData[idx].data_range)
      # Iterate over data vector
      for jdx in xrange(len(self.plotData[idx].data)):
        self.lines[idx].insert(jdx, plt.plot(self.plotData[idx].data[jdx], label='%d'%jdx))
      # place legend right of subplot by decreasing plot width to 90%
      box = spl.get_position()
      spl.set_position([box.x0, box.y0, box.width * 0.9, box.height])
      plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

  def show(self):
    plt.show()

  # TOOD: can we use it?...
  def _init_draw(self):
    pass

  def new_frame_seq(self):
      try:
        element = self.my_queue.get_nowait()
      except Queue.Empty:
        pass
      else:
        # handle 'events'
        if (element == "<setup>"):
          self._setup()
        elif (element == "<new_data>"):
          # return iterator with single element
          return iter(range(1,2))
        else:
          print element

      # return empty iterator so that _draw_frame() will not be executed
      return iter(str())

  def _draw_frame(self, framedata):
    for idx in xrange(len(self.plotData)):
      for jdx in xrange(len(self.plotData[idx].data)):
        self.lines[idx][jdx][0].set_ydata(self.plotData[idx].data[jdx])

