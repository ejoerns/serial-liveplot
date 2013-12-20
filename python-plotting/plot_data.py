from collections import deque

class ChannelPlotData:
  ''' 
  Holds data for a single channel 
  '''
  # constr
  def __init__(self, vec_size, maxLen, label="Unknown", unit="[]", divisor=1, data_range=(-2000, 2000)):
    self.maxLen = maxLen
    self.plotUnit = unit
    self.plotLabel = label
    self.divisor = divisor
    self.data_range = data_range
    # 
    self.vec_size = vec_size # really required?
    self.data = [deque([0.0]*maxLen) for x in xrange(vec_size)]
    print "init with vec_size %d" % (vec_size)

  # ring buffer
  def addToBuf(self, buf, val):
    if len(buf) < self.maxLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)

  # add data
  def add(self, data):
    #print "add: ", data
    for idx in range(0, len(data)):
      self.addToBuf(self.data[idx], data[idx] / self.divisor)

