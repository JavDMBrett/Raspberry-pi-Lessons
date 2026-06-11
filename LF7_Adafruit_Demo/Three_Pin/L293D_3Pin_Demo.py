#!/usr/bin/python3
# ============================================================
# L293D — 3-Pin DEMO (Enable PWM + IN1 + IN2)
# ============================================================
# Wiring:
#   Pi GPIO 16  --> L293D Pin 1 (Enable 1) -- PWM speed control
#   Pi GPIO 20  --> L293D Pin 2 (IN1)      -- direction
#   Pi GPIO 21  --> L293D Pin 7 (IN2)      -- direction
#   L293D Pin 3 (OUT1) + Pin 6 (OUT2) --> Motor
#   L293D Pin 8 (Vs)  --> 9V Battery +
#   L293D Pin 4+5 (GND) --> GND (shared with Pi and Battery -)
#
# DEMO Speed Bands:
#   temp < 25 C         --> OFF
#   temp 25 - 28 C      --> SLOW  (40% PWM)
#   temp 28 - 31 C      --> MEDIUM (70% PWM)
#   temp > 31 C         --> FAST  (100% PWM)
#
# Warm the sensor with your fingers to climb through the bands.
# Watch the speed percentage on the terminal.
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
EN  = PWMLED(16)        # Enable (PWM speed, 0.0-1.0)
IN1 = OutputDevice(20)  # Direction 1 — held HIGH for the whole demo (forward only)
IN2 = OutputDevice(21)  # Direction 2 — held LOW  for the whole demo

# --- Demo speed bands ---
BAND_OFF    = 25    # Below this -> OFF
BAND_SLOW   = 28    # Below this -> SLOW
BAND_MEDIUM = 31    # Below this -> MEDIUM
                    # Above BAND_MEDIUM -> FAST

SPEED_SLOW   = 0.40  # 40% PWM
SPEED_MEDIUM = 0.70  # 70% PWM
SPEED_FAST   = 1.00  # 100% PWM

aio = Client(ada_user, ada_key)

# Set direction to FORWARD for the whole demo
IN1.on()
IN2.off()


def read_temp():
    try:
        data = aio.receive(ada_feed)
        return float(data.value)
    except RequestError:
        print("Adafruit IO: Feed not found")
        return None


def set_speed(value):
    EN.value = max(0.0, min(1.0, value))


def handle_motor():
    temp = read_temp()
    if temp is None:
        return

    if temp < BAND_OFF:
        set_speed(0)
        print(f"Temp: {temp:.1f} C  -->  OFF             (below {BAND_OFF} C)")
    elif temp < BAND_SLOW:
        set_speed(SPEED_SLOW)
        print(f"Temp: {temp:.1f} C  -->  SLOW   {SPEED_SLOW*100:.0f}%  (warm a little more)")
    elif temp < BAND_MEDIUM:
        set_speed(SPEED_MEDIUM)
        print(f"Temp: {temp:.1f} C  -->  MEDIUM {SPEED_MEDIUM*100:.0f}%  (getting warmer!)")
    else:
        set_speed(SPEED_FAST)
        print(f"Temp: {temp:.1f} C  -->  FAST   {SPEED_FAST*100:.0f}%  (maximum speed!)")


def shutdown(sig=None, frame=None):
    set_speed(0)
    IN1.off()
    IN2.off()
    EN.close()
    IN1.close()
    IN2.close()
    print("\nStopped")
    sys.exit(0)


print("=== L293D 3-Pin PWM Demo ===")
print(f"  < {BAND_OFF} C    --> OFF")
print(f"  {BAND_OFF} - {BAND_SLOW} C  --> SLOW   ({SPEED_SLOW*100:.0f}% PWM)  warm sensor gently")
print(f"  {BAND_SLOW} - {BAND_MEDIUM} C  --> MEDIUM ({SPEED_MEDIUM*100:.0f}% PWM)  keep warming")
print(f"  > {BAND_MEDIUM} C    --> FAST   ({SPEED_FAST*100:.0f}% PWM)  hold tight!")
print("============================")

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

while True:
    handle_motor()
    sleep(2)
