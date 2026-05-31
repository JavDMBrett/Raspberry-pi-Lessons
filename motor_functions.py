from gpiozero import LED
from time import sleep

in1 = LED(17)
in2 = LED(27)

def forward():
    print("Forward")
    in1.on()
    in2.off()

def reverse():
    print("Reverse")
    in1.off()
    in2.on()

def stop():
    print("Stop")
    in1.off()
    in2.off()

forward()
sleep(2)

stop()
sleep(1)

reverse()
sleep(2)

stop()
