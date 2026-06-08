#!/usr/bin/python3

import glob
import time

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# A function that reads the sensors data
def read_temp_raw():
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

# Convert the value of the sensor into a temperature
# While the first line does not contain 'YES', wait for 0.2 secs
# and then read the device file again.
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()

    # Look for the position of the '=' in the second line of the device file.
    equals_pos = lines[1].find('t=')

    # If the '=' is found, convert into degrees Celsius and Fahrenheit
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

# Print out the temperature until the program is stopped.
while True:
    print(read_temp())
    time.sleep(1)
