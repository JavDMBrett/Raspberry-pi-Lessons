from gpiozero import LED
from signal import pause

led = LED(23)    # BCM pin 23

led.on()

try:
    pause()
except KeyboardInterrupt:
    led.close()
