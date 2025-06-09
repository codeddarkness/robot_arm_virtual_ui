#!/usr/bin/env python3
# mpu6050_monitor.py - v1.0.4
# Console monitor for MPU6050 sensor with web interface - vv1.0.5

import time
import json
import os
import math
import argparse
import logging
import signal
import sys
import threading
import subprocess
from datetime import datetime
import board
import busio
import adafruit_mpu6050
from flask import Flask, request, render_template, jsonify, send_file, Response

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mpu6050_monitor")

# Create Flask app for web server
app = Flask("mpu6050_web_server")
# Redirect Flask logging to file
app.logger.handlers = []
handler = logging.FileHandler('web_server.log')
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Global start time for uptime tracking
start_time = time.time()

# Global sensor data (updated by background thread)
sensor_data = {
    "acceleration": {"x": 0, "y": 0, "z": 0},
    "gyro": {"x": 0, "y": 0, "z": 0},
    "temperature": 0
}

# Global flag to control the main loop
running = True

# Configuration
CONFIG = {
    "data_file": "sensor_data.json",
    "sample_rate": 0.1,  # seconds
    "calibration": {
        "x_offset": 0,
        "y_offset": 0,
        "z_offset": 0,
        "calibrated": False
    }
}

def load_config():
    """Load config from file if exists"""
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return CONFIG

def save_config(config):
    """Save config to file"""
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

def init_sensor():
    """Initialize the MPU6050 sensor"""
    config = load_config()
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        mpu = adafruit_mpu6050.MPU6050(i2c)
        logger.info("MPU6050 sensor initialized successfully")
        return mpu, config
    except Exception as e:
        logger.error(f"Error initializing sensor: {e}")
        logger.error("Check I2C connections and make sure MPU6050 is properly connected.")
        return None, config

def read_sensor(mpu, config):
    """Read sensor data with calibration applied"""
    ax, ay, az = mpu.acceleration
    gx, gy, gz = mpu.gyro
    temp = mpu.temperature
    
    # Apply calibration if available
    if config["calibration"]["calibrated"]:
        ax += config["calibration"]["x_offset"]
        ay += config["calibration"]["y_offset"]
        az += config["calibration"]["z_offset"]
    
    return {
        "acceleration": {"x": ax, "y": ay, "z": az},
        "gyro": {"x": gx, "y": gy, "z": gz},
        "temperature": temp
    }

def save_data(data, config):
    """Save data to JSON file"""
    # Load existing data if file exists
    if os.path.exists(config["data_file"]):
        try:
            with open(config["data_file"], "r") as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                else:
                    existing_data = {"readings": []}
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {"readings": []}
    else:
        existing_data = {"readings": []}
    
    # Add new data and save
    if "readings" not in existing_data:
        existing_data["readings"] = []
    
    existing_data["readings"].append(data)
    
    # Save with proper formatting
    with open(config["data_file"], "w") as f:
        json.dump(existing_data, f, indent=2)

def get_direction_arrow(ax, ay):
    """Return ASCII arrow indicating direction based on acceleration"""
    if abs(ax) < 0.3 and abs(ay) < 0.3:
        return "•"  # Neutral
    
    # Determine primary direction
    if abs(ax) > abs(ay):
        return "→" if ax > 0 else "←"
    else:
        return "↑" if ay > 0 else "↓"

def get_horizontal_arrow(value, threshold=0.3):
    """Get horizontal arrow for value"""
    if value > threshold:
        return "→"
    elif value < -threshold:
        return "←"
    return " "

def get_vertical_arrow(value, threshold=0.3):
    """Get vertical arrow for value"""
    if value > threshold:
        return "↑"
    elif value < -threshold:
        return "↓"
    return " "

