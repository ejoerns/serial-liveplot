import serial

from base_reader import BaseReader
from base_reader import ReaderError

class SerialReceiver(BaseReader):

    def _device_open(self, **kwargs):
        try:
            self._serial = serial.Serial(port=kwargs['port'], baudrate=kwargs['baudrate'], timeout=0.001) # wait max 1ms for new data
        except serial.serialutil.SerialException as err:
            raise ReaderError(err)

    def _device_read(self):
        ''' 
        Read from device.
        '''
        return self._serial.read(20)

    def _device_close(self):
        ''' 
        Close device.
        '''
        self._serial.close()
        pass

