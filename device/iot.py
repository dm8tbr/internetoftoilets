import sys
import time

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
        value = value.rstrip()
        return value
        fp1.close()

def read_adc0_raw():
        fp2 =  open("/sys/devices/ocp.3/44e0d000.tscadc/tiadc/iio:device0/in_voltage0_raw","r")
        value = fp2.read()
        value = value.rstrip()
	return value
        fp2.close()

iio_enable()
while True:
        adc_value =  read_adc0()
        adc_raw_value = read_adc0_raw()
        print "ADC0 values: %s %s " % (adc_value, adc_raw_value, ) 
