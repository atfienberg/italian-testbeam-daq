#!/bin/bash

killall fe_master
killall daqometer

sleep 1

DAQDIR='/home/newg2/Applications/lab-daq'
olddir=`pwd`
cd $DAQDIR/fast
./bin/fe_master &> data/log &

cd $DAQDIR/online
python start_online.py &> log &

cd $olddir
unset oldir
