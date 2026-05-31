# TEACHER ANSWER — do not distribute to students

from gpiozero import TrafficLights
from time import sleep
from signal import pause

lights = TrafficLights(red=2, amber=3, green=17)

def sequence():

    yield (1, 0, 0);  sleep(2)    # Red
    yield (1, 1, 0);  sleep(0.5)  # Red + Amber
    yield (0, 0, 1);  sleep(2)    # Green
    yield (0, 1, 0);  sleep(0.5)  # Amber

lights.source = sequence()

pause()
