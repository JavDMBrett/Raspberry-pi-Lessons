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
#   temp > 28 C       --> FORWARD  (warm sensor with fingers)
#   temp 22 - 28 C    --> OFF      (room temperature)
#   temp < 22 C       --> REVERSE  (blow on sensor / cool it)
# ============================================================

from time import sleep
import RPi.GPIO as GPIO
from Adafruit_IO import Client, RequestError
from ada_secrets import ada_user, ada_key, ada_feed

# --- Pins ---
IN1 = 16
IN2 = 20

# --- Demo thresholds ---
TEMP_FORWARD = 30    # Above this -> FORWARD
TEMP_REVERSE = 25    # Below this -> REVERSE
# Between 25 and 27  -> OFF (motor off below 30, reverse below 25)

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
        print("Adafruit IO: Feed not found")
        return None


def motor_forward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)


def motor_reverse():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)


def motor_off():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)


def handle_motor():
    temp = read_temp()
    if temp is None:
        return

    if temp > TEMP_FORWARD:
        motor_forward()
        print(f"Temp: {temp:.1f} C  -->  Motor FORWARD   (warm the sensor to stay here)")
    elif temp < TEMP_REVERSE:
        motor_reverse()
        print(f"Temp: {temp:.1f} C  -->  Motor REVERSE   (cool the sensor to stay here)")
    else:
        motor_off()
        print(f"Temp: {temp:.1f} C  -->  Motor OFF       (room temp zone {TEMP_REVERSE}-{TEMP_FORWARD} C)")


print("=== L293D 2-Pin Demo ===")
print(f"  > {TEMP_FORWARD} C       --> FORWARD  (warm sensor with fingers)")
print(f"  {TEMP_REVERSE} - {TEMP_FORWARD} C   --> OFF      (middle zone)")
print(f"  < {TEMP_REVERSE} C       --> REVERSE  (room temp triggers this)")
print("========================")

try:
    while True:
        handle_motor()
        sleep(2)

except KeyboardInterrupt:
    motor_off()
    print("\nStopped")

GPIO.cleanup()
