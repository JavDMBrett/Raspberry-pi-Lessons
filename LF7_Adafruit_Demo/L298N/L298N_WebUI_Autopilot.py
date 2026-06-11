#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from gpiozero import Motor
from threading import Lock, Thread, Event
from time import time, sleep
import atexit

# BCM-GPIO-Nummern passend zu deinem Breakout-Board:
PIN_IN1 = 17      # L298N IN1
PIN_IN2 = 27      # L298N IN2
PIN_ENA = 18      # L298N ENA, dafür ENA-Jumper am L298N entfernen
# Für Geschwindigkeit per Slider/Programm muss ENA an GPIO18 hängen.
# Wenn ENA-Jumper am L298N draufbleibt, hier False setzen.
USE_ENABLE_PIN = True
app = Flask(__name__)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

lock = Lock()
last_command_time = time()
current_direction = "stop"
current_speed = 0.0          # Anzeige-/Sollwert: 0.0 bis 1.0
last_motor_direction = "stop"
START_BOOST_SPEED = 1.0      # kurzer Anlaufimpuls, damit der Motor sicher losdreht
START_BOOST_SECONDS = 0.18
program_thread = None
program_cancel = Event()
if USE_ENABLE_PIN:
    motor = Motor(forward=PIN_IN1, backward=PIN_IN2, enable=PIN_ENA)
else:
    motor = Motor(forward=PIN_IN1, backward=PIN_IN2)

