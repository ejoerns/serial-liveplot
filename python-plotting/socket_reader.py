import socket

from base_reader import BaseReader

class SocketReceiver(BaseReader):
  
    def _device_open(self, **kwargs):
        '''
        Opens a socket.
        Arguments: host=hostname, port=portnumber
        '''
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        print socket.gethostname()
        self._socket.connect((kwargs['host'], kwargs['port']))
        pass

    def _device_read(self):
        ''' 
        Reads from socket.
        '''
        return self._socket.recv(20)

    def _device_close(self):
        ''' 
        Closes connection to socket.
        '''
        self._socket.close()

