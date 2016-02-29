#for communicating with the zmq broker on the beagle board
#to read/set sipm gains/temps 

import zmq

CTXT = zmq.Context()

class Beagle:
    def __init__(self, connection_addr, timeout=200):
        self.socket = CTXT.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.RCVTIMEO, timeout)
        self.socket.connect(connection_addr)

    def read_temp(self, sipm_num):
        self.socket.send("sipm %i temp" % sipm_num)
        try:
            return float(self.socket.recv())
        except zmq.error.Again:
            return "timeout"
        except ValueError:
            return None

    def read_gain(self, sipm_num):
        self.socket.send("sipm %i gain" % sipm_num)
        try:
            return float(self.socket.recv())
        except zmq.error.Again:
            return "timeout"
        except ValueError:
            return None

    def set_gain(self, sipm_num, gain):
        self.socket.send("sipm %i gain %i" % (sipm_num, gain))
        try:
            return float(self.socket.recv())
        except zmq.error.Again:
            return "timeout"
        except ValueError:
            return None


        
def main():
    b = Beagle('tcp://192.168.7.2:6669')
    print b.read_temp(0)
    print b.read_gain(0)
    print b.set_gain(0,50)


if __name__ == "__main__":
    main()
