#!/usr/bin/python3
# ============================================================
# L298N — Keyboard Demo (ENA PWM + IN1 + IN2)
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
# Keys:
#   F = FORWARD
#   R = REVERSE
#   + = Faster  (+10% speed)
#   - = Slower  (-10% speed)
#   S = STOP
#   Q = Quit
# ============================================================

import RPi.GPIO as GPIO
import signal
import sys
import tty
import termios

# --- Pins ---
ENA = 23
IN1 = 24
IN2 = 25

# --- Speed settings ---
PWM_FREQ  = 1000
SPEED_STEP = 10
MIN_SPEED  = 20
MAX_SPEED  = 100

# --- State ---
current_speed     = 50
current_direction = 'STOP'

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

def motor_reverse(speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def motor_stop():
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)

def apply_speed():
    if current_direction == 'FORWARD':
        motor_forward(current_speed)
    elif current_direction == 'REVERSE':
        motor_reverse(current_speed)

def print_status():
    bar = '#' * (current_speed // 5) + '-' * ((MAX_SPEED - current_speed) // 5)
    print(f"\r  {current_direction:<8}  [{bar}]  {current_speed}%    ", end='', flush=True)

def shutdown(sig, frame):
    motor_stop()
    pwm.stop()
    GPIO.cleanup()
    print("\n\nStopped")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)


# --- Read single keypress ---
def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# --- Main ---
print("=== L298N Keyboard Demo ===")
print("  F = Forward   R = Reverse")
print("  + = Faster    - = Slower")
print("  S = Stop      Q = Quit")
print("===========================")
print()
print_status()

while True:
    key = get_key().upper()

    if key == 'F':
        current_direction = 'FORWARD'
        apply_speed()
    elif key == 'R':
        current_direction = 'REVERSE'
        apply_speed()
    elif key == '+' or key == '=':
        current_speed = min(MAX_SPEED, current_speed + SPEED_STEP)
        apply_speed()
    elif key == '-':
        current_speed = max(MIN_SPEED, current_speed - SPEED_STEP)
        apply_speed()
    elif key == 'S':
        current_direction = 'STOP'
        motor_stop()
    elif key == 'Q':
        shutdown(None, None)

    print_status()
