#Aaron Fienberg
#Fienberg@uw.edu
#online display for SLAC test beam run

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory, redirect, url_for
from flask import g, request, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from uuid import uuid4
import couchdb
from couchdb.design import ViewDefinition
import os, glob, datetime
import threading
import collections

import serial

import data_io
import zmq, json
from time import sleep, time
from setproctitle import setproctitle

# Set process name
setproctitle("daqometer")

# global parameters
# flag denoting whether or not a run is in progress
running = False
# current working directory
cwd = os.path.dirname(os.path.realpath(__file__))

#setup flask app
app = Flask(__name__)
app.config.update(dict(
    UPLOAD_FOLDER=cwd+'/uploads',
    IMAGE_UPLOADS=['.jpg', '.jpe', '.jpeg', '.png', '.gif', '.svg', '.bmp'],
    DEBUG=True))
app.config['SECRET_KEY'] = '\xf5\x1a#qx%`Q\x88\xd1h4\xc3\xba1~\x16\x11\x81\t\x8a?\xadF'
socketio = SocketIO(app, async_mode='eventlet')


#Define attributes of a run
run_info = {}
run_info['db_name'] = 'lab_db'
run_info['attr'] = ['Description', 'Bias Voltage', 'Temperature']
run_info['log_info'] = ['Events', 'Rate', 'Start Date', 'Start Time', 'End Date', 'End Time']
run_info['runlog'] = 'runlog.csv'

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html', in_progress=running), 404

@app.route('/')
def home():
    """display home page of online DAQ"""
    return render_template('home.html', in_progress=running)

@app.route('/new')
def new_run():
    """User wants to start a new run. Load the data from 
    the previous run and prompt user for summary information"""
    
    last_data = {}
    if last_run_number() != 0:
        last_data = get_last_data()
        last_data['Description'] = ''

    return render_template('new_run.html', info=run_info, data=last_data, 
                           last=last_run_number(), new=True, in_progress=running)

@app.route('/start', methods=['POST'])
def start_run():
    """Check user form for completion. If it is complete, start the run.
    This entails saving the user configuration in couchdb and 
    launching the data getter and emitter"""
    global running
    data = copy_form_data(run_info, request)
    if running:
        error = 'There is already a run in progress!'
        return render_template('new_run.html', info=run_info, 
                               last=last_run_number(), data=data, error=error, new=True,
                               in_progress=running)

    complete = check_form_data(run_info, data)
    if not complete:
        error = "All fields in the form must be filled."
        return render_template('new_run.html', info=run_info, 
                               last=last_run_number(), data=data, error=error, new=True,
                               in_progress=running)

    # Send a start run signal to fe_master.
    context = zmq.Context()

    handshake_sck = context.socket(zmq.REQ)
    handshake_sck.setsockopt(zmq.LINGER, 0);
    start_sck = context.socket(zmq.PUSH)
    start_sck.setsockopt(zmq.LINGER, 0)

    conf = json.load(open(os.path.join(cwd, '../fast/config/.default_master.json')))
    start_sck.connect(conf['trigger_port'])
    handshake_sck.connect(conf['handshake_port'])

    msg = "CONNECT"
    handshake_sck.send(msg)
    reply = ""
    sleep(0.2) #give fast-daq chance to reply
    try:
        reply = handshake_sck.recv(zmq.NOBLOCK)
    except zmq.error.Again:
        error = "fast-daq not responding (is it running?)"
        return render_template('new_run.html', info=run_info, 
                               last=last_run_number(), data=data, error=error, new=True,
                               in_progress=running)
    else:
        if reply == msg:
            # Connection established.
            start_sck.send("START:%05i:" % (last_run_number() + 1))
    finally:
        handshake_sck.close()
        start_sck.close()
        context.destroy()           
    
    #save the run info
    db = connect_db(run_info['db_name'])
    data['run_number'] = last_run_number() + 1
    now = datetime.datetime.now()
    data['Start Date'] = "%02i/%02i/%04i" % (now.month, now.day, now.year)
    data['Start Time'] = "%02i:%02i" % (now.hour, now.minute)
    db.save(data)

    #start the run and launch the data emitter
    running = True
    data_io.begin_run()

    t = threading.Thread(name='emitter', target=send_events)
    t.start()
    
    broadcast_refresh()
    
    return redirect(url_for('home'))

