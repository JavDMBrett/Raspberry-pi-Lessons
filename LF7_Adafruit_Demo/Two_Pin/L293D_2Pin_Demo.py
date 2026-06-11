#!/usr/bin/python3
# ============================================================
# L293D — 2-Pin DEMO (IN1 + IN2)
# ============================================================
# Wiring:
#   Pi GPIO 16  --> L293D Pin 2 (IN1)
#   Pi GPIO 20  --> L293D Pin 7 (IN2)
#   L293D Pin 1 (Enable 1) --> 3.3V (always enabled)
#   L293D Pin 3 (OUT1) + Pin 6 (OUT2) --> Motor
#   L293D Pin 8 (Vs)  --> 9V Battery +
#   L293D Pin 4+5 (GND) --> GND (shared with Pi and Battery -)
#
# DEMO Temperature Zones:
#   temp > 30 C       --> FORWARD  (warm sensor with fingers)
#   temp 25 - 30 C    --> OFF      (dead zone)
#   temp < 25 C       --> REVERSE  (blow on sensor / cool it)
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
IN1 = OutputDevice(16)
IN2 = OutputDevice(20)

# --- Demo thresholds ---
TEMP_FORWARD = 30    # Above this        -> FORWARD
TEMP_OFF     = 27    # Below this        -> OFF
TEMP_REVERSE = 25    # Below this        -> REVERSE

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


def motor_reverse():
    IN1.off()
    IN2.on()


def motor_off():
    IN1.off()
    IN2.off()


def handle_motor():
    temp = read_temp()
    if temp is None:
        return

    if temp > TEMP_FORWARD:
        motor_forward()
        print(f"Temp: {temp:.1f} C  -->  Motor FORWARD   (above {TEMP_FORWARD} C)")
    elif temp > TEMP_OFF:
        motor_off()
        print(f"Temp: {temp:.1f} C  -->  Motor OFF       ({TEMP_OFF}-{TEMP_FORWARD} C zone)")
    elif temp > TEMP_REVERSE:
        motor_off()
        print(f"Temp: {temp:.1f} C  -->  Motor OFF       ({TEMP_REVERSE}-{TEMP_OFF} C zone)")
    else:
        motor_reverse()
        print(f"Temp: {temp:.1f} C  -->  Motor REVERSE   (below {TEMP_REVERSE} C)")


def shutdown(sig=None, frame=None):
    motor_off()
    IN1.close()
    IN2.close()
    print("\nStopped")
    sys.exit(0)


print("=== L293D 2-Pin Demo ===")
print(f"  > {TEMP_FORWARD} C   --> FORWARD  (warm sensor with fingers)")
print(f"  {TEMP_REVERSE} - {TEMP_FORWARD} C  --> OFF")
print(f"  < {TEMP_REVERSE} C   --> REVERSE  (blow on / cool the sensor)")
print("========================")

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

while True:
    handle_motor()
    sleep(2)
