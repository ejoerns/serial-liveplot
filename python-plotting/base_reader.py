import threading

class BaseReader(threading.Thread):
    """ This class is based on work by
        Philipp Klaus and can be found on
        https://gist.github.com/4039175 .  """
    def __init__(self, **kwargs):
        self._target = self.read
        self._args = kwargs
        self.__lock = threading.Lock()
        #self._serial = serial.Serial(device, port, timeout=0.001) # wait max 1ms for new data
        self._device_open(**kwargs)
        self.data_buffer = ""
        self.closing = False # A flag to indicate thread shutdown
        #self.sleeptime = 0.00005
        threading.Thread.__init__(self)
        # List of handler functions to notify about new data
        self.dataHandler = []
        # List of handler functions to notify about connection close
        self.closeHandler = []

    def run(self):
        #self._target(*self._args)
        self._target()

    def read(self):
        while not self.closing:
            #time.sleep(self.sleeptime)
            if not self.__lock.acquire(False):
                continue
            try:
                #inbytes = self._serial.read(20)
                inbytes = self._device_read()
                # Notify receivers for each byte received
                for inbyte in inbytes:
                  for h in self.dataHandler:
                    h(ord(inbyte))
            finally:
                self.__lock.release()
        #self._serial.close()
        self._device_close()
        for chandler in self.closeHandler:
          chandler()

    def _device_open(self, **kwargs):
      ''' 
      Open device.
      Parameters are passed as kwargs and depend on implementation
      @note: to implement by concrete class 
      '''
      raise ReaderError("No implementation")

    def _device_read(self, args):
      ''' 
      Read from device.
      @note: to implement by concrete class 
      '''
      raise ReaderError("No implementation")


    def _device_close(self, args):
      ''' 
      Close device.
      @note: to implement by concrete class 
      '''
      raise ReaderError("No implementation")

    def pop_buffer(self):
        # If a request is pending, we don't access the buffer
        if not self.__lock.acquire(False):
            return ""
        buf = self.data_buffer
        self.data_buffer = ""
        self.__lock.release()
        return buf

    def write(data):
        self._serial.write(data)

    def close(self):
        self.closing = True


class ReaderError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
