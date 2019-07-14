#!/usr/bin/env python

import smbus
import time

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

# output data to screen
print ("Temperature: %.2f C" %temperature)
print ("Pressure:    %.2f hPa " %pressure)
print ("Pressure NN: %.2f hPa " %pressure_nn)