HTML = """
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Motorsteuerung</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: "Segoe UI", Arial, sans-serif;
            color: #f7fbff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            overflow: hidden;
            background:
                radial-gradient(circle at 15% 20%, rgba(70, 170, 255, 0.75), transparent 26%),
                radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.55), transparent 18%),
                radial-gradient(circle at 70% 85%, rgba(0, 210, 255, 0.45), transparent 28%),
                linear-gradient(135deg, #031a3f 0%, #0c65b8 45%, #71c8ff 100%);
            background-size: 180% 180%;
            animation: aeroBackground 12s ease-in-out infinite alternate;
        }
        body::before {
            content: "";
            position: fixed;
            inset: -20%;
            background:
                linear-gradient(115deg, transparent 0 42%, rgba(255,255,255,0.16) 48%, transparent 54% 100%),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.045) 0 1px, transparent 1px 70px);
            animation: lightSweep 7s linear infinite;
            pointer-events: none;
        }
        body::after {
            content: "";
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at center, transparent 0 48%, rgba(0,0,0,0.28) 100%);
            pointer-events: none;
        }
        @keyframes aeroBackground {
            from { background-position: 0% 20%; }
            to { background-position: 100% 80%; }
        }
        @keyframes lightSweep {
            from { transform: translateX(-18%) rotate(0deg); }
            to { transform: translateX(18%) rotate(0deg); }
        }
        .panel {
            position: relative;
            z-index: 1;
            width: 390px;
            padding: 24px;
            text-align: center;
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.65);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.38), rgba(255,255,255,0.11)),
                linear-gradient(135deg, rgba(5,32,70,0.78), rgba(4,95,165,0.55));
            box-shadow:
                0 24px 60px rgba(0,0,0,0.45),
                inset 0 1px 0 rgba(255,255,255,0.9),
                inset 0 -18px 40px rgba(0,0,0,0.17);
            backdrop-filter: blur(16px) saturate(145%);
        }
        .panel::before {
            content: "";
            position: absolute;
            inset: 8px 8px auto 8px;
            height: 52px;
            border-radius: 17px 17px 50% 50%;
            background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.06));
            pointer-events: none;
        }
        h1 {
            position: relative;
            font-size: 25px;
            margin-top: 0;
            margin-bottom: 18px;
            text-shadow: 0 1px 2px #00335f, 0 0 12px rgba(120,210,255,0.9);
        }
        .version {
            margin: -8px 0 12px;
            font-size: 12px;
            letter-spacing: 0.4px;
            color: rgba(255,255,255,0.88);
            text-shadow: 0 0 8px rgba(120,220,255,0.95);
        }
        .status {
            margin: 14px 0 18px;
            padding: 12px;
            background: linear-gradient(180deg, rgba(0,0,0,0.35), rgba(255,255,255,0.10));
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 12px;
            font-weight: bold;
            box-shadow: inset 0 1px 8px rgba(0,0,0,0.32), 0 0 18px rgba(0,170,255,0.22);
            text-shadow: 0 0 8px rgba(255,255,255,0.55);
        }
        button {
            position: relative;
            overflow: hidden;
            isolation: isolate;
            border: 1px solid rgba(255,255,255,0.78);
            border-radius: 13px;
            padding: 16px;
            margin: 8px;
            font-size: 18px;
            cursor: pointer;
            min-width: 135px;
            color: white;
            font-weight: 700;
            text-shadow: 0 -1px 1px rgba(0,0,0,0.72), 0 0 8px var(--button-glow-soft);
            background: var(--button-bg);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.95),
                inset 0 18px 18px rgba(255,255,255,0.26),
                inset 0 -17px 28px rgba(0,0,0,0.28),
                0 5px 14px rgba(0,0,0,0.28),
                0 0 16px var(--button-glow-soft);
            transition: transform 120ms ease, box-shadow 180ms ease, filter 180ms ease;
        }
        button::before {
            content: "";
            position: absolute;
            z-index: -1;
            inset: 2px 2px auto 2px;
            height: 48%;
            border-radius: 11px 11px 55% 55%;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.78), rgba(255,255,255,0.18) 52%, transparent 100%);
            opacity: 0.9;
            pointer-events: none;
        }
        button::after {
            content: "";
            position: absolute;
            z-index: 1;
            top: -35%;
            left: -85%;
            width: 55%;
            height: 170%;
            background: linear-gradient(105deg, transparent 0%, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.78) 48%, rgba(255,255,255,0.10) 68%, transparent 100%);
            transform: skewX(-22deg);
            opacity: 0.0;
            pointer-events: none;
        }
        button:hover {
            transform: translateY(-2px) scale(1.025);
            filter: brightness(1.17) saturate(1.35);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,1),
                inset 0 18px 20px rgba(255,255,255,0.34),
                inset 0 -15px 28px rgba(0,0,0,0.18),
                0 0 10px rgba(255,255,255,0.75),
                0 0 24px var(--button-glow),
                0 0 48px var(--button-glow-soft),
                0 8px 20px rgba(0,0,0,0.35);
        }
        button:hover::after {
            opacity: 1;
            animation: buttonShimmer 0.95s ease-out;
        }
        button:active {
            transform: translateY(1px) scale(0.99);
            filter: brightness(0.98) saturate(1.1);
        }
        @keyframes buttonShimmer {
            from { left: -85%; }
            to { left: 135%; }
        }
        .forward {
            --button-bg: linear-gradient(180deg, #9cffad, #1bbf52 50%, #076629);
            --button-glow: rgba(0,255,95,0.95);
            --button-glow-soft: rgba(0,255,120,0.42);
        }
        .backward {
            --button-bg: linear-gradient(180deg, #93c9ff, #286fff 50%, #073ca6);
            --button-glow: rgba(0,145,255,0.95);
            --button-glow-soft: rgba(0,165,255,0.42);
        }
        .stop {
            --button-bg: linear-gradient(180deg, #ffaaa3, #ef2525 50%, #820707);
            --button-glow: rgba(255,35,35,0.98);
            --button-glow-soft: rgba(255,45,45,0.45);
            width: 285px;
            font-size: 22px;
        }
        .program {
            --button-bg: linear-gradient(180deg, #fff09b, #ffb900 50%, #c96b00);
            --button-glow: rgba(255,210,0,0.98);
            --button-glow-soft: rgba(255,210,0,0.48);
            color: #241400;
            text-shadow: 0 1px 1px rgba(255,255,255,0.78), 0 0 12px rgba(255,238,120,0.7);
            width: 285px;
        }
        .program.running {
            --button-bg: linear-gradient(180deg, #fff4a8, #ff7a00 50%, #b43100);
            --button-glow: rgba(255,115,0,1);
            --button-glow-soft: rgba(255,170,0,0.6);
            animation: autopilotPulse 1.1s ease-in-out infinite alternate;
        }
        .program.running::after {
            opacity: 0.95;
            animation: buttonShimmer 1.45s ease-in-out infinite;
        }
        @keyframes autopilotPulse {
            from {
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,0.95),
                    inset 0 18px 18px rgba(255,255,255,0.28),
                    inset 0 -17px 28px rgba(0,0,0,0.26),
                    0 0 18px rgba(255,190,0,0.72),
                    0 5px 14px rgba(0,0,0,0.28);
            }
            to {
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,1),
                    inset 0 18px 22px rgba(255,255,255,0.38),
                    inset 0 -15px 28px rgba(0,0,0,0.18),
                    0 0 30px rgba(255,230,80,1),
                    0 0 58px rgba(255,100,0,0.82),
                    0 8px 20px rgba(0,0,0,0.35);
            }
        }
        label {
            font-weight: 700;
            text-shadow: 0 1px 2px rgba(0,0,0,0.6);
        }
        input[type="range"] {
            width: 285px;
            accent-color: #53c9ff;
            filter: drop-shadow(0 0 10px rgba(100,220,255,0.65));
            cursor: pointer;
        }
        .small {
            font-size: 13px;
            color: rgba(245,250,255,0.86);
            margin-top: 14px;
            line-height: 1.4;
            text-shadow: 0 1px 2px rgba(0,0,0,0.75);
        }
</style>
</head>
<body>
<div class="panel">
<h1>✨ L298N Motorsteuerung ✨</h1>
<div class="version">Windows 7 Aero Autopilot v3</div>
<div class="status" id="status">Status: STOP</div>
<label for="speed">Geschwindigkeit: <span id="speedValue">50</span>%</label>
<br>
<input id="speed" type="range" min="0" max="100" value="50">
<div>
<button class="forward" onclick="sendCommand('forward')">Vorwärts</button>
</div>
<div>
<button class="stop" onclick="sendCommand('stop')">STOP</button>
</div>
<div>
<button class="backward" onclick="sendCommand('backward')">Rückwärts</button>
</div>
<div>
<button class="program" id="programButton" onclick="toggleAutopilot()">Autopilot starten</button>
</div>
<div class="small">
            Autopilot: langsam vorwärts beschleunigen → stoppen → langsam rückwärts beschleunigen → stoppen → wiederholen<br>
            Slider: 1 % Anzeige entspricht 10 % Motorleistung, damit der Motor nicht direkt beleidigt stehen bleibt.<br>
            Tastatur: ↑ vorwärts · ↓ rückwärts · Leertaste/Esc STOP
</div>
</div>
<script>
    const speedSlider = document.getElementById("speed");
    const speedValue = document.getElementById("speedValue");
    const statusBox = document.getElementById("status");
    const programButton = document.getElementById("programButton");
    let currentDirection = "stop";
    let autopilotRunning = false;
    function getSpeed() {
        return Number(speedSlider.value) / 100;
    }
    function updateAutopilotButton() {
        programButton.textContent = autopilotRunning ? "Autopilot stoppen" : "Autopilot starten";
        programButton.classList.toggle("running", autopilotRunning);
    }
    async function sendCommand(direction) {
        currentDirection = direction;
        const response = await fetch("/api/motor", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                direction: direction,
                speed: getSpeed()
            })
        });
        const data = await response.json();
        autopilotRunning = data.autopilot_running;
        updateAutopilotButton();
        statusBox.textContent = "Status: " + data.status;
    }
    async function toggleAutopilot() {
        const response = await fetch("/api/program", {
            method: "POST"
        });
        const data = await response.json();
        autopilotRunning = data.autopilot_running;
        currentDirection = autopilotRunning ? "program" : "stop";
        updateAutopilotButton();
        statusBox.textContent = "Status: " + data.status;
    }
    async function refreshStatus() {
        try {
            const response = await fetch("/api/status");
            const data = await response.json();
            autopilotRunning = data.autopilot_running;
            updateAutopilotButton();
            statusBox.textContent = "Status: " + data.status;
        } catch (e) {
            statusBox.textContent = "Status: Verbindung verloren";
        }
    }
    speedSlider.addEventListener("input", () => {
        speedValue.textContent = speedSlider.value;
        if (currentDirection === "forward" || currentDirection === "backward") {
            sendCommand(currentDirection);
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowUp") {
            sendCommand("forward");
        } else if (event.key === "ArrowDown") {
            sendCommand("backward");
        } else if (event.key === " " || event.key === "Escape") {
            event.preventDefault();
            sendCommand("stop");
        }
    });
    // Heartbeat: Solange die Seite offen ist, bekommt der Pi regelmäßig ein Signal.
    setInterval(() => {
        fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
    }, 500);
    // Status regelmäßig aktualisieren, damit man den Autopilot live sieht.
    setInterval(refreshStatus, 300);
    // Beim Schließen der Seite stoppen.
    window.addEventListener("beforeunload", () => {
        navigator.sendBeacon("/api/stop");
    });
</script>
</body>
</html>
"""
def display_to_motor_speed(display_speed: float) -> float:
    """Mappt den angezeigten Sliderwert auf die echte Motorleistung.
    0% bleibt aus, 1% Anzeige entspricht 10% Motorleistung, 100% bleibt 100%.
    """
    display_speed = max(0.0, min(1.0, float(display_speed)))
    if display_speed <= 0:
        return 0.0
    return 0.10 + (((display_speed * 100) - 1) / 99 * 0.90)


