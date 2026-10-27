# TEACHER ANSWER — do not distribute to students

from gpiozero import TrafficLights
from time import sleep
from signal import pause

lights = TrafficLights(red=9, amber=10, green=11)

def sequence():
    while True:
        yield (1, 0, 0);  sleep(2)    # Red
        yield (0, 0, 1);  sleep(2)    # Green
        yield (0, 1, 0);  sleep(0.5)  # Amber

lights.source = sequence()

try:
    pause()
except KeyboardInterrupt:
    lights.close()
