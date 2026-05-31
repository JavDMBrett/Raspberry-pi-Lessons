from gpiozero import LED
from signal import pause

led = LED(23)    # BCM pin 23

led.on()

pause()          # keeps the script running — without this it exits immediately
