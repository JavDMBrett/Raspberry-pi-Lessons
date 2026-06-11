#!/usr/bin/env python3
# ============================================================
# L298N — Flask Web Demo (ENA PWM + IN1 + IN2)
# ============================================================
# Wiring:
#   Pi GPIO 17  --> L298N IN1  (direction)
#   Pi GPIO 27  --> L298N IN2  (direction)
#   Pi GPIO 18  --> L298N ENA  (PWM speed control)
#   L298N OUT1 + OUT2 --> Motor
#   L298N VCC  --> 9V Battery +
#   L298N GND  --> GND (shared with Pi and Battery -)
#   Remove ENA jumper on L298N module for PWM control
#
# Usage:
#   pip install flask
#   python L298N_WebDemo.py
#
# Access from a classroom PC via SSH tunnel:
#   ssh -L 5000:localhost:5000 pi@<raspberry-pi-ip>
#   Then open http://localhost:5000 in the browser.
#
# Safety features:
#   - Server listens on localhost only (not exposed on the network)
#   - Watchdog thread stops the motor if no command arrives for 2 s
#   - Browser heartbeat (every 500 ms) keeps the motor running
#   - Motor stops automatically when the browser tab is closed
# ============================================================

from flask import Flask, request, jsonify, render_template_string
from gpiozero import Motor
from threading import Lock, Thread
from time import time, sleep
import atexit

# --- Pins ---
PIN_IN1 = 17      # L298N IN1
PIN_IN2 = 27      # L298N IN2
PIN_ENA = 18      # L298N ENA  --  remove the ENA jumper on the L298N
USE_ENABLE_PIN = True

# --- App setup ---
app = Flask(__name__)
lock = Lock()
last_command_time = time()
current_direction = "stop"
current_speed = 0.5

if USE_ENABLE_PIN:
    motor = Motor(forward=PIN_IN1, backward=PIN_IN2, enable=PIN_ENA)
else:
    motor = Motor(forward=PIN_IN1, backward=PIN_IN2)

# --- HTML page (served to the browser) ---
HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>L298N Motor Control</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body {
        font-family: Arial, sans-serif;
        background: #111;
        color: #eee;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        margin: 0;
    }
    .panel {
        background: #1e1e1e;
        border-radius: 18px;
        padding: 24px;
        width: 340px;
        box-shadow: 0 0 25px rgba(0,0,0,0.5);
        text-align: center;
    }
    h1 { font-size: 22px; margin-top: 0; }
    .status {
        margin: 14px 0;
        padding: 10px;
        background: #2b2b2b;
        border-radius: 10px;
        font-weight: bold;
    }
    button {
        border: none;
        border-radius: 12px;
        padding: 16px;
        margin: 8px;
        font-size: 18px;
        cursor: pointer;
        min-width: 120px;
    }
    .forward  { background: #2e8b57; color: white; }
    .backward { background: #4169e1; color: white; }
    .stop     { background: #c0392b; color: white; width: 260px;
                font-size: 22px; font-weight: bold; }
    input[type="range"] { width: 280px; }
    .small { font-size: 13px; color: #aaa; margin-top: 14px; line-height: 1.4; }
</style>
</head>
<body>
<div class="panel">
    <h1>L298N Motor Control</h1>
    <div class="status" id="status">Status: STOP</div>
    <label for="speed">Speed: <span id="speedValue">50</span>%</label><br>
    <input id="speed" type="range" min="0" max="100" value="50">
    <div><button class="forward"  onclick="sendCmd('forward')">Forward</button></div>
    <div><button class="stop"     onclick="sendCmd('stop')">STOP</button></div>
    <div><button class="backward" onclick="sendCmd('backward')">Backward</button></div>
    <div class="small">
        Keys: &uarr; Forward &nbsp; &darr; Backward &nbsp; Space/Esc = STOP<br>
        Safety: motor stops automatically if the connection is lost.
    </div>
</div>
<script>
    const slider = document.getElementById('speed');
    const speedLabel = document.getElementById('speedValue');
    const statusBox = document.getElementById('status');
    let lastDir = 'stop';

    function getSpeed() { return Number(slider.value) / 100; }

    async function sendCmd(direction) {
        lastDir = direction;
        const res = await fetch('/api/motor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction, speed: getSpeed() })
        });
        const data = await res.json();
        statusBox.textContent = 'Status: ' + data.status;
    }

    slider.addEventListener('input', () => {
        speedLabel.textContent = slider.value;
        if (lastDir !== 'stop') sendCmd(lastDir);
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'ArrowUp')                     sendCmd('forward');
        else if (e.key === 'ArrowDown')               sendCmd('backward');
        else if (e.key === ' ' || e.key === 'Escape') { e.preventDefault(); sendCmd('stop'); }
    });

    // Heartbeat: tells the Pi the browser is still open.
    setInterval(() => fetch('/api/heartbeat', { method: 'POST' }).catch(() => {}), 500);

    // Stop motor when tab is closed.
    window.addEventListener('beforeunload', () => navigator.sendBeacon('/api/stop'));
</script>
</body>
</html>
"""


# --- Motor control ---
def apply_motor(direction: str, speed: float) -> str:
    global current_direction, current_speed, last_command_time
    speed = max(0.0, min(1.0, float(speed)))
    with lock:
        last_command_time = time()
        current_direction = direction
        current_speed = speed
        if direction == "forward" and speed > 0:
            motor.forward(speed)
            return f"FORWARD at {int(speed * 100)} %"
        if direction == "backward" and speed > 0:
            motor.backward(speed)
            return f"BACKWARD at {int(speed * 100)} %"
        motor.stop()
        current_direction = "stop"
        current_speed = 0
        return "STOP"


# --- Routes ---
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/motor", methods=["POST"])
def api_motor():
    data = request.get_json(force=True)
    direction = data.get("direction", "stop")
    speed = data.get("speed", 0)
    if direction not in ("forward", "backward", "stop"):
        return jsonify({"error": "Invalid direction"}), 400
    return jsonify({"status": apply_motor(direction, speed)})


@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    global last_command_time
    with lock:
        last_command_time = time()
    return jsonify({"ok": True})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    return jsonify({"status": apply_motor("stop", 0)})


# --- Watchdog thread ---
# Stops the motor if no command arrives for 2 seconds (e.g. network drop).
def watchdog():
    while True:
        sleep(0.2)
        with lock:
            timed_out = time() - last_command_time > 2.0
            running = current_direction != "stop"
        if timed_out and running:
            apply_motor("stop", 0)


# --- Cleanup ---
def cleanup():
    motor.stop()
    motor.close()


atexit.register(cleanup)
Thread(target=watchdog, daemon=True).start()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