@app.route('/end')
def end_run():
    """Ends the run, broadcasts a refresh message to all clients"""

    # Send a stop run signal to fe_master.
    context = zmq.Context()
    handshake_sck = context.socket(zmq.REQ)
    handshake_sck.setsockopt(zmq.LINGER, 0);
    stop_sck = context.socket(zmq.PUSH)
    stop_sck.setsockopt(zmq.LINGER, 0)

    conf = json.load(open(os.path.join(cwd, '../fast/config/.default_master.json')))
    stop_sck.connect(conf['trigger_port'])
    handshake_sck.connect(conf['handshake_port'])

    msg = "CONNECT"
    handshake_sck.send(msg)
    if (handshake_sck.recv() == msg):
        # Connection established.
        stop_sck.send("STOP:")

    handshake_sck.close()
    stop_sck.close()
    context.destroy()

    global running
    if running:
        running = False
        data_io.end_run()

    data = get_last_data()
    data['Events'] = data_io.eventCount
    data['Rate'] = "%.1f" % data_io.rate
    now = datetime.datetime.now()
    data['End Date'] = "%02i/%02i/%04i" % (now.month, now.day, now.year)
    data['End Time'] = "%02i:%02i" % (now.hour, now.minute)

    db = connect_db(run_info['db_name'])
    db.save(data)

    sleep(0.1)
    broadcast_refresh()

    context.destroy()

    return redirect(url_for('running_hist'))

@app.route('/hist')
def running_hist():
    """displays an online histogram"""
    if len(data_io.hists)==0:
        return render_template('no_data.html', in_progress=running)

    if 'device' not in session:
        session['device'] = 'sis_fast_0'
    if 'channel' not in session:
        session['channel'] = 0

    if 'refresh_rate' not in session:
        session['refresh_rate'] = 1.

    devices = []
    for device in data_io.data:
        try:
            num_chans = len(data_io.data[device]['trace'])
            for i in xrange(num_chans):
                devices.append(device + ' channel ' + str(i))
        except:
            pass
        try:
            num_chans = len(data_io.data[device]['value'])
            for j in xrange(num_chans):
                devices.append(device + ' channel ' + str(j))
        except:
            pass

    current_selection = session['device'] + ' channel ' + str(session['channel'])

    return render_template('hist.html', in_progress=running, 
                           r_rate=session['refresh_rate'], options=devices, 
                           selected=current_selection)

@app.route('/traces')
def traces():
    """Displays online traces"""
    if len(data_io.hists)==0:
        return render_template('no_data.html', in_progress=running)
    
    if 'device' not in session:
        session['device'] = 'sis_fast_0'
    if 'channel' not in session:
        session['channel'] = 0

    devices = []
    for device in data_io.data:
        try:
            num_chans = len(data_io.data[device]['trace'])
            for i in xrange(num_chans):
                devices.append(device + ' channel ' + str(i))
        except:
            continue

    current_selection = session['device'] + ' channel ' + str(session['channel'])

    if 'refresh_rate' not in session:
        session['refresh_rate'] = 1.

    return render_template('traces.html', options=devices, 
                           r_rate=session['refresh_rate'],
                           selected=current_selection, in_progress=running)

@app.route('/controls')
def controls():
    return render_template('controls.html', in_progress=running)

# @app.route('/beam')
# def beam_display():
#     """displays wire chamber hists"""
#     if len(data_io.hists)==0:
#         return render_template('no_data.html', in_progress=running)
    
#     if 'b_refresh_rate' not in session:
#         session['b_refresh_rate'] = 1.

#     return render_template('beam_monitor.html',
#                            r_rate=session['b_refresh_rate'],
#                            in_progress=running)

@app.route('/nodata')
def no_data():
    """Displays a message if someone tries to draw a histogram when no data
    is available"""
    return render_template('no_data.html', in_progress=running)

@app.route('/revision_select')
def revision_select():
    """display page where user can select a run to revise"""
    last = last_run_number()
    if last < 10:
        end = 0
    else:
        end = last - 10
    
    return render_template("revision_select.html", 
                           in_progress=running,
                           last_ten=range(last,end,-1))

