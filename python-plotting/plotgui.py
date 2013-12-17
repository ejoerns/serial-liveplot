from matplotlib import pyplot as plt

# plot class
class AnalogPlot:
  lines = []
  idx = 0
  # constr
  def __init__(self, plotData):
    # set plot to animated
    plt.ion()
    for idx in xrange(len(plotData)):
      self.lines.insert(idx, [])
      spl = plt.subplot(len(plotData), 1, idx+1)
      plt.title(plotData[idx].plotLabel)
      plt.xlabel('samples')
      plt.ylabel(plotData[idx].plotUnit)
      plt.ylim([-2000, 2023])
      for jdx in xrange(len(plotData[idx].data)):
        self.lines[idx].insert(jdx, plt.plot(plotData[idx].data[jdx], label='%d'%jdx))
      # place legend right of subplot by decreasing plot width to 90%
      box = spl.get_position()
      spl.set_position([box.x0, box.y0, box.width * 0.9, box.height])
      plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.show()

  # update plot
  def update(self, plotData):
    self.idx += 1
    for idx in xrange(len(plotData)):
      for jdx in xrange(len(plotData[idx].data)):
        self.lines[idx][jdx][0].set_ydata(plotData[idx].data[jdx])
    if (self.idx % 10) == 0:
      plt.draw()
      self.idx = 0

