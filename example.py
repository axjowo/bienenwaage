#! /usr/bin/python2

import time
import sys
import urllib2
import smbus




######################################################################
# Temperatur #

# number of I2C bus
BUS = 1

# BMP280 address, 0x76 or 0x77
BMP280ADDR = 0x76

# altitude 500 m
ALTITUDE = 500

# get I2C bus
bus = smbus.SMBus(BUS)

# temperature calibration coeff. array
T = [0, 0, 0];
# pressure calibration coeff. array
P = [0, 0, 0, 0, 0, 0, 0, 0, 0];

# read calibration data from 0x88, 24 bytes
data = bus.read_i2c_block_data(BMP280ADDR, 0x88, 24)

# temp coefficents
T[0] = data[1] * 256 + data[0]
T[1] = data[3] * 256 + data[2]
if T[1] > 32767:
  T[1] -= 65536
T[2] = data[5] * 256 + data[4]
if T[2] > 32767:
  T[2] -= 65536

# pressure coefficents
P[0] = data[7] * 256 + data[6];
for i in range (0, 8):
  P[i+1] = data[2*i+9]*256 + data[2*i+8];
  if P[i+1] > 32767:
    P[i+1] -= 65536

# select control measurement register, 0xF4
# 0x27: pressure/temperature oversampling rate = 1, normal mode
bus.write_byte_data(BMP280ADDR, 0xF4, 0x27)

# select configuration register, 0xF5
# 0xA0: standby time = 1000 ms
bus.write_byte_data(BMP280ADDR, 0xF5, 0xA0)

time.sleep(1.0)

# read data from 0xF7, 8 bytes
data = bus.read_i2c_block_data(BMP280ADDR, 0xF7, 8)

# convert pressure and temperature data to 19 bits
adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

# convert pressure and temperature data to 19 bits
adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

# temperature offset calculations
temp1 = ((adc_t)/16384.0 - (T[0])/1024.0)*(T[1]);
temp3 = (adc_t)/131072.0 - (T[0])/8192.0;
temp2 = temp3*temp3*(T[2]);
temperature = (temp1 + temp2)/5120.0

# pressure offset calculations
press1 = (temp1 + temp2)/2.0 - 64000.0
press2 = press1*press1*(P[5])/32768.0
press2 = press2 + press1*(P[4])*2.0
press2 = press2/4.0 + (P[3])*65536.0
press1 = ((P[2])*press1*press1/524288.0 + (P[1])*press1)/524288.0
press1 = (1.0 + press1/32768.0)*(P[0])
press3 = 1048576.0 - (adc_p)
if press1 != 0:
  press3 = (press3 - press2/4096.0)*6250.0/press1
  press1 = press3*press3*(P[8])/2147483648.0
  press2 = press3*(P[7])/32768.0
  pressure = (press3 + (press1 + press2 + (P[6]))/16.0)/100
else:
  pressure = 0
# pressure relative to sea level
pressure_nn = pressure/pow(1 - ALTITUDE/44330.0, 5.255)


###############################################################################













# Enter Your API key here
myAPI = 'NRYBWMETRTZ2Q2DJ' 
# URL where we will send the data, Don't change it
baseURL = 'https://api.thingspeak.com/update?api_key=%s' % myAPI 



EMULATE_HX711=False

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    print "Cleaning..."

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print "Bye!"
    sys.exit()



##########################################################
# Waage 

hx = HX711(5, 6)

# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
hx.set_reading_format("MSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
hx.set_reference_unit(-28)
#hx.set_reference_unit(1)

hx.reset()

#hx.tare()

print "Tare done! Add weight now..."

# to use both channels, you'll need to tare them both
#hx.tare_A()
#hx.tare_B()



        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment these three lines to see what it prints.
        
        # np_arr8_string = hx.get_np_arr8_string()
        # binary_string = hx.get_binary_string()
        # print binary_string + " " + np_arr8_string
        
        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
val = hx.get_weight(5) - 6985
print val

        # To get weight from both channels (if you have load cells hooked up 
        # to both channel A and B), do something like this
        #val_A = hx.get_weight_A(5)
        #val_B = hx.get_weight_B(5)
        #print "A: %s  B: %s" % ( val_A, val_B )

hx.power_down()
hx.power_up()
time.sleep(0.1)
##############################################################

conn = urllib2.urlopen(baseURL + '&field1=%s&field2=%s' % (val,temperature))

print conn.read()
conn.close()