@app.route('/revise/<string:run_num>')
def revise(run_num):
    """display page for revising the given run"""
    try:
        old_data = get_run_data(int(run_num))
        session['revision_number']=run_num
        return render_template('revise.html', num=run_num, 
                               info=run_info, data=old_data,
                               in_progress=running)
    except:
         return render_template('no_run.html')

@app.route('/save_revision', methods=['POST'])
def save_revision():
    """save run revision information"""
    new_data = copy_form_data(run_info, request)
    complete = check_form_data(run_info, new_data)
    if not complete:
        error = "All fields in the form must be filled."
        return render_template('revise.html',num=session['revision_number'], 
                               info=run_info, data=new_data,error=error, 
                               in_progress=running)
        
    #save the revision    
    data = {}
    try:
        data = get_run_data(int(session['revision_number']))
    except:
        error = 'error saving revision!'
        return render_template('revise.html',num=session['revision_number'], 
                               info=run_info, data=new_data,error=error, 
                               in_progress=running)
    for attr in run_info['attr']:
        data[attr] = new_data[attr]

    db = connect_db(run_info['db_name'])
    db.save(data)
    return render_template('revision_success.html', in_progress=running)

@app.route('/runlog')
def runlog():
    """renders page from which user can request the runlog"""
    runlog_path = upload_path(run_info['runlog'])
    return render_template('runlog.html', in_progress=running,
                           path=runlog_path)
@app.route('/<path:filename>')
def get_upload(filename):
    """Return the requested file from the server."""
    filename = os.path.basename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/nEvents')
def n_events_query():
    return repr(data_io.eventCount)

def send_events():
    """sends data to the clients while a run is going"""
    last = last_run_number()
    while not data_io.run_over.isSet():
        sleep(0.1)
        socketio.emit('event info', {"count" : data_io.eventCount, "rate" : data_io.rate, 
                                     "runNumber" : last },
                      namespace='/online')
        

@socketio.on('update histogram', namespace='/online')
def update_hist(msg):
    """send data to client needed to make histogram"""
    try:
        selection = msg['selected'].split(' ')
        device = selection[0]
        channel = int(selection[-1])
        this_dev = device + ' channel ' + str(channel)

        title = 'Run %i Event %i, %s channel %i' % (last_run_number(), 
                                                    data_io.eventCount,
                                                    device, 
                                                    channel)              

        data = [['amplitudes']]
        data.extend([[i] for i in data_io.hists[this_dev]])
        emit('histogram ready', {"title" : title, "data" : data});
    except:
        pass    
        
@socketio.on('update trace', namespace='/online')
def update_trace(msg):
    """send data to client needed to make trace"""
    try: 
        xmin = int(msg['x_min'])
        xmax = int(msg['x_max'])
        if xmin < 0:
            xmin = 0
        if xmax > 1024:
            xmax = 1024
        if xmin >= xmax:
            xmin = 0
            xmax = 1024
    except:
        xmin = 0
        xmax = 1024

    selection = msg['selected'].split(' ')

    device = selection[0]
    channel = int(selection[-1])
    
    title = 'Run %i Event %i, %s channel %i' % (last_run_number(), data_io.eventCount,
                                                device, channel)
                  
    data = [['sample', 'adc counts']]

    data.extend([[i, data_io.data[device]['trace'][channel][i]] for i in xrange(xmin, xmax)])
    emit('trace data', {'title' : title, 'data' : data})

def get_runlog_headers():
    runlog_headers = 'Run#'
    for attr in run_info['attr']:
        runlog_headers += ', ' + attr
    for info in run_info['log_info']:
        runlog_headers += ', ' + info
    return runlog_headers

@socketio.on('runlog data', namespace='/online')
def send_runlog(msg):
    """generate runlog data and send it"""
    n_rows = 0
    try:
        n_rows = int(msg['n_rows'])
    except ValueError:
        emit('bad row value')
        return
    if n_rows < 1:
        emit('bad row value')
        return        

    rows = []
    rows.append(get_runlog_headers().split(','))
    last = last_run_number()
    if(n_rows > last):
        n_rows = last
    view = db.view('_design/all/_view/all', descending=True)[last:last-n_rows+1]
    for doc in view:
        data = doc['value']
        thisRow = []
        if 'run_number' in data:
            thisRow.append(str(data['run_number']))
        else:
            thisRow.append('N/A')
        for attr in run_info['attr']:
            if attr in data:
                thisRow.append(str(data[attr]))
            else: 
                thisRow.append('N/A')
        for info in run_info['log_info']:
            if info in data:
                thisRow.append(str(data[info]))
            else:
                thisRow.append('N/A')
        rows.append(thisRow)
    emit('rows: ', rows)

