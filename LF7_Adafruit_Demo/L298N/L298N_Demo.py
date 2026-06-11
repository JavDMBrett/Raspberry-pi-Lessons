#!/usr/bin/env python3
# ============================================================
# L298N — Timed Sequence Demo (gpiozero)
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
# Runs a repeating timed sequence:
#   Ramp forward (25% -> 100%) -> STOP -> Ramp backward -> STOP
# Press Ctrl+C to exit cleanly.
# ============================================================

from gpiozero import Motor
from time import sleep
import signal
import sys

# --- Pins (BCM numbering) ---
PIN_IN1 = 24
PIN_IN2 = 25
PIN_ENA = 23

motor = Motor(forward=PIN_IN1, backward=PIN_IN2, enable=PIN_ENA)


def shutdown(sig=None, frame=None):
    motor.stop()
    motor.close()
    print("\n\nStopped.")
    sys.exit(0)


signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

print("=== L298N Timed Sequence Demo ===")
print("  Ctrl+C to stop")
print("=================================\n")

try:
    while True:
        for speed in [0.25, 0.50, 0.75, 1.00]:
            print(f"Forward  {int(speed * 100):>3} %")
            motor.forward(speed)
            sleep(1.5)

        print("STOP")
        motor.stop()
        sleep(1.0)

        for speed in [0.25, 0.50, 0.75, 1.00]:
            print(f"Backward {int(speed * 100):>3} %")
            motor.backward(speed)
            sleep(1.5)

        print("STOP\n")
        motor.stop()
        sleep(1.0)

except KeyboardInterrupt:
    shutdown()