def apply_motor_output(direction: str, display_speed: float, ui_direction: str | None = None):
    global current_direction, current_speed, last_command_time, last_motor_direction
    display_speed = max(0.0, min(1.0, float(display_speed)))
    motor_speed = display_to_motor_speed(display_speed)
    previous_motor_direction = last_motor_direction

    with lock:
        last_command_time = time()
        current_direction = ui_direction or direction
        current_speed = display_speed

        if direction == "forward" and motor_speed > 0:
            if previous_motor_direction != "forward" and display_speed < 0.40:
                motor.forward(START_BOOST_SPEED)
                sleep(START_BOOST_SECONDS)
            motor.forward(motor_speed)
            last_motor_direction = "forward"
            return f"VORWÄRTS: Anzeige {int(display_speed * 100)} % → Motor {int(motor_speed * 100)} %"

        if direction == "backward" and motor_speed > 0:
            if previous_motor_direction != "backward" and display_speed < 0.40:
                motor.backward(START_BOOST_SPEED)
                sleep(START_BOOST_SECONDS)
            motor.backward(motor_speed)
            last_motor_direction = "backward"
            return f"RÜCKWÄRTS: Anzeige {int(display_speed * 100)} % → Motor {int(motor_speed * 100)} %"

        motor.stop()
        current_direction = "stop"
        current_speed = 0.0
        last_motor_direction = "stop"
        return "STOP"