def calibrate_sensor(mpu):
    """Calibrate by taking 100 readings and finding average offset"""
    print("Calibrating sensor. Please keep the sensor still and level...")
    x_vals, y_vals, z_vals = [], [], []
    
    # Collect samples
    for i in range(100):
        ax, ay, az = mpu.acceleration
        x_vals.append(ax)
        y_vals.append(ay)
        z_vals.append(az - 9.8)  # Subtract gravity from z axis
        time.sleep(0.01)
        print(f"Calibrating: {i+1}/100", end="\r")
    
    # Calculate offsets (ideal: x=0, y=0, z=0 after gravity compensation)
    config = load_config()
    config["calibration"]["x_offset"] = -sum(x_vals) / len(x_vals)
    config["calibration"]["y_offset"] = -sum(y_vals) / len(y_vals)
    config["calibration"]["z_offset"] = -sum(z_vals) / len(z_vals)
    config["calibration"]["calibrated"] = True
    
    save_config(config)
    print("\nCalibration complete!")
    return config

def sensor_thread():
    """Background thread to continuously read sensor data"""
    global sensor_data, running
    mpu, config = init_sensor()
    
    if mpu is None:
        logger.warning("Sensor initialization failed. Using dummy data.")
        # Return dummy data for testing
        while running:
            sensor_data = {
                "acceleration": {"x": 0, "y": 0, "z": 9.8},
                "gyro": {"x": 0, "y": 0, "z": 0},
                "temperature": 25
            }
            time.sleep(0.1)
        return
    
    # Buffer for data logging
    data_buffer = []
    
    while running:
        try:
            # Read sensor data
            data = read_sensor(mpu, config)
            sensor_data = data
            
            # Add to buffer
            data_with_timestamp = data.copy()
            data_with_timestamp["timestamp"] = datetime.now().isoformat()
            data_buffer.append(data_with_timestamp)
            
            # Save to file periodically (every 10 readings)
            if len(data_buffer) >= 10:
                for item in data_buffer:
                    save_data(item, config)
                data_buffer = []
                
            time.sleep(config["sample_rate"])
                
        except Exception as e:
            logger.error(f"Error reading sensor: {e}")
            time.sleep(1)  # Retry after a longer delay

def run_text_console_mode(mpu, config):
    """Run in text-only console mode showing sensor data without fancy formatting"""
    global running
    
    # Import here to avoid potential circular import
    import select
    import sys
    import termios
    import tty
    
    # Save original terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode to better handle keypresses
        tty.setraw(sys.stdin.fileno())
        
        while running:
            # Get sensor data
            data = sensor_data
            
            # Get values
            ax = data["acceleration"]["x"]
            ay = data["acceleration"]["y"]
            az = data["acceleration"]["z"]
            
            gx = data["gyro"]["x"]
            gy = data["gyro"]["y"]
            gz = data["gyro"]["z"]
            
            temp = data["temperature"]
            temp_f = (temp * 9/5) + 32
            
            # Direction arrows
            acc_x_arrow = get_horizontal_arrow(ax)
            acc_y_arrow = get_vertical_arrow(ay)
            acc_z_arrow = get_horizontal_arrow(az)
            
            gyro_x_arrow = get_vertical_arrow(gx)
            gyro_y_arrow = get_vertical_arrow(gy)
            gyro_z_arrow = get_horizontal_arrow(gz)
            
            overall_direction = get_direction_arrow(ax, ay)
            
            # Clear screen with less aggressive technique
            print("\033[H\033[J", end="")
            
            # Simple output without borders
            print("MPU6050 MONITOR vv1.0.5 - TEXT MODE")
            print("---------------------------------")
            print(f"Acceleration (m/s²): X: {ax:7.2f} {acc_x_arrow} Y: {ay:7.2f} {acc_y_arrow} Z: {az:7.2f} {acc_z_arrow}")
            print(f"Gyroscope (rad/s):   X: {gx:7.2f} {gyro_x_arrow} Y: {gy:7.2f} {gyro_y_arrow} Z: {gz:7.2f} {gyro_z_arrow}")
            print(f"Temperature:         {temp:5.1f}°C / {temp_f:5.1f}°F")
            print(f"Direction:           {overall_direction}")
            print("---------------------------------")
            print("Web Interface: http://localhost:5000")
            print("[c] Calibrate  [q] Quit")
            
            # Use select with a short timeout to allow for responsive exit
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                key = sys.stdin.read(1)
                if key.lower() == "q":
                    break
                elif key.lower() == "c":
                    # Reset terminal to normal mode for calibration
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    calibrate_sensor(mpu)
                    # Set back to raw mode after calibration
                    tty.setraw(sys.stdin.fileno())
            
            # Short sleep time for responsive updates
            time.sleep(0.05)
            
    except Exception as e:
        logger.error(f"Text console mode error: {e}")
    finally:
        # Always restore terminal settings
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            print("\nExiting text console mode...")
        except:
            pass
    
    # Ensure global running flag is set to False
    running = False

