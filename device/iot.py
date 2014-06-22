import sys
import time
import os
import collections
from twitter import *
import mosquitto

print "IoT ready!"
print "Press CTRL + C to exit"

active_level = 535
calibration = { 0.5 : 178, 1 : 229, 1.5 : 266.5, 2 : 303, 2.5 : 335, 3 : 361.5, 3.5 : 390.5, 4 : 415.5, 4.5 : 439, 5 : 464.5, 5.5 : 488, 6 : 514, 6.5 : 534.5, 7 : 557 }
twitter_user_creds = os.path.expanduser("~/.twitter_oauth")
twitter_consumer_creds = os.path.expanduser("~/.twitter_consumer")
mqtt_creds = os.path.expanduser("~/.mqtt_auth")
mqtt_name = "iot"
mqtt_server = "mqtt.ruecker.fi"
mqtt_port = 1883
mqtt_keepalive = 60


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
	#print "Average of last 10 measurements: %i" % (sum(adc_values)/10)
	return (sum(adc_values)/10)

def get_volume(adc_value):
	volume, tmp = min(calibration.items(), key=lambda (_, v): abs(v - adc_value))
	return volume

def handle_flush(value):
	current_level = value
	new_level = value-1
	state = "flush"
	flushes = collections.deque()
	
	while state != "done":
		if state == "flush":
			initial_level = current_level
			while current_level > new_level:
				current_level = new_level
				new_level = get_adc0_average()
				print "waiting for flush to stop"
			flushes.append(get_volume(initial_level) - get_volume(current_level))
			state = "filling"
			print "flush stopped after %i" % (initial_level - current_level, )
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
	print "We're really done! Total flushed: %i" % (sum(flushes), )
	try:
		twitter.statuses.update(status='Latest flush: %i litres. #IoT' % (sum(flushes), ))
	except:
		print "Something went wrong while sending the tweet: ", sys.exc_info()[1]
	else:
		print "Tweet sent: Latest flush: %i litres. #IoT" % (sum(flushes), ))
	try:
		mqtt.publish("iotoilet/flush/volume", str(sum(flushes)), 1)
	except:
		print "Something went wrong while sending MQTT message: ", sys.exc_info()[1]
	else:
		print "MQTT message: %s; sent to: iotoilet/flush/volume" % (str(sum(flushes)), )

#Enter the dragon
iio_enable()
adc_values_longterm = collections.deque(maxlen=20)

#Initialize Twitter
oauth_token, oauth_secret = read_token_file(twitter_user_creds)
consumer_key, consumer_secret = read_token_file(twitter_consumer_creds)
twitter = Twitter(auth=OAuth(oauth_token, oauth_secret, consumer_key, consumer_secret))

#Initialize MQTT
mqtt_user, mqtt_password = read_token_file(mqtt_creds)
mqtt = mosquitto.Mosquitto(mqtt_name)
mqtt.username_pw_set(mqtt_user, mqtt_password)
mqtt.connect(mqtt_server, mqtt_port, mqtt_keepalive)

while True:
	mqtt.loop()
	adc0_average = get_adc0_average()
	adc_values_longterm.append(adc0_average)
	if adc0_average < active_level:
		adc_max = 0
		for elem in adc_values_longterm:
			if elem > adc_max:
				adc_max = elem
		handle_flush(adc_max)

