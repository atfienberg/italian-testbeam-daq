#for communicating with the zmq broker on the beagle board
#to read/set sipm gains/temps 

import zmq

CTXT = zmq.context()

class Beagle:
    def __init__(self, connection_addr, timeout=200):
        self.socket = CTXT.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.setsockopt(zmq.RCVTIME, timeout)
        self.socket.connect(connection_addr)

    def read_temp(self, sipm_num):
        self.socket.send("sipm %i temp")
        try:
            return socket.recv()
        except zmq.error.Again:
            return "timeout"
        
