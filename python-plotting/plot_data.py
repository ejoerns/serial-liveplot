from collections import deque

class ChannelData:
  ''' 
  Holds data for a single channel 
  '''
  # constr
  def __init__(self, vec_size, maxLen, label="Unknown", unit="[]", divisor=1):
    self.vec_size = vec_size 
    self.maxLen = maxLen
    self.plotUnit = unit
    self.plotLabel = label
    self.divisor = divisor
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
    #print "add: ", data
    for idx in range(0, len(data)):
      self.addToBuf(self.data[idx], data[idx] / self.divisor)

