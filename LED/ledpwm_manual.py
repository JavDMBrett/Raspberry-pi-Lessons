from gpiozero import PWMLED
from signal import pause
from time import sleep

led = PWMLED(23)

def brightness():
    while True:
        yield 0      # off
        sleep(1)
        yield 0.5    # half brightness
        sleep(1)
        yield 1      # full brightness
        sleep(1)

led.source = brightness()

try:
    pause()
except KeyboardInterrupt:
    led.close()
