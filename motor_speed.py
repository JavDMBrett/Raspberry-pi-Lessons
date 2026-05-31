from gpiozero import LED, PWMLED
from time import sleep

in1 = LED(17)
in2 = LED(27)
ena = PWMLED(22)

def forward(speed):
    print(f"Forward at speed {speed}")
    in1.on()
    in2.off()
    ena.value = speed

def reverse(speed):
    print(f"Reverse at speed {speed}")
    in1.off()
    in2.on()
    ena.value = speed

def stop():
    print("Stop")
    ena.off()
    in1.off()
    in2.off()

forward(0.4)
sleep(3)

forward(0.8)
sleep(3)

stop()
sleep(1)

reverse(0.6)
sleep(3)

stop()
