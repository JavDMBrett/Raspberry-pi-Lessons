#!/usr/bin/env python3
# ============================================================
# L298N — Keyboard Demo (gpiozero)
# ============================================================
# Wiring:
#   Pi GPIO 24  --> L298N IN1  (direction)
#   Pi GPIO 25  --> L298N IN2  (direction)
#   Pi GPIO 23  --> L298N ENA  (PWM speed — remove ENA jumper)
#   L298N OUT1 + OUT2 --> Motor
#   L298N VCC  --> 9 V battery +
#   L298N GND  --> GND (shared with Pi and battery -)
#
# Note: gpiozero is the current recommended GPIO library for
# Raspberry Pi OS. It handles pin setup, PWM and cleanup
# automatically, replacing the older RPi.GPIO library which
# is no longer actively developed.
#
# Keys:
#   F = Forward       R = Reverse
#   + = Faster (+10%) - = Slower (-10%)
#   S = Stop          Q = Quit
# ============================================================

from gpiozero import Motor
import signal
import sys
import tty
import termios

# --- Pins (BCM numbering) ---
PIN_IN1 = 24
PIN_IN2 = 25
PIN_ENA = 23

# --- Speed settings (0.0–1.0) ---
SPEED_STEP = 0.10
MIN_SPEED  = 0.20
MAX_SPEED  = 1.00

# --- State ---
current_speed     = 0.50
current_direction = 'STOP'

motor = Motor(forward=PIN_IN1, backward=PIN_IN2, enable=PIN_ENA)


def apply_speed():
    if current_direction == 'FORWARD':
        motor.forward(current_speed)
    elif current_direction == 'REVERSE':
        motor.backward(current_speed)


def print_status():
    pct = int(current_speed * 100)
    filled = pct // 5
    bar = '#' * filled + '-' * (20 - filled)
    print(f"\r  {current_direction:<8}  [{bar}]  {pct}%    ", end='', flush=True)


def shutdown(sig=None, frame=None):
    motor.stop()
    motor.close()
    print("\n\nStopped.")
    sys.exit(0)


signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)


def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


print("=== L298N Keyboard Demo ===")
print("  F = Forward   R = Reverse")
print("  + = Faster    - = Slower")
print("  S = Stop      Q = Quit")
print("===========================\n")
print_status()

while True:
    key = get_key().upper()

    if key == 'F':
        current_direction = 'FORWARD'
        apply_speed()
    elif key == 'R':
        current_direction = 'REVERSE'
        apply_speed()
    elif key in ('+', '='):
        current_speed = min(MAX_SPEED, round(current_speed + SPEED_STEP, 2))
        apply_speed()
    elif key == '-':
        current_speed = max(MIN_SPEED, round(current_speed - SPEED_STEP, 2))
        apply_speed()
    elif key == 'S':
        current_direction = 'STOP'
        motor.stop()
    elif key == 'Q':
        shutdown()

    print_status()
