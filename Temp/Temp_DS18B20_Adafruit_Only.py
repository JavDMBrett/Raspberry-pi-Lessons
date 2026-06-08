#!/usr/bin/python3

import glob
import time
from Adafruit_IO import Client, Feed, Data, RequestError

# Define the username and key for the Adafruit IO Cloud
ADAFRUIT_IO_USERNAME = 'YOUR_USERNAME'
ADAFRUIT_IO_KEY = 'YOUR_API_KEY'
ADAFRUIT_IO_FEED = 'YOUR_FEED_NAME'

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# A function to read and return the contents of the temp file
def read_temp_raw():
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

# A function to get the temperature in degrees Celsius from the temp file
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    return None

# Check feed exists
try:
    aio.feeds(ADAFRUIT_IO_FEED)
except RequestError:
    print("Feed nicht vorhanden")

# Print and send temperature until the program is stopped.
while True:
    temp = read_temp()
    if temp is not None:
        print(f'Sending temperature {temp:.2f} C to Adafruit IO')
        aio.send(ADAFRUIT_IO_FEED, temp)
    time.sleep(1)
