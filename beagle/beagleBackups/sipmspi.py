import Adafruit_BBIO.GPIO as GPIO
from spidev import SpiDev
import time
import datetime

spi = SpiDev(1, 0)
spi.mode = 3
spi.max_speed_hz = 200000
#spi.xfer2([0x0])

GPIO.setup("P9_11", GPIO.OUT) # A0 sipm select bit0
GPIO.setup("P9_12", GPIO.OUT) # A1 sipm select bit1
GPIO.setup("P9_13", GPIO.OUT) # A2 sipm select bit2
GPIO.setup("P9_14", GPIO.OUT) # A3 sipm select bit3


GPIO.setup("P9_15", GPIO.OUT) # A5 chip select bit0
GPIO.setup("P9_16", GPIO.OUT) # A6 chip select bit1

#chip select map
# 0: nc
# 1: pga
# 2: temp
# 3: mem


GPIO.output("P9_11", GPIO.LOW)
GPIO.output("P9_12", GPIO.LOW)
GPIO.output("P9_13", GPIO.LOW)
GPIO.output("P9_14", GPIO.LOW)
GPIO.output("P9_15", GPIO.LOW)
GPIO.output("P9_16", GPIO.LOW)

#time.sleep(0.2)

def select_sipm(sipm_number):
        pin_list = ["P9_11", "P9_12", "P9_13", "P9_14"]

        for idx, pin_name in enumerate(pin_list):
                if (sipm_number >> idx & 0x1):
                        GPIO.output(pin_name, GPIO.HIGH)
                else:
                        GPIO.output(pin_name, GPIO.LOW)

        #print "sipm %d selected" % sipm_number


chip_map = { "nc": 0, "pga": 1, "temp": 2, "mem": 3 }

def chip_select(key):
	pin_list = ["P9_15", "P9_16"]
	chip_num = chip_map[key]

	for idx, pin_name in enumerate(pin_list):
		if (chip_num >> idx & 0x1):
			GPIO.output(pin_name, GPIO.HIGH)
		else:
			GPIO.output(pin_name, GPIO.LOW)

	#time.sleep(0.1)


def reset_temperature():
	spi.xfer2([0xff, 0xff, 0xff, 0xff])
	#spi.xfer2([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
	#time.sleep(0.2)
	
	res = spi.xfer2([0x40, 0x00]) # read status register
	print "status: 0x%02x" % res[1]

	res = spi.xfer2([0x48, 0x00]) # read config register
	print "status: 0x%02x" % res[1]

	res = spi.xfer2([0x58, 0x00]) # read ID register
	print "status: 0x%02x" % res[1]

	#time.sleep(0.1)

def setup_temperature():
	spi.xfer2([0x08, 0x80])
	time.sleep(0.2)

def read_temperature():
	res = spi.xfer2([0x50, 0x00, 0x00])
	#temp = (res[1] << 5 | res[2] >> 3) / 16.0
	temp = (res[1] << 8 | res[2]) / 128.0
	print "temp: %f deg C" % temp
	return str(temp)


def read_gain():
	res = spi.xfer2([0x83, 0x00])
	gain_read = res[1]
	print "old gain readout: %d = %f dB" % (gain_read, 26 - gain_read / 4.0)
	return str(gain_read)


def set_gain(gain_value):
	#print read_gain()
        res = spi.xfer2([0x03, gain_value])
	#time.sleep(0.1)

        res = spi.xfer2([0x83, 0x00])
	gain_read = res[1]
        print "new gain readout: %d = %f dB" % (gain_read, 26 - gain_read / 4.0)
	return str(gain_read)

def check_eeprom_status():
	res = spi.xfer2([0x05, 0x00])
	print "eeprom status 0x%02x\n" % res[1]

def read_eeprom_page(page):
	page <<= 4
	cmd = [0x03, page] + [0 for i in range(16)]
	res = spi.xfer2(cmd)
	int_array = res[2:]
	#utf8 safety
	chr_array = [ ' ' if i==255 else chr(i) for i in int_array]
	print ''.join(chr_array)

def write_eeprom_page(page, msg):
	page <<= 4
	#enable write latch
	spi.xfer2([0x06])
	check_eeprom_status()
	#write page
	cmd = [0x02, page] + msg
	res = spi.xfer2(cmd)
	print res
	check_eeprom_status()

#GPIO.cleanup()
#spi.close()


if __name__ == "__main__":

	#sipm_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
	#sipm_list = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	#sipm_list = [8,9,8,9,8,9,8,9,8,9,8,9,8,9,8,9,8,9,8]
	#sipm_list = [9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9]
	#sipm_list = [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
	#sipm_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
	sipm_list = [5,6]

	for sipm in sipm_list:
		print "\n"
		select_sipm(sipm)
		chip_select("mem")
		# #check_eeprom_status()
		# #write_eeprom_page(1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
		read_eeprom_page(1)
		time.sleep(0.1)
		chip_select("pga")
		print read_gain()
		print set_gain(50)
		time.sleep(0.1)
		chip_select("temp")
		#reset_temperature()
		#setup_temperature()
		print read_temperature()
		time.sleep(0.2)

'''
	for step in range(30000):
		temp_readout = []
		for sipm in sipm_list:
			select_sipm(sipm)
			tmp = read_temperature()
			temp_readout.append(tmp)
	
		temp_string = ["%.3f "%(i) for i in temp_readout]
		dump_string = datetime.datetime.now().isoformat() + " "
		dump_string += "".join(temp_string)
		print dump_string	
		time.sleep(20.0)
'''

