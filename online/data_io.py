#Aaron Fienberg
#Fienberg@uw.edu
#grabs data for the online SLAC daq display
#


import numpy as np
from time import sleep, time
import threading
import Queue
from flask.ext.socketio import emit
import gevent

import zmq, json, os

cwd = os.path.dirname(os.path.realpath(__file__))
conf = json.load(open(os.path.join(cwd, '../fast/config/.default_master.json')))

data = {}
hists = {}
trace = np.zeros(1024)
wireX = []
wireY = []
run_over = threading.Event()

rate = 0 
eventCount = 0



def clear_data():
    global data
    global hists
    global wireX
    global wireY
    global rate
    global eventCount
    data = {}
    hists = {}
    wireX = []
    wireY = []
    rate = 0
    eventCount = 0
    
    generate_data.counter = 0

def pulse_shape(t):
    return -1.0*np.exp(-(t)/5.0)*(1-np.exp(-(t)/1.0))
    
def fill_trace():
    trace = np.array(xrange(50))
    return pulse_shape(trace)

def pull_event(e, start):
    """The function constantly tries to pull new event data which arrives
    in json format. The basic structure of the data is as follows:
    {
        "run_number":run_number, # @bug Hardcoded for now
        
        "event_number":event_number # @bug Hardcoded for now
        
        "sis_fast_<id>:{
            "system_clock":value,
            "device_clock":array[4],
            "trace":array[4][1024]
        },

        "sis_slow_<id>:{
            "system_clock":value,
            "device_clock":array[8],
            "trace":array[8][1024]
        },

        "caen_adc_<id>:{
            "system_clock":value,
            "device_clock":array[8],
            "value":array[8]
        }
    }

    """
    global rate
    global eventCount
    global trace
    global hists
    global data

    context = zmq.Context()
    data_sck = context.socket(zmq.PULL)
    data_sck.bind(conf['writers']['online']['port'])
    last_message = ''
    message = ''

    while not run_over.isSet():

        try:
            last_message = message

            nevents = data_sck.poll(200)
            if nevents > 0:
                message = data_sck.recv()

            if (message[0:7] == '__EOB__'):
                print 'got EOB'
                continue

            data = json.loads(message.split('__EOM__')[0])
            if generate_data.counter != generate_data.maxsize:
                generate_data.counter += 1
            
            for device in data:
                try:
                    num_chans = len(data[device]['trace'])
                    for i in xrange(num_chans):
                        this_dev = device + ' channel ' + str(i)
                        if this_dev not in hists:
                            hists[this_dev] = []
                        hists[this_dev].append(max(data[device]['trace'][i]))
                except:
                    pass
                try:
                    num_adc_chans = len(data[device]['value'])
                    for j in xrange(num_adc_chans):
                        this_adc = device + ' channel ' + str(j)
                        if this_adc not in hists:
                            hists[this_adc] = []
                        hists[this_adc].append(data[device]['value'][j])
                    wireX.append(np.random.standard_normal(1)[0])
                    wireY.append(np.random.standard_normal(1)[0])
                except:
                    pass
                    
            eventCount = data['event_number']
            rate = float(eventCount)/(time()-start)

        except:
            pass

        sleep(1000e-6)

pull_event.event_data = Queue.Queue()


def generate_data(e, data):
    while not run_over.isSet():
        if generate_data.counter != generate_data.maxsize:
            generate_data.counter += 1
            
        now = time()
        past = generate_data.times.get()
        generate_data.times.put(now)
        

        global rate
        global eventCount
        global trace
        eventCount+=1

        trace = np.random.standard_normal(len(trace))
        data.append(trace.max())
        
        rate = float(generate_data.counter)/(now-past)

        sleep(0.1)
generate_data.maxsize = 10
generate_data.counter = 0
generate_data.times = Queue.Queue(maxsize=generate_data.maxsize)


def begin_run():
    global run_over
    print 'starting'
    run_over.clear()
    clear_data()
    start = time()
    for unused_i in xrange(10):
        generate_data.times.put(start)

    #t = threading.Thread(name='data-generator', target=generate_data, args=(run_over,data))
    t = threading.Thread(name='data-puller', target=pull_event, args=(run_over, start))

    print 'starting'
    t.start()

def end_run():
    global run_over
    run_over.set()
    for i in xrange(10):
        generate_data.times.get()
