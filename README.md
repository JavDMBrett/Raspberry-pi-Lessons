# Raspberry Pi Lessons

Python scripts for Raspberry Pi 4B+ lessons (LF 7), organized by topic.
Each folder is a self-contained lesson/demo.

## Structure

| Folder | Topic |
|---|---|
| [`LED/`](LED/) | LED basics, blinking, PWM, traffic-light simulations |
| [`RGB/`](RGB/) | RGB LEDs, colour mixing, CPU/temperature-driven RGB demos, barrier gate |
| [`Temp/`](Temp/) | DS18B20 temperature sensor reading (local + Adafruit IO) |
| [`DC_Motor/`](DC_Motor/) | DC motor control and speed control |
| [`Button/`](Button/) | Push-button input handling *(in progress)* |
| [`LF7_Adafruit_Demo/`](LF7_Adafruit_Demo/) | Two-Pi live demo: cloud-linked temperature sensing + automatic fan control via Adafruit IO + MQTT/REST concepts |

## Notes
- Scripts that talk to Adafruit IO read credentials from a local
  `ada_secrets.py` (gitignored) - copy the provided
  `ada_secrets_template.py`, fill in your own values, and never commit
  the real one.
- Built and tested on Raspberry Pi 4B+ running Raspberry Pi OS.
