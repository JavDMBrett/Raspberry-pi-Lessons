#!/usr/bin/python3
# ============================================================
# L293D — 2-Pin Control (IN1 + IN2, no Enable)
# ============================================================
# Wiring:
#   Pi GPIO 16  --> L293D Pin 2 (IN1)
#   Pi GPIO 20  --> L293D Pin 7 (IN2)
#   L293D Pin 1 (Enable 1) --> 3.3V (always enabled)
#   L293D Pin 3 (OUT1) + Pin 6 (OUT2) --> Motor
#   L293D Pin 8 (Vs)  --> 9V Battery +
#   L293D Pin 4+5 (GND) --> GND (shared with Pi and Battery -)
#
# L293D Truth Table:
#   IN1  IN2  Result
#   HIGH LOW  Motor FORWARD
#   LOW  HIGH Motor REVERSE
#   LOW  LOW  Motor OFF (coast)
#   HIGH HIGH Motor OFF (brake)
#
# Behaviour:
#   Temp too high  --> Motor FORWARD (fan blows air)
#   Temp too low   --> Motor OFF
#   (Bonus demo)   --> Call motor_reverse() to show direction change
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

# --- Pins ---
IN1 = OutputDevice(16)   # Direction pin 1
IN2 = OutputDevice(20)   # Direction pin 2

# --- Thresholds ---
MAX_TEMP  = 30
HYSTERESE =  3

aio = Client(ada_user, ada_key)


def read_temp():
    try:
        data = aio.receive(ada_feed)
        return float(data.value)
    except RequestError:
        print("Adafruit IO: Feed not found")
        return None


def motor_forward():
    IN1.on()
    IN2.off()
    print("Motor FORWARD")


def motor_reverse():
    IN1.off()
    IN2.on()
    print("Motor REVERSE")


def motor_off():
    IN1.off()
    IN2.off()
    print("Motor OFF")


def handle_motor():
    temp = read_temp()
    if temp is None:
        return
    print(f"Temp: {temp:.1f} C")
    if temp > MAX_TEMP:
        motor_forward()
    elif temp < MAX_TEMP - HYSTERESE:
        motor_off()


def shutdown(sig=None, frame=None):
    motor_off()
    IN1.close()
    IN2.close()
    print("\nStopped")
    sys.exit(0)


signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

while True:
    handle_motor()
    sleep(2)
