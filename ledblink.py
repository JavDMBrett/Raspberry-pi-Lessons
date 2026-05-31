from gpiozero import LED
from signal import pause

led = LED(23)

led.blink()              # 1 second on, 1 second off (default)

# led.blink(0.2, 0.2)   # faster: 0.2s on, 0.2s off

pause()
