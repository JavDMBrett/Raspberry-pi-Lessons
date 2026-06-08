# LF7 - Adafruit IO Cloud Demo (Two-Pi Live Demo)

Demonstrates an end-to-end IoT flow using the Adafruit IO cloud as the
link between two independent Raspberry Pis - they don't need to be on
the same network.

## Architecture
- **Pi 1 (sender)** - `Temp_DS18B20_Adafruit_Sender.py`
  Reads a DS18B20 temperature sensor and pushes the reading to an
  Adafruit IO feed every ~2 seconds (visible live on an Adafruit IO
  dashboard).
- **Pi 2 (receiver)** - `1P_Fan_LF7_AdaFruit_May23.py`
  Polls the same Adafruit IO feed and switches a fan motor on/off
  (via an L293N driver, single control pin) based on the temperature,
  using a hysteresis band to avoid rapid on/off cycling.

## Setup
Both scripts read their Adafruit IO credentials from a local
`ada_secrets.py` file (NOT committed to git - see `.gitignore`).

1. Copy `ada_secrets_template.py` to `ada_secrets.py`
2. Fill in your own values:
   ```python
   ada_user = 'your_adafruit_username'
   ada_key  = 'your_adafruit_io_key'
   ada_feed = 'your_feed_name'
   ```
3. Run the sender script on Pi 1, the receiver script on Pi 2.

## Notes
- Adafruit IO free accounts are rate-limited (~30 data points/minute),
  so the sender waits ~2 seconds between sends.
- `maxTMP` and `hysterese` in the receiver script control the
  on/off switching thresholds - adjust to suit your sensor placement.
