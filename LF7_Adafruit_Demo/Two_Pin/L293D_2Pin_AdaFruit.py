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
# ============================================================

from time import sleep
import RPi.GPIO as GPIO
from Adafruit_IO import Client, RequestError
from ada_secrets import ada_user, ada_key, ada_feed

# --- Pins ---
IN1 = 16    # Direction pin 1
IN2 = 20    # Direction pin 2

# --- Thresholds ---
MAX_TEMP  = 30
HYSTERESE =  3

# --- Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

aio = Client(ada_user, ada_key)


def read_temp():
    try:
        data = aio.receive(ada_feed)
        return float(data.value)
    except RequestError:
        print("Adafruit IO: Feed nicht vorhanden")
        return None


def motor_forward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor FORWARD")


def motor_reverse():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    print("Motor REVERSE")


def motor_off():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
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


# --- Main loop ---
try:
    while True:
        handle_motor()
        sleep(2)

except KeyboardInterrupt:
    motor_off()

GPIO.cleanup()
