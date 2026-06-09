from gpiozero import RGBLED
from time import sleep
from signal import pause

RGB = RGBLED(red=9, green=10, blue=11)

def colours():
    while True:
        yield (1, 0, 0);       sleep(2)    # Red
        yield (0, 1, 0);       sleep(2)    # Green
        yield (0, 0, 1);       sleep(2)    # Blue
        yield (1.0, 0.549, 0); sleep(3)    # Orange  (255, 140, 0) ÷ 255

RGB.source = colours()

try:
    pause()
except KeyboardInterrupt:
    RGB.close()