@socketio.on('generate runlog', namespace='/online')
def generate_runlog():
    '''generates the runlog from db'''
    #generate column headers
    start = time()
    runlog_headers = get_runlog_headers()

    #fill runlog lines with database info
    runlog_lines = collections.deque()
    db = connect_db(run_info['db_name'])
    n_runs = get_last_data()['run_number']
    counter = 0
    for doc in db.view('_design/all/_view/all'):
        data = doc['value']
    
        runlog_lines.appendleft('')
        if 'run_number' in data:
            runlog_lines[0] += str(data['run_number'])
        else:
            runlog_lines[0] += 'N/A'
        for attr in run_info['attr']:
                if attr in data:
                    runlog_lines[0] += ', ' + str(data[attr])
                else: 
                    runlog_lines[0] += (', N/A')
        for info in run_info['log_info']:
            if info in data:
                runlog_lines[0] += ', ' + str(data[info])
            else:
                runlog_lines[0] += (', N/A')

        counter+=1
        progress = 100*float(counter)/n_runs

        emit('progress', "%02i%s Generated" % 
             (progress, "%"))
    
    #write the file
    with open(app.config['UPLOAD_FOLDER']+'/'+run_info['runlog'], 'w') as runlog:
        runlog.write(runlog_headers)
        for line in runlog_lines:
            runlog.write('\n' + line)
    
    emit('runlog ready')


@socketio.on('refreshed', namespace='/online')
def on_refresh():
    """when a client refreshes his page, this ds him a fresh batch of data"""
    if running:
        emit('event info', {"count" : data_io.eventCount, "rate" : data_io.rate})

def read_serial(s, terminator='\n'):
    """tries to read one byte at a time but breaks if timeout"""
    response = ''
    while True:
        old_len = len(response)
        response += s.read(1)
        try:
            if response[-1] == terminator:
                break
        except IndexError:
            #timed out
            break
        if len(response) == old_len:
            #timed out
            break
        response = response.strip()
    return response.strip()

@socketio.on('filter position?', namespace='/online')
def query_filter_position():
    filter = serial.Serial('/dev/filterwheel', 115200, timeout=1)
    filter.write('pos?\r')
    counter = 0
    while True:
        try:
            response = read_serial(filter, '>')
            if(response[-1] == '>'):
                emit('filter position is: ', {'position' : response[-2]})
                return
        except IndexError:
            counter += 1
            sleep(0.01)
            if counter == 500:
                return

@socketio.on('new filter wheel setting', namespace='/online')
def new_filter_wheel_setting(msg):
    badValue = False
    try:
        new_setting = int(msg['new_setting'])
    except ValueError:
        badValue = True
    if not badValue and new_setting < 7 and new_setting > 0:
        filter = serial.Serial('/dev/filterwheel', 115200, timeout=1)
        filter.write('pos=%s\r' % repr(new_setting))
        read_serial(filter)
        emit('filter moved')
    else:
        emit('invalid setting')

@socketio.on('bk status', namespace='/online')
def query_bk_status():
    bk = serial.Serial('/dev/keyspan', 4800, timeout=1)

    #make sure we are current limited at desired level
    current_limit = 0.005
    #seems to like being made contact with initially
    bk.write('*IDN?\n')
    read_serial(bk)

    try: 
        bk.write('SOUR:CURR?\n')
        response = ''
        response = read_serial(bk) 
        if float(response) != current_limit:
            bk.write('SOUR:CURR % .4f\n' % current_limit)
            bk.write('SOUR:CURR?\n')
            response = read_serial(bk)
            if float(response) != current_limit:
                #failed to set current limit, return here
                emit('bk failure')
                return
    except ValueError:
        #couldn't convert to float for some reason, something weird happening
        emit('bk failure')
        return

    status = {}

    #get output status
    bk.write('OUTP:STAT?\n')
    status['output'] = read_serial(bk)
    
    #get set point
    bk.write('SOUR:VOLT?\n')
    status['set_pt'] = read_serial(bk)
    
    #get measured voltage
    bk.write('MEAS:VOLT?\n')
    status['measured'] = read_serial(bk)
    
    bk.write('SOUR:CURR?\n')
    status['i_limit'] = read_serial(bk)

    emit('bk status is', status)

