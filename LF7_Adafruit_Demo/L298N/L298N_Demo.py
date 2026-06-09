#!/usr/bin/python3
# ============================================================
# L298N — Full Demo (ENA PWM + IN1 + IN2)
# ============================================================
# Wiring:
#   Pi GPIO 23  --> L298N ENA  (PWM speed control)
#   Pi GPIO 24  --> L298N IN1  (direction)
#   Pi GPIO 25  --> L298N IN2  (direction)
#   L298N OUT1 + OUT2 --> Motor
#   L298N VCC  --> 9V Battery +
#   L298N GND  --> GND (shared with Pi and Battery -)
#   Remove ENA jumper on L298N module for PWM control
#
# Demo sequence (auto-cycles):
#   1. FORWARD  SLOW   (40%)
#   2. FORWARD  MEDIUM (70%)
#   3. FORWARD  FAST   (100%)
#   4. OFF
#   5. REVERSE  SLOW   (40%)
#   6. REVERSE  MEDIUM (70%)
#   7. REVERSE  FAST   (100%)
#   8. OFF
#   ... repeats
# ============================================================

from time import sleep
import RPi.GPIO as GPIO
import signal
import sys

# --- Pins ---
ENA = 23    # PWM speed control
IN1 = 24    # Direction 1
IN2 = 25    # Direction 2

# --- PWM ---
PWM_FREQ  = 1000   # Hz
SLOW      = 40     # %
MEDIUM    = 70     # %
FAST      = 100    # %
STEP_TIME = 3      # seconds per step

# --- Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

pwm = GPIO.PWM(ENA, PWM_FREQ)
pwm.start(0)


# --- Motor functions ---
def motor_forward(speed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)
    print(f"  FORWARD  {speed}%")

def motor_reverse(speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)
    print(f"  REVERSE  {speed}%")

def motor_off():
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    print("  OFF")

def shutdown(sig, frame):
    motor_off()
    pwm.stop()
    GPIO.cleanup()
    print("\nStopped")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

# --- Demo sequence ---
sequence = [
    (motor_forward, SLOW),
    (motor_forward, MEDIUM),
    (motor_forward, FAST),
    (motor_off,     None),
    (motor_reverse, SLOW),
    (motor_reverse, MEDIUM),
    (motor_reverse, FAST),
    (motor_off,     None),
]

print("=== L298N Full Demo ===")
print(f"ENA=GPIO{ENA}  IN1=GPIO{IN1}  IN2=GPIO{IN2}")
print(f"Cycling every {STEP_TIME} seconds. Ctrl+C to stop.")
print("=======================")

while True:
    for func, speed in sequence:
        if speed is not None:
            func(speed)
        else:
            func()
        sleep(STEP_TIME)
