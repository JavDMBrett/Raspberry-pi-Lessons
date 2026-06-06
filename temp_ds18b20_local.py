#!/usr/bin/env python3

import glob
import time

BASE_DIR = "/sys/bus/w1/devices/"


def find_sensor_file():
    """Find the first DS18B20 sensor folder."""
    sensor_folders = glob.glob(BASE_DIR + "28-*")

    if not sensor_folders:
        raise FileNotFoundError(
            "No DS18B20 sensor found. Check wiring and 1-Wire setup."
        )

    return sensor_folders[0] + "/w1_slave"


def read_temp_raw(sensor_file):
    """Read the raw temperature data from the sensor file."""
    with open(sensor_file, "r") as file:
        return file.readlines()


def read_temp(sensor_file):
    """Read and convert the sensor temperature to Celsius."""
    lines = read_temp_raw(sensor_file)

    while lines[0].strip()[-3:] != "YES":
        time.sleep(0.2)
        lines = read_temp_raw(sensor_file)

    equals_pos = lines[1].find("t=")

    if equals_pos == -1:
        return None

    temp_string = lines[1][equals_pos + 2:]
    temp_c = float(temp_string) / 1000.0

    return temp_c


sensor_file = find_sensor_file()

print("DS18B20 temperature sensor found.")
print(f"Sensor file: {sensor_file}")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
        temperature = read_temp(sensor_file)

        if temperature is not None:
            print(f"Temperature: {temperature:.2f} °C")
        else:
            print("Could not read temperature.")

        time.sleep(1)

except KeyboardInterrupt:
    print()
    print("Program stopped.")
