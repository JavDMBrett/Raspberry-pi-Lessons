import os
from time import sleep
import RPi.GPIO as GPIO

from Adafruit_IO import Client, RequestError        # Adafruit-Bibliothek exportieren
                                                     # vorher: pip3 install adafruit-io
from ada_secrets import ada_user, ada_key, ada_feed # Zugangsdaten aus ada_secrets.py (nicht in git!)


fanPin = 16 # The pin ID, edit here to change it

maxTMP = 30 # The maximum temperature in Celsius after which we trigger the fan
hysterese = 3  #Wert der Hysterese


# Setup the pins

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(fanPin, GPIO.OUT)

aio = Client(ada_user, ada_key)


def Shutdown():
    fanOFF()
    os.system("sudo shutdown -h now")
    sleep(100)


def read_temp():
#   Temepratur vom Server lesen
    try:
        temp = aio.receive(ada_feed)
        return temp.value
    except RequestError:
        print("Feed nicht vorhanden")
        return None


def fanON():
    setPin(True)


def fanOFF():
    setPin(False)


def handleFan():
    raw = read_temp()
    if raw is None:
        return
    temp = float(raw)
    print(temp)
    if temp > maxTMP:
        fanON()
        print("fan on")
    if temp < maxTMP - hysterese:
        fanOFF()
        print("fan off")

# A little redundant function but useful if you want to add logging

def setPin(mode):
    GPIO.output(fanPin, mode)

# Read the temperature every 5 sec, increase or decrease this limit if you want
try:

    while True:
        handleFan()
        sleep(5)

except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt
    fanOFF()

GPIO.cleanup() # resets all GPIO ports used by this program
