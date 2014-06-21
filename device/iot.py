import sys
import time
import collections

print "IoT ready!"
print "Press CTRL + C to exit"

def iio_enable():
        try:
                iioenable = open("/sys/devices/bone_capemgr.9/slots","w")
                iioenable.write("cape-bone-iio")
                iioenable.close()
        except IOError:
                print "INFO: IIO already enabled, skipping."

def read_adc0():
        fp1 = open("/sys/devices/ocp.3/helper.15/AIN0","r")
        value = fp1.read()
        value = int(value.rstrip())
        return value
        fp1.close()

def read_adc0_raw():
        fp2 =  open("/sys/devices/ocp.3/44e0d000.tscadc/tiadc/iio:device0/in_voltage0_raw","r")
        value = fp2.read()
        value = int(value.rstrip())
	return value
        fp2.close()

def get_adc0_average():
	adc_values = collections.deque(maxlen=10)
	read_adc0() # TI ADC driver sucks, discard first value
	for cycle in xrange(10):
		adc_values.append(read_adc0())
		time.sleep(0.05)
	print "Average of last 10 measurements: %i" % (sum(adc_values)/10)
	return (sum(adc_values)/10)

iio_enable()
while True:
	get_adc0_average()

