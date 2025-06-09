#!/usr/bin/env python3
#!/usr/bin/env python3
import evdev
import signal
import sys
import Adafruit_PCA9685
import time
import json
import threading
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from smbus2 import SMBus
from evdev import InputDevice, categorize, ecodes
from adafruit_pca9685 import PCA9685
from adafruit_mpu6050 import MPU6050
import board
import busio

# Configure logging to suppress repetitive waitress messages
logging.basicConfig(level=logging.INFO)
# Filter out waitress.queue messages containing "Task queue depth"
class TaskQueueFilter(logging.Filter):
    def filter(self, record):
        return not (record.name == 'waitress.queue' and 'Task queue depth' in record.getMessage())

# Apply filter to all relevant loggers
for logger_name in ['waitress', 'waitress.queue', 'waitress.channel', 'waitress.task']:
    logging.getLogger(logger_name).addFilter(TaskQueueFilter())
    # Set higher level for waitress loggers to reduce verbosity
    logging.getLogger(logger_name).setLevel(logging.WARNING)

DEVICE_PATH = "/dev/input/event3"
LOG_FILE = "servo_log.json"

app = Flask(__name__)

def log_data():
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "servo_positions": servo_positions,
        "mpu_accel": [float(x) for x in mpu.acceleration],
        "mpu_gyro": [float(x) for x in mpu.gyro],
        "i2c_status": i2c_status
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")
    return data

def update_display():
    while True:
        display_status()
        time.sleep(0.1)  # Update every 100ms

def check_i2c_devices():
    devices = {}
    bus = SMBus(1)
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            if addr == 0x68:
                devices[addr] = "MPU6050"
            elif addr == 0x40:
                devices[addr] = "PCA9685"
            elif addr == 0x70:
                devices[addr] = "SparkFun Qwiic"  # Update with actual device name if known
            else:
                devices[addr] = "Unknown"
        except:
            pass
    bus.close()
    return devices

# Initialize I2C bus
i2c_status = {"connected": False, "devices": {}}
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    i2c_status["connected"] = True
    i2c_status["devices"] = check_i2c_devices()
    print("I2C bus initialized successfully")
    print(f"I2C devices found: {i2c_status['devices']}")
except Exception as e:
    i2c_status["error"] = str(e)
    print(f"I2C initialization error: {e}")

# Initialize other hardware
try:
    pwm = Adafruit_PCA9685.PCA9685(busnum=1)
    pwm.set_pwm_freq(50)
    print("PCA9685 initialized successfully")
except Exception as e:
    print(f"PCA9685 initialization error: {e}")

try:
    mpu = MPU6050(i2c)
    print("MPU6050 initialized successfully")
except Exception as e:
    print(f"MPU6050 initialization error: {e}")
    # Create a dummy MPU object if hardware not available
    class DummyMPU:
        @property
        def acceleration(self):
            return (0, 0, 0)
        @property
        def gyro(self):
            return (0, 0, 0)
    mpu = DummyMPU()

SERVO_MIN, SERVO_MAX, SERVO_RANGE = 150, 600, 180
SERVO_CHANNELS = [0, 1, 2, 3]
hold_state = {ch: False for ch in SERVO_CHANNELS}
servo_positions = {ch: 90 for ch in SERVO_CHANNELS}
speed = 1.0

# Track Xbox controller status
xbox_controller_status = {"connected": False, "last_event": None}

def joystick_to_pwm(value):
    angle = int(((value + 32767) / 65534) * SERVO_RANGE)
    pwm_value = int(SERVO_MIN + (angle / SERVO_RANGE) * (SERVO_MAX - SERVO_MIN))
    return pwm_value, angle

def move_servo(channel, value):
    if not hold_state[channel]:
        pwm_value, angle = joystick_to_pwm(value)
        try:
            pwm.set_pwm(channel, 0, pwm_value)
        except Exception as e:
            print(f"Error setting PWM: {e}")
        servo_positions[channel] = angle
        return log_data()

def move_all_servos(angle):
    pwm_value = int(SERVO_MIN + (angle / SERVO_RANGE) * (SERVO_MAX - SERVO_MIN))
    for channel in SERVO_CHANNELS:
        try:
            pwm.set_pwm(channel, 0, pwm_value)
        except Exception as e:
            print(f"Error setting PWM: {e}")
        servo_positions[channel] = angle
    return log_data()

def toggle_hold(channel=None):
    if channel is None:
        for ch in hold_state:
            hold_state[ch] = not hold_state[ch]
    else:
        hold_state[channel] = not hold_state[channel]

def stop_all_servos():
    try:
        pwm.set_all_pwm(0, 0)
        for channel in SERVO_CHANNELS:
            servo_positions[channel] = 90
        print("All servos stopped.")
    except Exception as e:
        print(f"Error stopping servos: {e}")

def reset_speed():
    global speed
    speed = 1.0

