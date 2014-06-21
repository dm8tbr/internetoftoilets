import sys
import time
import collections

print "IoT ready!"
print "Press CTRL + C to exit"

active_level = 545

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

def handle_flush(value):
	current_level = value
	new_level = value-1
	state = "flush"
	
	while state != "done":
		if state == "flush":
			while current_level > new_level:
				current_level = new_level
				new_level = get_adc0_average()
				print "waiting for flush to stop"
			state = "filling"
			print "flush stopped at %i" % (current_level, )
		elif state == "filling":
			while current_level <= new_level and state == "filling":
				new_level = get_adc0_average()
				if current_level >= active_level:
					print "We're done here!"
					state = "done"
				elif current_level > new_level:
					print "We're gone back to flushing."
					state = "flush"
				else:
					current_level = new_level
					print "waiting for full or flush"
	print "We're really done!"

iio_enable()
while True:
	adc0_average = get_adc0_average()
	if adc0_average < active_level:
		handle_flush(adc0_average)

