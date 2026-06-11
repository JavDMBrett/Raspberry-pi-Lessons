#!/usr/bin/python3
# ============================================================
# L293D — 1-Pin Control (Enable only)
# ============================================================
# Wiring:
#   Pi GPIO 16  --> L293D Pin 1 (Enable 1)
#   L293D Pin 2 (IN1) --> 3.3V (always HIGH)
#   L293D Pin 7 (IN2) --> GND  (always LOW)
#   L293D Pin 3 (OUT1) + Pin 6 (OUT2) --> Motor
#   L293D Pin 8 (Vs)  --> 9V Battery +
#   L293D Pin 4+5 (GND) --> GND (shared with Pi and Battery -)
#
# Behaviour:
#   Enable HIGH = Motor ON (forward only)
#   Enable LOW  = Motor OFF
#   No direction control, no speed control.
#
# Uses gpiozero (current recommended GPIO library for Raspberry Pi OS).
# gpiozero handles pin setup and cleanup automatically.
# ============================================================

from gpiozero import OutputDevice
from time import sleep
import signal
import sys
from Adafruit_IO import Client, RequestError
from ada_secrets import ada_user, ada_key, ada_feed

# --- Pin ---
EN = OutputDevice(16)   # Enable pin -> motor on/off

# --- Thresholds ---
MAX_TEMP  = 30   # degrees C — motor turns ON above this
HYSTERESE =  3   # degrees C — motor turns OFF below (MAX_TEMP - HYSTERESE)

aio = Client(ada_user, ada_key)


def read_temp():
    try:
        data = aio.receive(ada_feed)
        return float(data.value)
    except RequestError:
        print("Adafruit IO: Feed not found")
        return None


def motor_on():
    EN.on()
    print("Motor ON")


def motor_off():
    EN.off()
    print("Motor OFF")


def handle_motor():
    temp = read_temp()
    if temp is None:
        return
    print(f"Temp: {temp:.1f} C")
    if temp > MAX_TEMP:
        motor_on()
    elif temp < MAX_TEMP - HYSTERESE:
        motor_off()


def shutdown(sig=None, frame=None):
    motor_off()
    EN.close()
    print("\nStopped")
    sys.exit(0)


signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

while True:
    handle_motor()
    sleep(2)
