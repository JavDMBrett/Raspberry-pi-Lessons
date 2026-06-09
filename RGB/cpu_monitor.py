from gpiozero import RGBLED
from signal import pause
import psutil

RGB = RGBLED(red=9, green=10, blue=11)

def cpu_colour():
    while True:
        cpu       = psutil.cpu_percent(interval=0.5)
        red_val   = cpu / 100.0
        green_val = (100 - cpu) / 100.0
        print(f"CPU: {cpu:.1f}%")
        yield (red_val, green_val, 0)

RGB.source = cpu_colour()

try:
    pause()
except KeyboardInterrupt:
    RGB.close()
