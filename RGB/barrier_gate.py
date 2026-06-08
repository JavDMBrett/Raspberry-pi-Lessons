from gpiozero import LED, Button, PWMLED
from time import sleep

# L298N Motor A
in1 = LED(17)
in2 = LED(27)
ena = PWMLED(22)

# Input and status LEDs
button = Button(5)
red = LED(23)
green = LED(24)

def motor_forward(speed=0.7):
    print("Opening barrier")
    in1.on()
    in2.off()
    ena.value = speed

def motor_reverse(speed=0.7):
    print("Closing barrier")
    in1.off()
    in2.on()
    ena.value = speed

def motor_stop():
    print("Motor stopped")
    ena.off()
    in1.off()
    in2.off()

def open_barrier():
    motor_forward(0.7)
    sleep(2)
    motor_stop()

def close_barrier():
    motor_reverse(0.7)
    sleep(2)
    motor_stop()

while True:
    red.on()
    green.off()
    print("Barrier closed. Waiting for button.")

    button.wait_for_press()

    red.off()
    open_barrier()

    green.on()
    print("Barrier open")
    sleep(3)

    green.off()
    close_barrier()

    red.on()