@socketio.on("toggle bk power", namespace='/online')
def toggle_bk_power():
    bk = serial.Serial('/dev/ttyUSB1', 4800, timeout=0.5)

    #really seems to need two commands to start out for some reason
    bk.write('*idn?\nOUTP:STAT?\n')
    read_serial(bk)
    
    bk_on = False
    try:
        bk_on = int(read_serial(bk)) == 1
    except ValueError:
        #something didn't work
        return 
    
    if bk_on:
        bk.write('OUTP:STAT 0\n')
    else:
        bk.write('OUTP:STAT 1\n')
    
    sleep(1)
    emit('bk changed')        

@socketio.on("new voltage pt", namespace='/online')
def new_bk_voltage(msg):
    new_voltage = 0
    try:
        new_voltage = float(msg['new_setting'])
    except ValueError:        
        emit('invalid bk setting')
        return
        
    #temporary limits for now
    v_low = 0
    v_high = 70.0
    if new_voltage < v_low or new_voltage > v_high:
        emit('invalid bk setting')
        return

    bk = serial.Serial('/dev/ttyUSB1', 4800, timeout=0.5)
    
    bk.write("*IDN?\n")
    read_serial(bk)
    bk.write('SOUR:VOLT % .4f\n' % new_voltage)
    bk.write('SOUR:VOLT?\n')
    try:
        if float(read_serial(bk)) == new_voltage:
            emit('bk changed')
        else: 
            emit('bk failure')
    except:
        emit('bk failure')        

def broadcast_refresh():
    """tells all clients to refresh their pages. This is called when a run begins
    or ends"""
    socketio.emit('refresh', {'data': ''}, namespace='/online')
   
def unique_filename(upload_file):
     """Take a base filename, add characters to make it more unique, and ensure that it is a secure filename."""
     filename = os.path.basename(upload_file).split('.')[0]
     filename += '-' + str(uuid4().hex[-12:])
     filename += os.path.splitext(upload_file)[1]
     return secure_filename(filename)

def upload_path(filename):
    """Construct the full path of the uploaded file."""
    basename = os.path.basename(filename)
    return os.path.join(cwd+
                        '/uploads', basename)

def copy_form_data(info, req):
    """Copy the data in the form that is filled out."""
    data = {}
    for key in info['attr']:
        data[key] = req.form[key]

    return data

def get_last_data():
    """get data for the last run"""
    db = connect_db(run_info['db_name'])
    last = last_run_number()
    try:
        return iter(db.view('_design/all/_view/all', descending=True)[last]).next()['value']
    except (KeyError, StopIteration):
        return {}

def get_run_data(run_num):
    """get data for a given run"""
    db = connect_db(run_info['db_name'])
    data = {}
    try:
        data = iter(db.view('_design/all/_view/all')[run_num]).next()['value']
    except StopIteration:
        pass
    return data

def check_form_data(info, data):
    """Check each spot in the form data."""
    for key in info['attr']:
        if data[key] == '':
            return False

    return True

def connect_db(db_name):
    """Connect to the database if open, and start database if not running."""
    try:
        client = couchdb.Server()

    except:
        subprocess.call(['couchdb', '-b'])
        time.sleep(2)
        client = couchdb.Server()

    try:
        db = client[db_name]

    except:
        client.create(db_name)
        db = client[db_name]

    return db

def last_run_number():
    """determines the last run number by looking in the database"""
    db = connect_db(run_info['db_name'])
    try:
        return db.view('_design/all/_view/all').total_rows
    except:
        return 0

if __name__ == '__main__':
    #create permanent view to all if one doesn't exist
    db = connect_db(run_info['db_name'])    
    if '_design/all' not in db:
        view_def = ViewDefinition('all', 'all',''' 
				  function(doc) { 
				      if( doc.run_number )
					  emit(parseInt(doc.run_number), doc);
				  }''')
        couch = couchdb.Server()
        db = couch[run_info['db_name']]
        view_def.sync(db)
        if '_design/all' not in db:
            print 'error: cannot create view. Do you have credentials?'
            sys.exit(0)

    socketio.run(app, host='0.0.0.0')
