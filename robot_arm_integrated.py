#!/usr/bin/env python3
"""
Integrated Robot Arm Controller
Combines virtual UI with physical hardware control
Dashboard-based navigation system
"""

import os
import logging
import socket
import json
import time
import threading
import math
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for

# Try to import hardware libraries
try:
    import Adafruit_PCA9685
    PCA9685_AVAILABLE = True
except ImportError:
    PCA9685_AVAILABLE = False

try:
    from mpu6050 import mpu6050
    MPU6050_AVAILABLE = True
except ImportError:
    MPU6050_AVAILABLE = False

try:
    import evdev
    from evdev import InputDevice, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_robot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state
system_state = {
    'virtual_arm': {
        'channel0': 135, 'channel1': 135, 'channel2': 135, 'channel3': 135
    },
    'physical_servos': {
        0: 90, 1: 90, 2: 90, 3: 90
    },
    'hardware': {
        'pca9685': {'connected': False, 'bus': None},
        'mpu6050': {'connected': False, 'bus': None},
        'controller': {'connected': False, 'type': None, 'path': None}
    },
    'mpu_data': {
        'accel': {'x': 0, 'y': 0, 'z': 0},
        'gyro': {'x': 0, 'y': 0, 'z': 0},
        'temp': 0,
        'direction': {'x': "neutral", 'y': "neutral", 'z': "neutral"}
    },
    'controller_state': {
        'hold_states': {0: False, 1: False, 2: False, 3: False},
        'lock_state': False,
        'speed': 1.0
    },
    'sync_enabled': True,  # Whether virtual and physical are synchronized
    'active_mode': 'dashboard'  # dashboard, virtual, physical, controller
}

# Hardware instances
pwm = None
mpu = None
gamepad = None

# Database setup
DB_PATH = 'integrated_robot.db'

