from gpiozero import RGBLED
from time import sleep

RGB = RGBLED(red=9, green=10, blue=11)

try:
    while True:
        RGB.color = (1, 0, 0)  # Red
        sleep(3)
        RGB.color = (0, 1, 0)  # Green
        sleep(3)
        RGB.color = (0, 0, 1)  # Blue
        sleep(3)
except KeyboardInterrupt:
    RGB.close()
