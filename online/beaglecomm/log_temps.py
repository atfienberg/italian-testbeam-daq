from beagle_class import Beagle
import time
from datetime import datetime
import sys

def main():
    beagle = Beagle("tcp://192.168.7.2:6669", 2000)
    try:
        wait_time = 10 if len(sys.argv) < 3 else float(sys.argv[2])
    except ValueError:
        print 'wait time must be a number. you entered %s' % sys.argv[2]
        sys.exit(0)
    with open("temperaturedata/%s" % sys.argv[1], "w") as outf:
        outf.write('date, time, left, middle, right, top\n')
    while True:
        with open("temperaturedata/%s" % sys.argv[1], "a") as outf:
            temps = [str(beagle.read_temp(j)) for j in xrange(1, 5)]
            print temps
            now = datetime.now()
            outf.write('%s, %s, %s, %s, %s, %s\n' % (('%02i/%02i/%02i' % (now.day, now.month, now.year), '%02i:%02i:%02i' % (now.hour, now.minute, now.second)) + tuple(temps)))
        time.sleep(wait_time)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'need file name'
        sys.exit(0)
    main()
            