def motor_status_text():
    with lock:
        motor_speed = display_to_motor_speed(current_speed)
        if current_direction == "forward":
            return f"VORWÄRTS: Anzeige {int(current_speed * 100)} % → Motor {int(motor_speed * 100)} %"
        if current_direction == "backward":
            return f"RÜCKWÄRTS: Anzeige {int(current_speed * 100)} % → Motor {int(motor_speed * 100)} %"
        if current_direction == "program":
            return f"AUTOPILOT läuft: Anzeige {int(current_speed * 100)} % → Motor {int(motor_speed * 100)} %"
        return "STOP"


def set_motor(direction: str, speed: float):
    return apply_motor_output(direction, speed)


def set_program_motor(direction: str, speed: float):
    apply_motor_output(direction, speed, ui_direction="program" if direction != "stop" else "stop")

def cancel_running_program():
    global program_thread
    program_cancel.set()
    if program_thread is not None and program_thread.is_alive():
        program_thread.join(timeout=1.0)
    program_cancel.clear()

def wait_cancelable(seconds: float):
    end_time = time() + seconds
    while time() < end_time:
        if program_cancel.is_set():
            return False
        sleep(0.05)
    return True

def is_autopilot_running():
    return program_thread is not None and program_thread.is_alive() and not program_cancel.is_set()


def run_preprogrammed_sequence():
    try:
        while not program_cancel.is_set():
            # Vorwärts langsam beschleunigen: Anzeige 1% bis 100%
            for percent in range(1, 101, 10):
                if program_cancel.is_set():
                    break
                set_program_motor("forward", percent / 100)
                if not wait_cancelable(0.4):
                    break
            # Kurz stoppen
            if not program_cancel.is_set():
                set_program_motor("stop", 0)
                if not wait_cancelable(1.0):
                    break
            # Rückwärts langsam beschleunigen: Anzeige 1% bis 100%
            for percent in range(1, 101, 10):
                if program_cancel.is_set():
                    break
                set_program_motor("backward", percent / 100)
                if not wait_cancelable(0.4):
                    break
            # Kurz stoppen, bevor der Autopilot wieder von vorne beginnt.
            if not program_cancel.is_set():
                set_program_motor("stop", 0)
                wait_cancelable(1.0)
    finally:
        set_motor("stop", 0)

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/motor", methods=["POST"])
def api_motor():
    cancel_running_program()
    data = request.get_json(force=True)
    direction = data.get("direction", "stop")
    speed = data.get("speed", 0)
    if direction not in ["forward", "backward", "stop"]:
        return jsonify({"error": "Ungültige Richtung"}), 400
    status = set_motor(direction, speed)
    return jsonify({"status": status, "autopilot_running": is_autopilot_running()})

@app.route("/api/program", methods=["POST"])
def api_program():
    global program_thread
    if is_autopilot_running():
        cancel_running_program()
        status = set_motor("stop", 0)
        return jsonify({"status": status, "autopilot_running": False})
    cancel_running_program()
    program_thread = Thread(target=run_preprogrammed_sequence, daemon=True)
    program_thread.start()
    return jsonify({"status": "AUTOPILOT gestartet", "autopilot_running": True})

@app.route("/api/status")
def api_status():
    return jsonify({"status": motor_status_text(), "autopilot_running": is_autopilot_running()})

@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    global last_command_time
    with lock:
        last_command_time = time()
    return jsonify({"ok": True})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    cancel_running_program()
    status = set_motor("stop", 0)
    return jsonify({"status": status, "autopilot_running": False})

def watchdog():
    while True:
        sleep(0.2)
        with lock:
            timeout_reached = time() - last_command_time > 2.0
            motor_running = current_direction != "stop"
        if timeout_reached and motor_running:
            cancel_running_program()
            set_motor("stop", 0)

def cleanup():
    cancel_running_program()
    motor.stop()
    motor.close()

atexit.register(cleanup)
Thread(target=watchdog, daemon=True).start()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
 