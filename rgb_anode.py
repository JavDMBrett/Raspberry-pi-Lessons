# TEACHER ANSWER — do not distribute to students

from gpiozero import RGBLED
from time import sleep
from signal import pause

RGB = RGBLED(red=9, green=10, blue=11)

def colours():
    while True:
        yield (0, 1, 1);  sleep(2)    # Red   (inverted)
        yield (1, 0, 1);  sleep(2)    # Green (inverted)
        yield (1, 1, 0);  sleep(2)    # Blue  (inverted)

RGB.source = colours()

try:
    pause()
except KeyboardInterrupt:
    RGB.close()