def setup_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            mode TEXT,
            action TEXT,
            data TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servo_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            virtual_state TEXT,
            physical_state TEXT,
            mpu_data TEXT,
            hardware_status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def log_activity(mode, action, data=None):
    """Log system activity"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (timestamp, mode, action, data) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), mode, action, json.dumps(data) if data else None)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database logging error: {e}")

def detect_hardware():
    """Detect and initialize available hardware"""
    global pwm, mpu, system_state
    
    # Detect PCA9685
    if PCA9685_AVAILABLE:
        for bus_num in [0, 1]:
            try:
                test_pwm = Adafruit_PCA9685.PCA9685(busnum=bus_num)
                test_pwm.set_pwm_freq(50)
                pwm = test_pwm
                system_state['hardware']['pca9685'] = {'connected': True, 'bus': bus_num}
                logger.info(f"PCA9685 found on I2C bus {bus_num}")
                break
            except Exception as e:
                logger.debug(f"PCA9685 not found on bus {bus_num}: {e}")
    
    # Detect MPU6050
    if MPU6050_AVAILABLE:
        for bus_num in [0, 1]:
            try:
                test_mpu = mpu6050(bus_num)
                test_mpu.get_temp()  # Test read
                mpu = test_mpu
                system_state['hardware']['mpu6050'] = {'connected': True, 'bus': bus_num}
                logger.info(f"MPU6050 found on I2C bus {bus_num}")
                break
            except Exception as e:
                logger.debug(f"MPU6050 not found on bus {bus_num}: {e}")
    
    # Detect game controller
    if EVDEV_AVAILABLE:
        try:
            devices = [InputDevice(path) for path in evdev.list_devices()]
            for device in devices:
                if any(keyword in device.name.lower() for keyword in ['xbox', 'playstation', 'ps3']):
                    controller_type = 'PS3' if 'playstation' in device.name.lower() or 'ps3' in device.name.lower() else 'Xbox'
                    system_state['hardware']['controller'] = {
                        'connected': True, 
                        'type': controller_type, 
                        'path': device.path
                    }
                    logger.info(f"{controller_type} controller found: {device.name}")
                    break
        except Exception as e:
            logger.debug(f"Controller detection error: {e}")

def update_mpu_data():
    """Update MPU6050 sensor data"""
    global mpu, system_state
    
    if mpu and system_state['hardware']['mpu6050']['connected']:
        try:
            accel_data = mpu.get_accel_data()
            gyro_data = mpu.get_gyro_data()
            temp = mpu.get_temp()
            
            system_state['mpu_data'] = {
                'accel': accel_data,
                'gyro': gyro_data,
                'temp': temp,
                'direction': {
                    'x': "right" if accel_data['x'] > 0.5 else "left" if accel_data['x'] < -0.5 else "neutral",
                    'y': "up" if accel_data['y'] > 0.5 else "down" if accel_data['y'] < -0.5 else "neutral",
                    'z': "up" if accel_data['z'] > 9.8 + 0.5 else "down" if accel_data['z'] < 9.8 - 0.5 else "neutral"
                }
            }
        except Exception as e:
            logger.error(f"MPU6050 read error: {e}")
    else:
        # Simulation data
        t = time.time()
        system_state['mpu_data'] = {
            'accel': {
                'x': math.sin(t * 0.5) * 0.5,
                'y': math.cos(t * 0.7) * 0.5,
                'z': 9.8 + math.sin(t * 0.3) * 0.2
            },
            'gyro': {
                'x': math.sin(t * 0.2) * 2,
                'y': math.cos(t * 0.4) * 2,
                'z': math.sin(t * 0.6) * 2
            },
            'temp': 25 + math.sin(t * 0.1) * 0.5,
            'direction': {
                'x': "neutral", 'y': "neutral", 'z': "neutral"
            }
        }

def sync_servo_positions():
    """Synchronize virtual and physical servo positions"""
    if system_state['sync_enabled'] and pwm and system_state['hardware']['pca9685']['connected']:
        try:
            for channel in range(4):
                # Convert virtual angle (0-270) to physical PWM (150-600)
                virtual_angle = system_state['virtual_arm'][f'channel{channel}']
                # Map to 0-180 range for physical servos
                physical_angle = int((virtual_angle / 270) * 180)
                system_state['physical_servos'][channel] = physical_angle
                
                # Set PWM
                pwm_value = int(150 + (physical_angle / 180.0) * (600 - 150))
                pwm.set_pwm(channel, 0, pwm_value)
        except Exception as e:
            logger.error(f"Servo sync error: {e}")

def background_update_thread():
    """Background thread for updating sensors and synchronization"""
    while True:
        try:
            update_mpu_data()
            if system_state['sync_enabled']:
                sync_servo_positions()
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Background update error: {e}")
            time.sleep(1)

# Flask Routes

@app.route('/')
def dashboard():
    """Main dashboard"""
    system_state['active_mode'] = 'dashboard'
    return render_template('dashboard.html', state=system_state)

@app.route('/virtual')
def virtual_interface():
    """Virtual robot arm interface"""
    system_state['active_mode'] = 'virtual'
    return render_template('virtual_arm.html', state=system_state)

@app.route('/physical')
def physical_interface():
    """Physical hardware interface"""
    system_state['active_mode'] = 'physical'
    return render_template('physical_control.html', state=system_state)

@app.route('/controller')
def controller_interface():
    """Game controller interface"""
    system_state['active_mode'] = 'controller'
    return render_template('controller_monitor.html', state=system_state)

@app.route('/mpu')
def mpu_interface():
    """MPU6050 sensor interface"""
    system_state['active_mode'] = 'mpu'
    return render_template('mpu_monitor.html', state=system_state)

# API Routes

@app.route('/api/status')
def api_status():
    """Get complete system status"""
    return jsonify(system_state)

@app.route('/api/virtual/servo', methods=['GET', 'POST'])
def api_virtual_servo():
    """Virtual servo control API"""
    if request.method == 'GET':
        return jsonify(system_state['virtual_arm'])
    
    data = request.get_json()
    if data:
        for channel in range(4):
            key = f'channel{channel}'
            if key in data:
                value = max(0, min(270, int(data[key])))
                system_state['virtual_arm'][key] = value
        
        log_activity('virtual', 'servo_update', system_state['virtual_arm'])
        return jsonify({"status": "success", "state": system_state['virtual_arm']})
    
    return jsonify({"error": "No data provided"}), 400

@app.route('/api/physical/servo/<int:channel>/<int:angle>', methods=['POST'])
def api_physical_servo(channel, angle):
    """Physical servo control API"""
    if 0 <= channel <= 3 and 0 <= angle <= 180:
        system_state['physical_servos'][channel] = angle
        
        if pwm and system_state['hardware']['pca9685']['connected']:
            try:
                pwm_value = int(150 + (angle / 180.0) * (600 - 150))
                pwm.set_pwm(channel, 0, pwm_value)
                log_activity('physical', 'servo_move', {'channel': channel, 'angle': angle})
                return jsonify({"success": True, "channel": channel, "angle": angle})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            # Simulation mode
            log_activity('physical', 'servo_move_sim', {'channel': channel, 'angle': angle})
            return jsonify({"success": True, "channel": channel, "angle": angle, "mode": "simulation"})
    
    return jsonify({"error": "Invalid parameters"}), 400

@app.route('/api/sync', methods=['POST'])
def api_sync_toggle():
    """Toggle synchronization between virtual and physical"""
    system_state['sync_enabled'] = not system_state['sync_enabled']
    log_activity('system', 'sync_toggle', {'enabled': system_state['sync_enabled']})
    return jsonify({"sync_enabled": system_state['sync_enabled']})

@app.route('/api/controller/hold/<int:channel>', methods=['POST'])
def api_controller_hold(channel):
    """Toggle servo hold state (from controller interface)"""
    if 0 <= channel <= 3:
        system_state['controller_state']['hold_states'][channel] = not system_state['controller_state']['hold_states'][channel]
        log_activity('controller', 'hold_toggle', {'channel': channel, 'state': system_state['controller_state']['hold_states'][channel]})
        return jsonify({"success": True, "channel": channel, "hold": system_state['controller_state']['hold_states'][channel]})
    return jsonify({"error": "Invalid channel"}), 400

@app.route('/api/logs')
def api_logs():
    """Get activity logs"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'timestamp': row[1],
                'mode': row[2],
                'action': row[3],
                'data': json.loads(row[4]) if row[4] else None
            })
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        except Exception:
            continue
    return start_port

