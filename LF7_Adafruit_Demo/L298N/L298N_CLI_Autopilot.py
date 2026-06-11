#!/usr/bin/env python3
from gpiozero import Motor
from threading import Lock, Thread, Event
from time import sleep
import atexit

# BCM-GPIO-Nummern passend zu deinem Breakout-Board:
PIN_IN1 = 17      # L298N IN1
PIN_IN2 = 27      # L298N IN2
PIN_ENA = 18      # L298N ENA, dafür ENA-Jumper am L298N entfernen
USE_ENABLE_PIN = True

# Motor startet bei niedriger PWM oft nicht sauber.
START_BOOST_SPEED = 1.0
START_BOOST_SECONDS = 0.18

lock = Lock()
program_thread = None
program_cancel = Event()
current_direction = "stop"
current_speed = 0.0        # Anzeige 0.0 bis 1.0
last_motor_direction = "stop"

if USE_ENABLE_PIN:
    motor = Motor(forward=PIN_IN1, backward=PIN_IN2, enable=PIN_ENA)
else:
    motor = Motor(forward=PIN_IN1, backward=PIN_IN2)


def display_to_motor_speed(display_speed: float) -> float:
    """Mappt 1-100% Anzeige auf 10-100% Motorleistung."""
    display_speed = max(0.0, min(1.0, float(display_speed)))
    if display_speed <= 0:
        return 0.0
    return 0.10 + (display_speed * 0.90)


def apply_motor(direction: str, display_speed: float, use_boost: bool = True):
    global current_direction, current_speed, last_motor_direction

    display_speed = max(0.0, min(1.0, float(display_speed)))
    motor_speed = display_to_motor_speed(display_speed)

    with lock:
        was_stopped_or_changed = (
            last_motor_direction == "stop" or
            last_motor_direction != direction
        )
        current_direction = direction
        current_speed = display_speed

    if direction == "forward" and motor_speed > 0:
        if use_boost and was_stopped_or_changed and motor_speed < 0.40:
            motor.forward(START_BOOST_SPEED)
            sleep(START_BOOST_SECONDS)
        motor.forward(motor_speed)
        last_motor_direction = "forward"
        return

    if direction == "backward" and motor_speed > 0:
        if use_boost and was_stopped_or_changed and motor_speed < 0.40:
            motor.backward(START_BOOST_SPEED)
            sleep(START_BOOST_SECONDS)
        motor.backward(motor_speed)
        last_motor_direction = "backward"
        return

    motor.stop()
    with lock:
        current_direction = "stop"
        current_speed = 0.0
    last_motor_direction = "stop"


def stop_motor():
    apply_motor("stop", 0, use_boost=False)
    print("Status: STOP")


def status_text() -> str:
    with lock:
        if current_direction == "forward":
            return f"VORWÄRTS {int(current_speed * 100)}%"
        if current_direction == "backward":
            return f"RÜCKWÄRTS {int(current_speed * 100)}%"
        if current_direction == "program":
            return f"AUTOPILOT {int(current_speed * 100)}%"
        return "STOP"


def wait_cancelable(seconds: float) -> bool:
    steps = max(1, int(seconds / 0.05))
    for _ in range(steps):
        if program_cancel.is_set():
            return False
        sleep(0.05)
    return not program_cancel.is_set()


def set_autopilot_motor(direction: str, percent: int):
    global current_direction, current_speed
    with lock:
        current_direction = "program"
        current_speed = percent / 100
    apply_motor(direction, percent / 100)
    print(f"Autopilot: {direction} {percent}%")


def autopilot_loop():
    try:
        while not program_cancel.is_set():
            for percent in range(10, 101, 10):
                if program_cancel.is_set():
                    return
                set_autopilot_motor("forward", percent)
                if not wait_cancelable(0.4):
                    return

            apply_motor("stop", 0, use_boost=False)
            print("Autopilot: Pause")
            if not wait_cancelable(1.0):
                return

            for percent in range(10, 101, 10):
                if program_cancel.is_set():
                    return
                set_autopilot_motor("backward", percent)
                if not wait_cancelable(0.4):
                    return

            apply_motor("stop", 0, use_boost=False)
            print("Autopilot: Pause")
            if not wait_cancelable(1.0):
                return
    finally:
        stop_motor()


def start_autopilot():
    global program_thread
    stop_autopilot(silent=True)
    program_cancel.clear()
    program_thread = Thread(target=autopilot_loop, daemon=True)
    program_thread.start()
    print("Autopilot gestartet. Mit 'x' oder 'stop' abbrechen.")


def stop_autopilot(silent: bool = False):
    global program_thread
    program_cancel.set()
    if program_thread is not None and program_thread.is_alive():
        program_thread.join(timeout=1.0)
    program_cancel.clear()
    program_thread = None
    stop_motor()
    if not silent:
        print("Autopilot gestoppt.")


def cleanup():
    program_cancel.set()
    motor.stop()
    motor.close()


def print_help():
    print("""
Minimal-Terminalsteuerung

Befehle:
  f [1-100]     vorwärts, z.B. f 30
  b [1-100]     rückwärts, z.B. b 30
  s / stop      Motor stoppen
  a / auto      Autopilot starten/stoppen
  x             Autopilot stoppen
  status        Status anzeigen
  h / help      Hilfe anzeigen
  q / quit      beenden

Hinweis:
  1% Anzeige entspricht intern 10% Motorleistung.
  Beim Anlaufen unter 40% gibt es kurz 100% Boost.
""".strip())


def parse_speed(parts) -> float:
    if len(parts) < 2:
        return 0.50
    try:
        value = int(parts[1])
    except ValueError:
        print("Ungültige Geschwindigkeit, nutze 50%.")
        return 0.50
    value = max(1, min(100, value))
    return value / 100


def main():
    print_help()
    while True:
        try:
            command = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBeende...")
            break

        if not command:
            continue

        parts = command.split()
        cmd = parts[0]

        if cmd in ["q", "quit", "exit"]:
            break

        if cmd in ["h", "help", "?"]:
            print_help()
            continue

        if cmd == "status":
            print("Status:", status_text())
            continue

        if cmd in ["s", "stop"]:
            stop_autopilot(silent=True)
            continue

        if cmd in ["x"]:
            stop_autopilot()
            continue

        if cmd in ["a", "auto", "autopilot"]:
            if program_thread is not None and program_thread.is_alive():
                stop_autopilot()
            else:
                start_autopilot()
            continue

        speed = parse_speed(parts)

        if cmd in ["f", "forward", "v", "vor", "vorwaerts", "vorwärts"]:
            stop_autopilot(silent=True)
            apply_motor("forward", speed)
            print(f"Status: VORWÄRTS {int(speed * 100)}%")
            continue

        if cmd in ["b", "back", "backward", "r", "rueck", "rück", "rueckwaerts", "rückwärts"]:
            stop_autopilot(silent=True)
            apply_motor("backward", speed)
            print(f"Status: RÜCKWÄRTS {int(speed * 100)}%")
            continue

        print("Unbekannter Befehl. 'help' zeigt alle Befehle.")

    cleanup()
    print("Motor aus. Programm beendet.")


atexit.register(cleanup)

if __name__ == "__main__":
    main()
