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
    #plt.ioff()
    self.fig = plt.figure()
    self.win = self.fig.canvas.manager.window
    #self.fig.add_subplot(111)
    self.lines = []
    #self.fig.canvas.mpl_connect('my event', onMyEvent)
    #spl = self.fig.add_subplot(111)
    ax = plt.gca() # get Axes instance as it does not force redraw for each call
    #plt.title('foo')
    #plt.xlabel('samples')
    #plt.ylabel('ylabel')
    animation.TimedAnimation.__init__(self, self.fig, interval=40, blit=True)

  def onMyEvent(self):
    print "looop"
    try:
      element = self.my_queue.get_nowait()
    except Queue.Empty:
      pass
    else:
      # handle 'events'
      if (element == "<setup>"):
        self._setup()
    self.win.after(20, self.onMyEvent) # register method to be executed

  # to be called
  def setup(self, dummyPlotData):
    print "SETUP() called"
    self.my_queue.put("<setup>")

  def _setup(self):
    '''
    plt.ion()
    # Iterate over each channel
    '''
    # clear figure
    plt.clf()
    print "IN GUI len: ", len(self.plotData)
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
    print "****************************"
    '''
    self.fig.canvas.draw()
    plt.show()
    '''

  def show(self):
    plt.show()
    #plt.plot(np.random.rand(20), mfc='g', mec='r', ms=40, mew=4, ls='--', lw=3)
    #self.win.after(100, self.onMyEvent) # register method to be executed
    #plt.ion()
    #animation.TimedAnimation.__init__(self, self.fig, interval=200, blit=True)
    #plt.show()
    #plt.show()
    #print "show end"
    pass

  def _draw_frame(self, framedata):
    #print "_draw_frame", framedata
    idx = 0
    for idx in xrange(len(self.plotData)):
      for jdx in xrange(len(self.plotData[idx].data)):
        self.lines[idx][jdx][0].set_ydata(self.plotData[idx].data[jdx])
    if (idx % 10) == 0:
      plt.draw()
      idx = 0
    pass

  def new_frame_seq(self):
      #print "new_frame_seq"
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

  def _init_draw(self):
    print "_init_draw()"
    '''
    for idx in xrange(len(self.plotData)):
      self.lines.insert(idx, [])
      spl = self.fig.add_subplot(len(self.plotData), 1, idx+1)
      ax = plt.gca() # get Axes instance as it does not force redraw for each call
      plt.title(plotData[idx].plotLabel)
      plt.xlabel('samples')
      plt.ylabel(plotData[idx].plotUnit)
      plt.ylim(plotData[idx].data_range)
      # Iterate over data vector
      for jdx in xrange(len(plotData[idx].data)):
        self.lines[idx].insert(jdx, plt.plot(plotData[idx].data[jdx], label='%d'%jdx))
      # place legend right of subplot by decreasing plot width to 90%
      box = spl.get_position()
      spl.set_position([box.x0, box.y0, box.width * 0.9, box.height])
      plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    '''

  # update plot
  def update(self):
    self.idx += 1
    for idx in xrange(len(self.plotData)):
      for jdx in xrange(len(self.plotData[idx].data)):
        self.lines[idx][jdx][0].set_ydata(self.plotData[idx].data[jdx])
    if (self.idx % 10) == 0:
      plt.draw()
      self.idx = 0

