################################################################################
#
# AVR serial data logger (ASDL)
#
# To be used with the avr-logger library
#
# (c) 2013 by Enrico Joerns
#
################################################################################

from collections import deque

class ChannelPlotData:
  ''' 
  Holds data for a single channel.
  Both general information and a deque with all current data points
  '''
  # constr
  def __init__(self, vec_size, maxLen, label="Unknown", unit="[]", divisor=1, data_range=(-2000, 2000)):
    '''
    vec_size : int
      Vector size of channel (i.e. number of elements)
    maxLen : int
      Maximum number of values held in data deque
    label : str
      Label for channel subplot. May contain additional vec labels in the form [x:y:z]
    unit : str
      Unit for channel subplot
    divisor : int
      Divisor will be applied to each data value before added to que.
      Can be used to fit 'unit'
    data_range : (int, int)
      Default y data range for plot
    '''
    self.maxLen = maxLen
    self.plotUnit = unit
    # do some string magic to extract channel and vector labels
    vec_lbls = None
    tmp = label.rsplit("[")
    ch_lbl = tmp[0].rstrip()
    if (len(tmp) > 1): vec_lbls = tmp[1].rstrip(']').split(':')
    # assign
    self.plotLabel = ch_lbl
    self.vecLabels = vec_lbls
    self.divisor = divisor
    self.data_range = data_range
    # 
    self.vec_size = vec_size # really required?
    self.data = [deque([0.0]*maxLen) for x in xrange(vec_size)]
    print "init with vec_size %d" % (vec_size)

  # ring buffer
  def _addToBuf(self, buf, val):
    if len(buf) < self.maxLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)

  # add data
  def add(self, data):
    '''
    data : [int]
      New data vector for this channel
    '''
    #print "add: ", data
    for idx in range(0, len(data)):
      self._addToBuf(self.data[idx], (0.0 + data[idx]) / self.divisor)