def display_status():
    arrows = {"left": "\u2190", "right": "\u2192", "up": "\u2191", "down": "\u2193", "neutral": "O"}
    lx = arrows["left"] if servo_positions[0] < 80 else arrows["right"] if servo_positions[0] > 100 else arrows["neutral"]
    ly = arrows["up"] if servo_positions[1] < 80 else arrows["down"] if servo_positions[1] > 100 else arrows["neutral"]
    ry = arrows["up"] if servo_positions[2] < 80 else arrows["down"] if servo_positions[2] > 100 else arrows["neutral"]
    rx = arrows["left"] if servo_positions[3] < 80 else arrows["right"] if servo_positions[3] > 100 else arrows["neutral"]
    hold_status = {ch: "ON" if hold_state[ch] else "OFF" for ch in hold_state}
    accel = mpu.acceleration
    gyro = mpu.gyro

    # Adjusted thresholds based on observed values
    # Direction arrows for accelerometer
    mpu_x = arrows["left"] if accel[0] < -4 else arrows["right"] if accel[0] > 4 else arrows["neutral"]
    mpu_y = arrows["up"] if accel[1] > 2 else arrows["down"] if accel[1] < -2 else arrows["neutral"]
    mpu_z = arrows["up"] if accel[2] > 10 else arrows["down"] if accel[2] < 6 else arrows["neutral"]

    # Direction arrows for gyroscope
    gyro_x = arrows["left"] if gyro[0] < -1 else arrows["right"] if gyro[0] > 1 else arrows["neutral"]
    gyro_y = arrows["up"] if gyro[1] > 1 else arrows["down"] if gyro[1] < -1 else arrows["neutral"]
    gyro_z = arrows["left"] if gyro[2] < -1 else arrows["right"] if gyro[2] > 1 else arrows["neutral"]

    # Simplified I2C device display focusing on MPU and PCA
    i2c_devices_str = ""
    pca_status = "-"
    mpu_status = "-"

    for addr, name in i2c_status["devices"].items():
        if name == "PCA9685":
            pca_status = "+"
        elif name == "MPU6050":
            mpu_status = "+"

    i2c_status_str = f"I2C: PCA{pca_status} MPU{mpu_status}"

    # Xbox controller status
    xbox_status = "XBOX: " + ("+" if xbox_controller_status["connected"] else "-")

    # Check terminal support for ANSI escape codes
    term = os.environ.get('TERM', '')
    supports_ansi = term in ['xterm', 'xterm-color', 'xterm-256color', 'linux', 'screen']

    # Compact one-line status display with smaller font if supported
    sys.stdout.write("\033[2K")  # Clear the line
    if supports_ansi:
        sys.stdout.write("\033[10m")  # Smaller font (ANSI escape code)

    # Add spaces between labels and values for better readability
    status_str = (
        f"LX: {lx} {servo_positions[0]:03d}  LY: {ly} {servo_positions[1]:03d}  "
        f"RY: {ry} {servo_positions[2]:03d}  RX: {rx} {servo_positions[3]:03d} | "
        f"Accel: {mpu_x} X {accel[0]:.1f}  {mpu_y} Y {accel[1]:.1f}  {mpu_z} Z {accel[2]:.1f} | "
        f"Gyro: {gyro_x} X {gyro[0]:.1f}  {gyro_y} Y {gyro[1]:.1f}  {gyro_z} Z {gyro[2]:.1f} | "
        f"Hold: B {hold_status[0][0]}  A {hold_status[1][0]}  Y {hold_status[2][0]}  X {hold_status[3][0]}  "
        f"S: {speed:.1f} | {i2c_status_str} | {xbox_status}"
    )

    # Print status (stays on one line)
    sys.stdout.write(f"\r{status_str}")
    sys.stdout.flush()

