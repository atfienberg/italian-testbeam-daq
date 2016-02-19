#!/bin/bash

#starts zmq broker and sipm worker if they are not running already

#zmq broker
if ! [[ $(ps auxw | grep -v grep | grep beagle-broker) ]]; then 
    echo starting broker
    pushd /home/uw/zmqbroker > /dev/null 
    ./beagle-broker >& /dev/null &
    popd > /dev/null
else
    echo broker already running
fi

#sipm worker
if ! [[ $(ps auxw | grep -v grep | grep zmq-sipm-worker) ]]; then
    echo starting worker
    pushd /home/uw/zmqbroker > /dev/null
    python worker.py >& /dev/null &
    popd > /dev/null
else
    echo worker already running
fi