#######################################
def run_console_mode(mpu, config):
    """Run in console mode showing sensor data"""
    global running
    
    # Import here to avoid potential circular import
    import select
    import sys
    import termios
    import tty
    
    # Save original terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode to better handle keypresses
        tty.setraw(sys.stdin.fileno())
        
        while running:
            # Get sensor data
            data = sensor_data
            
            # Get direction arrows
            ax = data["acceleration"]["x"]
            ay = data["acceleration"]["y"]
            az = data["acceleration"]["z"]
            
            gx = data["gyro"]["x"]
            gy = data["gyro"]["y"]
            gz = data["gyro"]["z"]
            
            temp = data["temperature"]
            temp_f = (temp * 9/5) + 32
            
            # Direction arrows
            acc_x_arrow = get_horizontal_arrow(ax)
            acc_y_arrow = get_vertical_arrow(ay)
            acc_z_arrow = get_horizontal_arrow(az)
            
            gyro_x_arrow = get_vertical_arrow(gx)
            gyro_y_arrow = get_vertical_arrow(gy)
            gyro_z_arrow = get_horizontal_arrow(gz)
            
            overall_direction = get_direction_arrow(ax, ay)
            
            # Prepare display in a buffer to avoid flicker
            output = []
            output.append("╔════════════════════════════════════════════════════════════╗")
            output.append("║               MPU6050 MONITOR vv1.0.5                       ║")
            output.append("╠════════════════════════════════════════════════════════════╣")
            output.append(f"║ Accel(m/s²) X: {ax:6.2f}{acc_x_arrow} Y: {ay:6.2f}{acc_y_arrow} Z: {az:6.2f}{acc_z_arrow} | Gyro(rad/s) X: {gx:6.2f}{gyro_x_arrow} Y: {gy:6.2f}{gyro_y_arrow} Z: {gz:6.2f}{gyro_z_arrow} | Temp: {temp:5.1f}°C / {temp_f:5.1f}°F ║")
            output.append("╠════════════════════════════════════════════════════════════╣")
            output.append(f"║ Direction: {overall_direction}                                               ║")
            output.append(f"║ Web Interface: http://localhost:5000                       ║")
            output.append("╠════════════════════════════════════════════════════════════╣")
            output.append("║ [c] Calibrate  [q] Quit                                    ║")
            output.append("╚════════════════════════════════════════════════════════════╝")
            
            # Clear screen first
            os.system('clear')
            
            # Print entire display at once to avoid formatting issues
            print("\n".join(output))
            
            # Use select with a short timeout to allow for responsive exit
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                key = sys.stdin.read(1)
                if key.lower() == 'q':
                    break
                elif key.lower() == 'c':
                    # Reset terminal to normal mode for calibration
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    calibrate_sensor(mpu)
                    # Set back to raw mode after calibration
                    tty.setraw(sys.stdin.fileno())
            
            # Reduce flicker by using a slightly longer sleep
            time.sleep(0.05)  # 50ms refresh rate
            
    except Exception as e:
        logger.error(f"Console mode error: {e}")
    finally:
        # Always restore terminal settings
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            print("\nExiting console mode...")
        except:
            pass
    
    # Ensure global running flag is set to False
    running = False

