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
#   Enable pin uses PWM (0-100% duty cycle) to control speed.
#   IN1/IN2 set direction (same truth table as 2-pin variant).
#   Speed is proportional to how far above MAX_TEMP we are —
#   the hotter it gets, the faster the motor runs.
#
# Speed mapping:
#   At MAX_TEMP            --> MIN_SPEED (just starts turning)
#   At MAX_TEMP + TEMP_RANGE --> 100% speed
# ============================================================

from time import sleep
import RPi.GPIO as GPIO
import signal
import sys
from Adafruit_IO import Client, RequestError
from ada_secrets import ada_user, ada_key, ada_feed

# --- Pins ---
EN  = 16    # Enable (PWM)
IN1 = 20    # Direction 1
IN2 = 21    # Direction 2

# --- Thresholds ---
MAX_TEMP   = 30     # Motor starts above this temperature
HYSTERESE  =  3     # Motor stops below (MAX_TEMP - HYSTERESE)
TEMP_RANGE =  5     # Degrees above MAX_TEMP to reach full speed
MIN_SPEED  = 40     # Minimum PWM % to actually move the motor (overcome inertia)
PWM_FREQ   = 1000   # Hz

# --- Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(EN,  GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

pwm = GPIO.PWM(EN, PWM_FREQ)
pwm.start(0)  # Start with motor off

aio = Client(ada_user, ada_key)


def read_temp():
    try:
        data = aio.receive(ada_feed)
        return float(data.value)
    except RequestError:
        print("Adafruit IO: Feed nicht vorhanden")
        return None


def set_speed(percent):
    """Set motor speed 0-100%. Below MIN_SPEED the motor won't turn."""
    duty = max(0, min(100, percent))
    pwm.ChangeDutyCycle(duty)


def motor_forward(speed=100):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    set_speed(speed)
    print(f"Motor FORWARD @ {speed:.0f}%")


def motor_off():
    set_speed(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("Motor OFF")


def calc_speed(temp):
    """Map temperature above MAX_TEMP to a speed between MIN_SPEED and 100%."""
    excess = temp - MAX_TEMP
    speed = MIN_SPEED + (excess / TEMP_RANGE) * (100 - MIN_SPEED)
    return max(MIN_SPEED, min(100, speed))


def handle_motor():
    temp = read_temp()
    if temp is None:
        return
    print(f"Temp: {temp:.1f} C")
    if temp > MAX_TEMP:
        speed = calc_speed(temp)
        motor_forward(speed)
    elif temp < MAX_TEMP - HYSTERESE:
        motor_off()


# --- Main loop ---
def shutdown(sig, frame):
    motor_off()
    pwm.stop()
    GPIO.cleanup()
    print("\nStopped")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

while True:
    handle_motor()
    sleep(2)
