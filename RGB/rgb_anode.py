# TEACHER ANSWER — do not distribute to students

from gpiozero import RGBLED
from time import sleep
from signal import pause

RGB = RGBLED(red=9, green=10, blue=11)

def colours():

    yield (0, 1, 1);  sleep(2)    # Red   (inverted logic — common anode)
    yield (1, 0, 1);  sleep(2)    # Green (inverted logic — common anode)
    yield (1, 1, 0);  sleep(2)    # Blue  (inverted logic — common anode)

RGB.source = colours()

pause()