def signal_handler(sig, frame):
    """Handle Ctrl+C with improved safety"""
    global running
    
    # Avoid nested prints or repeated calls
    if running:
        running = False
        sys.stdout.write("\nInterrupted. Shutting down...\n")
        sys.stdout.flush()
        
        # Attempt a clean exit
        try:
            sys.exit(0)
        except:
            pass

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return jsonify(sensor_data)

@app.route('/logdata')
def get_log_data():
    config = load_config()
    try:
        with open(config["data_file"], "r") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"readings": []})

@app.route('/download')
def download_data():
    config = load_config()
    return send_file(config["data_file"], as_attachment=True)

# API Routes
@app.route('/api/v1/data')
def api_get_data():
    """API endpoint to get current sensor data"""
    return jsonify({
        "version": "1.0.4",
        "timestamp": datetime.now().isoformat(),
        "data": sensor_data
    })

@app.route('/api/v1/status')
def api_get_status():
    """API endpoint to get system status"""
    config = load_config()
    return jsonify({
        "version": "1.0.4",
        "uptime": time.time() - start_time,
        "calibrated": config["calibration"]["calibrated"],
        "sample_rate": config["sample_rate"],
        "data_file": config["data_file"]
    })

@app.route('/api/v1/log')
def api_get_log():
    """API endpoint to get logged data"""
    config = load_config()
    try:
        with open(config["data_file"], "r") as f:
            content = f.read().strip()
            if content:
                return jsonify(json.loads(content))
            else:
                return jsonify({"readings": []})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"readings": []})

@app.route('/api/v1/calibrate', methods=['POST'])
def api_calibrate():
    """API endpoint to trigger calibration"""
    global sensor_data
    
    # We can't directly calibrate the sensor here as it requires console input
    # So just return the current calibration values
    config = load_config()
    
    return jsonify({
        "status": "success",
        "message": "Current calibration values returned. Use console mode for full calibration.",
        "calibration": config["calibration"]
    })

def start_web_server():
    """Start the Flask web server"""
    # Configure logging to file only for werkzeug
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Only log errors
    file_handler = logging.FileHandler('web_server.log')
    file_handler.setLevel(logging.ERROR)
    log.addHandler(file_handler)
    log.disabled = True  # Disable console output
    
    # Start the server
    logger.info("Starting web server at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    """Main function"""
    global running
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MPU6050 Monitor")
    parser.add_argument("--web-only", action="store_true", help="Run in web mode only (no console)")
    parser.add_argument("--console-only", action="store_true", help="Run in console mode only (no web server)")
    parser.add_argument("--text-only", action="store_true", help="Run in text-only console mode (no web server)")
    parser.add_argument("--text-console", action="store_true", help="Run in text console with web server")
    args = parser.parse_args()

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize sensor
    mpu, config = init_sensor()

    # Start sensor reading thread
    sensor_daemon = threading.Thread(target=sensor_thread, daemon=True)
    sensor_daemon.start()

    # Start based on mode
    if args.web_only:
        # Web server only
        start_web_server()
    elif args.console_only:
        # Console only
        run_console_mode(mpu, config)
    elif args.text_only:
        # Text console only
        run_text_console_mode(mpu, config)
    elif args.text_console:
        # Text console with web server
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        
        # Run text console in main thread
        run_text_console_mode(mpu, config)
    else:
        # Both console and web server
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        
        # Run console in main thread
        run_console_mode(mpu, config)

    # Cleanup
    running = False
    print("\nExiting MPU6050 Monitor...")

if __name__ == "__main__":
    main()
