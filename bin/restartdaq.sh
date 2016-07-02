#!/bin/bash

echo killing master frontend
killall fe_master 
pushd /home/newg2/Workspace/aaron-work/italian-testbeam-daq/fast &> /dev/null 
echo starting master frontend
bin/fe_master &> /dev/null &
echo killing daqometer
killall daqometer
echo starting daqometer
python2.7 ../online/start_online.py &> /dev/null &
popd &>/dev/null
echo done
