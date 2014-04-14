import serial

from base_reader import BaseReader

class SerialReceiver(BaseReader):
    """ This class has been written by
        Philipp Klaus and can be found on
        https://gist.github.com/4039175 .  """

    def _device_open(self, **kwargs):
        self._serial = serial.Serial(port=kwargs['port'], baudrate=kwargs['baudrate'], timeout=0.001) # wait max 1ms for new data
        pass

    def _device_read(self):
        ''' 
        Read from device.
        @note: to implement by concrete class 
        '''
        return self._serial.read(20)

    def _device_close(self):
        ''' 
        Close device.
        @note: to implement by concrete class 
        '''
        self._serial.close()
        pass

