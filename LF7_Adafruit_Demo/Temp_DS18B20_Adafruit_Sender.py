#!/usr/bin/python3
# Reads the DS18B20 temperature sensor and pushes the value to Adafruit IO

import glob
import time

from Adafruit_IO import Client, RequestError
from ada_secrets import ada_user, ada_key, ada_feed  # Zugangsdaten aus ada_secrets.py (nicht in git!)

aio = Client(ada_user, ada_key)

# Finds the correct device file that holds the temperature data

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


def read_temp_raw():
    with open(device_file, 'r') as f:
        return f.readlines()


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


# Send the temperature to Adafruit IO every couple of seconds.
# (Free Adafruit IO accounts are rate-limited to ~30 data points/minute,
#  so don't go faster than roughly once every 2 seconds.)

try:
    while True:
        temp = read_temp()
        if temp is not None:
            print(temp)
            try:
                aio.send(ada_feed, temp)
            except RequestError:
                print("Feed nicht vorhanden")
        time.sleep(2)

except KeyboardInterrupt:
    print("Stopped")