if __name__ == '__main__':
    # Initialize system
    setup_database()
    detect_hardware()
    
    # Start background thread
    background_thread = threading.Thread(target=background_update_thread, daemon=True)
    background_thread.start()
    
    # Log startup
    log_activity('system', 'startup', {
        'hardware': system_state['hardware'],
        'libraries': {
            'PCA9685': PCA9685_AVAILABLE,
            'MPU6050': MPU6050_AVAILABLE,
            'evdev': EVDEV_AVAILABLE
        }
    })
    
    # Start Flask app
    port = find_available_port()
    logger.info(f"Starting Integrated Robot Arm Controller on http://localhost:{port}")
    logger.info("Hardware Status:")
    logger.info(f"  PCA9685: {'Connected' if system_state['hardware']['pca9685']['connected'] else 'Not connected'}")
    logger.info(f"  MPU6050: {'Connected' if system_state['hardware']['mpu6050']['connected'] else 'Not connected'}")
    logger.info(f"  Controller: {'Connected' if system_state['hardware']['controller']['connected'] else 'Not connected'}")
    
    try:
        app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
    except KeyboardInterrupt:
        log_activity('system', 'shutdown', None)
        logger.info("Shutting down...")
    except Exception as e:
        log_activity('system', 'error', {'error': str(e)})
        logger.error(f"Server error: {e}")
