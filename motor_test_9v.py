from gpiozero import LED
from time import sleep

# L298N Motor A input pins
in1 = LED(17)
in2 = LED(27)

print("Motor forward")
in1.on()
in2.off()
sleep(3)

print("Motor stop")
in1.off()
in2.off()
sleep(2)

print("Motor reverse")
in1.off()
in2.on()
sleep(3)

print("Motor stop")
in1.off()
in2.off()