def read_xbox_controller():
    global xbox_controller_status
    try:
        gamepad = evdev.InputDevice(DEVICE_PATH)
        xbox_controller_status["connected"] = True
        print(f"Listening for input from {gamepad.name} ({DEVICE_PATH})")
        print("Use the left and right sticks to control servos. Press 'Ctrl+C' to exit.")
        for event in gamepad.read_loop():
            xbox_controller_status["last_event"] = time.time()
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    move_servo(0, event.value)
                elif event.code == evdev.ecodes.ABS_Y:
                    move_servo(1, event.value)
                elif event.code == evdev.ecodes.ABS_RY:
                    move_servo(2, event.value)
                elif event.code == evdev.ecodes.ABS_RX:
                    move_servo(3, event.value)
                elif event.code == 2:
                    move_all_servos(0 if event.value > 128 else 90)
                elif event.code == 5:
                    move_all_servos(180 if event.value > 128 else 90)
            elif event.type == evdev.ecodes.EV_KEY:
                if event.code == 704 and event.value == 1:
                    move_all_servos(0)
                elif event.code == 705 and event.value == 1:
                    move_all_servos(180)
                elif event.code == 706 and event.value == 1:
                    move_all_servos(90)
                elif event.code == 707 and event.value == 1:
                    toggle_hold()
                elif event.code == 304 and event.value == 1:
                    toggle_hold(1)
                elif event.code == 305 and event.value == 1:
                    toggle_hold(0)
                elif event.code == 308 and event.value == 1:
                    toggle_hold(2)
                elif event.code == 307 and event.value == 1:
                    toggle_hold(3)
                elif event.code == 310 and event.value == 1:
                    speed = max(0.1, speed - 0.1)
                elif event.code == 311 and event.value == 1:
                    speed = min(2.0, speed + 0.1)
                elif event.code == 315 and event.value == 1:
                    stop_all_servos()
                    reset_speed()
    except FileNotFoundError:
        xbox_controller_status["connected"] = False
        print(f"Error: Controller not found at {DEVICE_PATH}.")
        print("Check if your controller is connected and the path is correct.")
        print(f"You can modify DEVICE_PATH in the code if needed.")
    except PermissionError:
        xbox_controller_status["connected"] = False
        print(f"Permission denied. Try running with 'sudo'.")
    except Exception as e:
        xbox_controller_status["connected"] = False
        print(f"Error with controller input: {e}")
        print("You can still use the web interface to control servos.")

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    data = {
        "servo_positions": servo_positions,
        "mpu_accel": [float(x) for x in mpu.acceleration],
        "mpu_gyro": [float(x) for x in mpu.gyro],
        "hold_state": hold_state,
        "i2c_status": i2c_status,
        "speed": speed,
        "xbox_status": xbox_controller_status["connected"]
    }
    return jsonify(data)

@app.route('/api/servo/<int:channel>/<int:angle>', methods=['POST'])
def set_servo(channel, angle):
    if channel in SERVO_CHANNELS and 0 <= angle <= 180:
        try:
            pwm_value = int(SERVO_MIN + (angle / SERVO_RANGE) * (SERVO_MAX - SERVO_MIN))
            pwm.set_pwm(channel, 0, pwm_value)
            servo_positions[channel] = angle
            log_data()
            return jsonify({"success": True, "channel": channel, "angle": angle})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "Invalid channel or angle"})

@app.route('/api/hold/<int:channel>', methods=['POST'])
def toggle_hold_api(channel):
    if channel in SERVO_CHANNELS:
        toggle_hold(channel)
        return jsonify({"success": True, "channel": channel, "hold": hold_state[channel]})
    return jsonify({"success": False, "error": "Invalid channel"})

@app.route('/api/stop', methods=['POST'])
def stop_servos_api():
    stop_all_servos()
    reset_speed()
    return jsonify({"success": True})

@app.route('/api/speed/<float:value>', methods=['POST'])
def set_speed_api(value):
    global speed
    if 0.1 <= value <= 2.0:
        speed = value
        return jsonify({"success": True, "speed": speed})
    return jsonify({"success": False, "error": "Invalid speed value"})

@app.route('/api/logs')
def get_logs():
    if os.path.exists(LOG_FILE):
        logs = []
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except:
                    pass
        return jsonify(logs[-100:])  # Return last 100 log entries
    return jsonify([])

@app.route('/api/download-logs')
def download_logs():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    return jsonify({"error": "Log file not found"})

def start_flask():
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Copy the template file to the templates directory
    # Make sure to put the HTML file in the same directory as your script
    import shutil
    try:
        shutil.copy('index.html', 'templates/index.html')
        print("Template file copied successfully")
    except Exception as e:
        print(f"Error copying template: {e}")
        # Create a minimal template as fallback
        with open('templates/index.html', 'w') as f:
            f.write('<html><body><h1>Servo Controller</h1><p>Template error. Check console.</p></body></html>')

    # Try to use waitress if available, otherwise fall back to Flask's server
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000)
    except ImportError:
        print("Waitress not installed. Using Flask's built-in server instead.")
        print("For production use, consider installing waitress: pip install waitress")
        app.run(host="0.0.0.0", port=5000, threaded=True)

def signal_handler(sig, frame):
    print("\nStopping servos and exiting...")
    stop_all_servos()
    sys.exit(0)

def main():
    # Create a signal handler to stop servos on exit
    signal.signal(signal.SIGINT, signal_handler)

    # Start display thread
    display_thread = threading.Thread(target=update_display, daemon=True)
    display_thread.start()

    # Start Flask thread with error handling
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Start controller input thread
    try:
        read_xbox_controller()
    except FileNotFoundError:
        print(f"Error: Controller not found at {DEVICE_PATH}.")
        print("Check if your controller is connected and the path is correct.")
        print(f"You can modify DEVICE_PATH in the code if needed.")
    except Exception as e:
        print(f"Error with controller input: {e}")
        print("You can still use the web interface to control servos.")

    # Wait for threads to complete
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        stop_all_servos()
        sys.exit(0)

if __name__ == "__main__":
    main()
