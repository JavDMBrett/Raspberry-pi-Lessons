#!/usr/bin/python3
# ============================================================
# L293D — 3-Pin Control (Enable PWM + IN1 + IN2)
# ============================================================
# Wiring:
#   Pi GPIO 16  --> L293D Pin 1 (Enable 1) -- PWM speed control
#   Pi GPIO 20  --> L293D Pin 2 (IN1)      -- direction
#   Pi GPIO 21  --> L293D Pin 7 (IN2)      -- direction
#   L293D Pin 3 (OUT1) + Pin 6 (OUT2) --> Motor
#   L293D Pin 8 (Vs)  --> 9V Battery +
#   L293D Pin 4+5 (GND) --> GND (shared with Pi and Battery -)
#
# How it works:
#   Enable pin uses PWM (0.0-1.0) to control speed.
#   IN1/IN2 set direction (same truth table as 2-pin variant).
#   Speed is proportional to how far above MAX_TEMP we are —
#   the hotter it gets, the faster the motor runs.
#
# Speed mapping:
#   At MAX_TEMP              --> MIN_SPEED (just starts turning)
#   At MAX_TEMP + TEMP_RANGE --> 100% speed
#
# Uses gpiozero (current recommended GPIO library for Raspberry Pi OS).
# gpiozero handles pin setup, PWM and cleanup automatically.
# ============================================================

from gpiozero import OutputDevice, PWMLED
from time import sleep
import signal
import sys
from Adafruit_IO import Client, RequestError
from ada_secrets import ada_user, ada_key, ada_feed

# --- Pins ---
EN  = PWMLED(16)        # Enable (PWM speed control, 0.0-1.0)
IN1 = OutputDevice(20)  # Direction 1
IN2 = OutputDevice(21)  # Direction 2

# --- Thresholds ---
MAX_TEMP   = 30     # Motor starts above this temperature
HYSTERESE  =  3     # Motor stops below (MAX_TEMP - HYSTERESE)
TEMP_RANGE =  5     # Degrees above MAX_TEMP to reach full speed
MIN_SPEED  = 0.40   # Minimum speed (0.0-1.0) to actually move the motor

aio = Client(ada_user, ada_key)


def read_temp():
    try:
        data = aio.receive(ada_feed)
        return float(data.value)
    except RequestError:
        print("Adafruit IO: Feed not found")
        return None


def set_speed(value):
    """Set motor speed 0.0-1.0."""
    EN.value = max(0.0, min(1.0, value))


def motor_forward(speed=1.0):
    IN1.on()
    IN2.off()
    set_speed(speed)
    print(f"Motor FORWARD @ {speed * 100:.0f}%")


def motor_off():
    set_speed(0)
    IN1.off()
    IN2.off()
    print("Motor OFF")


def calc_speed(temp):
    """Map temperature above MAX_TEMP to a speed between MIN_SPEED and 1.0."""
    excess = temp - MAX_TEMP
    speed = MIN_SPEED + (excess / TEMP_RANGE) * (1.0 - MIN_SPEED)
    return max(MIN_SPEED, min(1.0, speed))


def handle_motor():
    temp = read_temp()
    if temp is None:
        return
    print(f"Temp: {temp:.1f} C")
    if temp > MAX_TEMP:
        motor_forward(calc_speed(temp))
    elif temp < MAX_TEMP - HYSTERESE:
        motor_off()


def shutdown(sig=None, frame=None):
    motor_off()
    EN.close()
    IN1.close()
    IN2.close()
    print("\nStopped")
    sys.exit(0)


signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

while True:
    handle_motor()
    sleep(2)
