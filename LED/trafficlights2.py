from gpiozero import TrafficLights
from time import sleep
from signal import pause

lights = TrafficLights(red=2, amber=3, green=17)

def sequence():
    while True:
        yield (1, 0, 0);  sleep(2)    # Red
        yield (0, 1, 0);  sleep(2)    # Amber
        yield (0, 0, 1);  sleep(2)    # Green

lights.source = sequence()

try:
    pause()
except KeyboardInterrupt:
    lights.close()
