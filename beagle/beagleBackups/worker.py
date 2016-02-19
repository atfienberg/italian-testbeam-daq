import zmq
import time
import setproctitle
import sipmspi
setproctitle.setproctitle("zmq-sipm-worker")

def sipm_control(command_list):
    # get sipm number
    sipm_num = None
    try:
        sipm_num = int(command_list[0])
    except (ValueError, IndexError):
        pass
    finally:
        if sipm_num not in range(16):
            return "ERROR: invalid sipm number"

    sipmspi.select_sipm(sipm_num)
    
    #get chip 
    chip = None
    try:
        chip = command_list[1]
    except IndexError:
        pass
    finally:
        if chip not in ["gain", "temp"]:
            return "ERROR: invalid chip selection"

    if chip == "temp":
        sipmspi.chip_select(chip)
        return sipmspi.read_temperature()
    else:
        sipmspi.chip_select("pga")
        new_gain = None
        try:
            new_gain = int(command_list[2])
        except IndexError:
            return sipmspi.read_gain()
        except ValueError:
            pass
        
        if 0 <= new_gain <= 80:
            return sipmspi.set_gain(new_gain)
        else:
            return "ERROR: invalid gain setting"
        

def process_message(message):
    command_list = message.split()
    print "command list %s" % repr([command for command in command_list])

    if len(command_list) == 0:
        return "ERROR: no commands"
    elif command_list[0] == "sipm":
        return sipm_control(command_list[1:])
    else:
        return "ERROR: invalid request"


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.connect("ipc://beaglebackend.ipc");

    while True:
        print "waiting for request"
        message = socket.recv()
        print "received work request %s" % message
        print "sending back"
        socket.send(process_message(message))


if __name__ == "__main__":
    main()
