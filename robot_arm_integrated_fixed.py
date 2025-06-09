#!/usr/bin/env python3
"""
Integrated Robot Arm Controller - Fixed Version
Improved hardware detection and error handling
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

# Try to import the improved hardware manager
try:
    from improved_hardware_manager import hardware_manager
    HARDWARE_MANAGER_AVAILABLE = True
except ImportError:
    print("Warning: improved_hardware_manager not found. Using fallback detection.")
    HARDWARE_MANAGER_AVAILABLE = False

# Fallback imports for basic functionality
try:
    import evdev
    from evdev import InputDevice, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

# Setup logging with better format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_robot_fixed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state with better structure
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
        'temp': 25.0,
        'direction': {'x': "neutral", 'y': "neutral", 'z': "neutral"}
    },
    'controller_state': {
        'hold_states': {0: False, 1: False, 2: False, 3: False},
        'lock_state': False,
        'speed': 1.0
    },
    'sync_enabled': True,
    'active_mode': 'dashboard',
    'last_hardware_check': 0,
    'hardware_check_interval': 30  # Check hardware every 30 seconds
}

# Database setup
DB_PATH = 'integrated_robot_fixed.db'

def setup_database():
    """Initialize SQLite database with error handling"""
    try:
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hardware_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                component TEXT,
                status TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        return False

def log_activity(mode, action, data=None):
    """Log system activity with error handling"""
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
        logger.error(f"Activity logging error: {e}")

def log_hardware_status(component, status, details=None):
    """Log hardware status changes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hardware_logs (timestamp, component, status, details) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), component, status, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Hardware logging error: {e}")

def detect_hardware():
    """Detect and initialize available hardware with improved error handling"""
    global system_state
    
    hardware_status = {
        'pca9685': {'connected': False, 'bus': None},
        'mpu6050': {'connected': False, 'bus': None}, 
        'controller': {'connected': False, 'type': None, 'path': None}
    }
    
    if HARDWARE_MANAGER_AVAILABLE:
        # Use improved hardware manager
        try:
            logger.info("Using improved hardware detection...")
            detected = hardware_manager.detect_all()
            
            # Convert to our format
            hardware_status['pca9685'] = {
                'connected': detected['pca9685']['connected'],
                'bus': detected['pca9685']['bus']
            }
            hardware_status['mpu6050'] = {
                'connected': detected['mpu6050']['connected'],
                'bus': detected['mpu6050']['bus']
            }
            hardware_status['controller'] = {
                'connected': detected['controller']['connected'],
                'type': detected['controller']['type'],
                'path': detected['controller']['path']
            }
            
            # Log hardware detection results
            for component, status in hardware_status.items():
                if status['connected']:
                    log_hardware_status(component, "connected", str(status))
                else:
                    log_hardware_status(component, "disconnected", "Not detected")
                    
        except Exception as e:
            logger.error(f"Hardware manager detection failed: {e}")
            hardware_status = fallback_hardware_detection()
    else:
        # Use fallback detection
        hardware_status = fallback_hardware_detection()
    
    system_state['hardware'] = hardware_status
    system_state['last_hardware_check'] = time.time()
    
    return hardware_status

def fallback_hardware_detection():
    """Fallback hardware detection method"""
    logger.info("Using fallback hardware detection...")
    
    hardware_status = {
        'pca9685': {'connected': False, 'bus': None},
        'mpu6050': {'connected': False, 'bus': None},
        'controller': {'connected': False, 'type': None, 'path': None}
    }
    
    # Try to detect PCA9685
    try:
        import Adafruit_PCA9685
        for bus_num in [0, 1]:
            try:
                pwm = Adafruit_PCA9685.PCA9685(busnum=bus_num)
                pwm.set_pwm_freq(50)
                hardware_status['pca9685'] = {'connected': True, 'bus': bus_num}
                logger.info(f"PCA9685 detected on I2C bus {bus_num}")
                break
            except Exception as e:
                logger.debug(f"PCA9685 not found on bus {bus_num}: {e}")
    except ImportError:
        logger.warning("Adafruit_PCA9685 library not available")
    
    # Try to detect MPU6050
    try:
        from mpu6050 import mpu6050
        for bus_num in [0, 1]:
            try:
                sensor = mpu6050(bus_num)
                sensor.get_temp()  # Test read
                hardware_status['mpu6050'] = {'connected': True, 'bus': bus_num}
                logger.info(f"MPU6050 detected on I2C bus {bus_num}")
                break
            except Exception as e:
                logger.debug(f"MPU6050 not found on bus {bus_num}: {e}")
    except ImportError:
        logger.warning("MPU6050 library not available")
    
    # Try to detect controllers
    if EVDEV_AVAILABLE:
        try:
            devices = [InputDevice(path) for path in evdev.list_devices()]
            for device in devices:
                name_lower = device.name.lower()
                if any(keyword in name_lower for keyword in ['xbox', 'playstation', 'ps3', 'controller']):
                    controller_type = 'PS3' if 'ps' in name_lower else 'Xbox'
                    hardware_status['controller'] = {
                        'connected': True,
                        'type': controller_type,
                        'path': device.path
                    }
                    logger.info(f"{controller_type} controller detected: {device.name}")
                    break
        except Exception as e:
            logger.error(f"Controller detection error: {e}")
    
    return hardware_status

def update_mpu_data():
    """Update MPU6050 sensor data with improved error handling"""
    global system_state
    
    if HARDWARE_MANAGER_AVAILABLE and system_state['hardware']['mpu6050']['connected']:
        try:
            data = hardware_manager.read_mpu6050()
            if data:
                # Update system state
                system_state['mpu_data']['accel'] = data['accel']
                system_state['mpu_data']['gyro'] = data['gyro']
                system_state['mpu_data']['temp'] = data['temp']
                
                # Calculate directions
                threshold = 0.5
                system_state['mpu_data']['direction'] = {
                    'x': "right" if data['accel']['x'] > threshold else "left" if data['accel']['x'] < -threshold else "neutral",
                    'y': "up" if data['accel']['y'] > threshold else "down" if data['accel']['y'] < -threshold else "neutral",
                    'z': "up" if data['accel']['z'] > 9.8 + threshold else "down" if data['accel']['z'] < 9.8 - threshold else "neutral"
                }
                return
        except Exception as e:
            logger.error(f"MPU6050 read error: {e}")
            # Fall through to simulation
    
    # Simulation mode with more realistic data
    t = time.time()
    system_state['mpu_data'] = {
        'accel': {
            'x': math.sin(t * 0.5) * 0.3 + (math.random() - 0.5) * 0.1,
            'y': math.cos(t * 0.7) * 0.3 + (math.random() - 0.5) * 0.1,
            'z': 9.8 + math.sin(t * 0.3) * 0.2 + (math.random() - 0.5) * 0.1
        },
        'gyro': {
            'x': math.sin(t * 0.2) * 1.5 + (math.random() - 0.5) * 0.5,
            'y': math.cos(t * 0.4) * 1.5 + (math.random() - 0.5) * 0.5,
            'z': math.sin(t * 0.6) * 1.5 + (math.random() - 0.5) * 0.5
        },
        'temp': 25 + math.sin(t * 0.1) * 2 + (math.random() - 0.5),
        'direction': {
            'x': "neutral", 'y': "neutral", 'z': "neutral"
        }
    }

def sync_servo_positions():
    """Synchronize virtual and physical servo positions with error handling"""
    if not system_state['sync_enabled']:
        return
        
    if not system_state['hardware']['pca9685']['connected']:
        return
    
    try:
        if HARDWARE_MANAGER_AVAILABLE:
            # Use hardware manager's PCA9685 instance
            pwm_instance = hardware_manager.hardware_state['pca9685']['instance']
        else:
            # Fallback: try to create PCA9685 instance
            import Adafruit_PCA9685
            bus = system_state['hardware']['pca9685']['bus']
            pwm_instance = Adafruit_PCA9685.PCA9685(busnum=bus)
        
        if pwm_instance:
            for channel in range(4):
                # Convert virtual angle (0-270) to physical PWM (150-600)
                virtual_angle = system_state['virtual_arm'][f'channel{channel}']
                physical_angle = int((virtual_angle / 270) * 180)
                system_state['physical_servos'][channel] = physical_angle
                
                # Set PWM
                pwm_value = int(150 + (physical_angle / 180.0) * 450)
                pwm_instance.set_pwm(channel, 0, pwm_value)
                
    except Exception as e:
        logger.error(f"Servo sync error: {e}")

def periodic_hardware_check():
    """Periodically check hardware status"""
    current_time = time.time()
    if current_time - system_state['last_hardware_check'] > system_state['hardware_check_interval']:
        logger.info("Performing periodic hardware check...")
        try:
            old_status = system_state['hardware'].copy()
            new_status = detect_hardware()
            
            # Check for changes
            for component in ['pca9685', 'mpu6050', 'controller']:
                old_conn = old_status[component]['connected']
                new_conn = new_status[component]['connected']
                
                if old_conn != new_conn:
                    status = "connected" if new_conn else "disconnected"
                    logger.info(f"{component} status changed: {status}")
                    log_hardware_status(component, status, f"Auto-detected change")
                    
        except Exception as e:
            logger.error(f"Periodic hardware check error: {e}")

def background_update_thread():
    """Background thread for updating sensors and synchronization"""
    while True:
        try:
            # Update MPU data
            update_mpu_data()
            
            # Sync servos if enabled
            if system_state['sync_enabled']:
                sync_servo_positions()
            
            # Periodic hardware check
            periodic_hardware_check()
            
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Background update error: {e}")
            time.sleep(1)

# Flask Routes (keeping existing structure but with improved error handling)

@app.route('/')
def dashboard():
    """Main dashboard with error handling"""
    try:
        system_state['active_mode'] = 'dashboard'
        return render_template('dashboard.html', state=system_state)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"Dashboard error: {e}", 500

@app.route('/virtual')
def virtual_interface():
    """Virtual robot arm interface"""
    try:
        system_state['active_mode'] = 'virtual'
        return render_template('virtual_arm.html', state=system_state)
    except Exception as e:
        logger.error(f"Virtual interface error: {e}")
        return f"Virtual interface error: {e}", 500

@app.route('/physical')
def physical_interface():
    """Physical hardware interface"""
    try:
        system_state['active_mode'] = 'physical'
        return render_template('physical_control.html', state=system_state)
    except Exception as e:
        logger.error(f"Physical interface error: {e}")
        return f"Physical interface error: {e}", 500

@app.route('/controller')
def controller_interface():
    """Game controller interface"""
    try:
        system_state['active_mode'] = 'controller'
        return render_template('controller_monitor.html', state=system_state)
    except Exception as e:
        logger.error(f"Controller interface error: {e}")
        return f"Controller interface error: {e}", 500

@app.route('/mpu')
def mpu_interface():
    """MPU6050 sensor interface"""
    try:
        system_state['active_mode'] = 'mpu'
        return render_template('mpu_monitor.html', state=system_state)
    except Exception as e:
        logger.error(f"MPU interface error: {e}")
        return f"MPU interface error: {e}", 500

# API Routes with better error handling

@app.route('/api/status')
def api_status():
    """Get complete system status with error handling"""
    try:
        # Ensure we have fresh hardware status
        if time.time() - system_state['last_hardware_check'] > 5:
            detect_hardware()
            
        return jsonify(system_state)
    except Exception as e:
        logger.error(f"API status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/virtual/servo', methods=['GET', 'POST'])
def api_virtual_servo():
    """Virtual servo control API with validation"""
    try:
        if request.method == 'GET':
            return jsonify(system_state['virtual_arm'])
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate and update virtual servo positions
        for channel in range(4):
            key = f'channel{channel}'
            if key in data:
                try:
                    value = max(0, min(270, int(data[key])))
                    system_state['virtual_arm'][key] = value
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid value for {key}"}), 400
        
        log_activity('virtual', 'servo_update', system_state['virtual_arm'])
        return jsonify({"status": "success", "state": system_state['virtual_arm']})
        
    except Exception as e:
        logger.error(f"Virtual servo API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/physical/servo/<int:channel>/<int:angle>', methods=['POST'])
def api_physical_servo(channel, angle):
    """Physical servo control API with validation"""
    try:
        # Validate inputs
        if not (0 <= channel <= 3):
            return jsonify({"error": "Invalid channel (must be 0-3)"}), 400
        if not (0 <= angle <= 180):
            return jsonify({"error": "Invalid angle (must be 0-180)"}), 400
        
        # Update state
        system_state['physical_servos'][channel] = angle
        
        # Try to control physical servo
        if system_state['hardware']['pca9685']['connected']:
            try:
                if HARDWARE_MANAGER_AVAILABLE:
                    pwm_instance = hardware_manager.hardware_state['pca9685']['instance']
                else:
                    import Adafruit_PCA9685
                    bus = system_state['hardware']['pca9685']['bus']
                    pwm_instance = Adafruit_PCA9685.PCA9685(busnum=bus)
                
                pwm_value = int(150 + (angle / 180.0) * 450)
                pwm_instance.set_pwm(channel, 0, pwm_value)
                
                log_activity('physical', 'servo_move', {'channel': channel, 'angle': angle})
                return jsonify({"success": True, "channel": channel, "angle": angle})
                
            except Exception as e:
                logger.error(f"Physical servo control error: {e}")
                return jsonify({"error": f"Hardware error: {e}"}), 500
        else:
            # Simulation mode
            log_activity('physical', 'servo_move_sim', {'channel': channel, 'angle': angle})
            return jsonify({"success": True, "channel": channel, "angle": angle, "mode": "simulation"})
            
    except Exception as e:
        logger.error(f"Physical servo API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def api_sync_toggle():
    """Toggle synchronization with error handling"""
    try:
        system_state['sync_enabled'] = not system_state['sync_enabled']
        log_activity('system', 'sync_toggle', {'enabled': system_state['sync_enabled']})
        return jsonify({"sync_enabled": system_state['sync_enabled']})
    except Exception as e:
        logger.error(f"Sync toggle error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/hardware/refresh', methods=['POST'])
def api_hardware_refresh():
    """Manually refresh hardware detection"""
    try:
        old_status = system_state['hardware'].copy()
        new_status = detect_hardware()
        
        changes = []
        for component in ['pca9685', 'mpu6050', 'controller']:
            if old_status[component]['connected'] != new_status[component]['connected']:
                changes.append({
                    'component': component,
                    'old_status': old_status[component]['connected'],
                    'new_status': new_status[component]['connected']
                })
        
        log_activity('system', 'hardware_refresh', {'changes': changes})
        return jsonify({
            "success": True,
            "hardware": new_status,
            "changes": changes
        })
        
    except Exception as e:
        logger.error(f"Hardware refresh error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Get activity logs with pagination"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM activity_logs ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
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
        logger.error(f"Logs API error: {e}")
        return jsonify({"error": str(e)}), 500

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port with better error handling"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        except Exception:
            continue
    return start_port

if __name__ == '__main__':
    # Initialize system
    logger.info("Starting Integrated Robot Arm Controller (Fixed Version)")
    
    # Setup database
    if not setup_database():
        logger.error("Database setup failed, exiting")
        sys.exit(1)
    
    # Detect hardware
    logger.info("Detecting hardware...")
    hardware_status = detect_hardware()
    
    # Log startup
    log_activity('system', 'startup', {
        'hardware': hardware_status,
        'libraries': {
            'hardware_manager': HARDWARE_MANAGER_AVAILABLE,
            'evdev': EVDEV_AVAILABLE
        }
    })
    
    # Start background thread
    background_thread = threading.Thread(target=background_update_thread, daemon=True)
    background_thread.start()
    logger.info("Background update thread started")
    
    # Start Flask app
    port = find_available_port()
    logger.info(f"Starting server on http://localhost:{port}")
    logger.info("Hardware Status Summary:")
    logger.info(f"  PCA9685: {'✓ Connected' if hardware_status['pca9685']['connected'] else '✗ Simulation mode'}")
    logger.info(f"  MPU6050: {'✓ Connected' if hardware_status['mpu6050']['connected'] else '✗ Simulation mode'}")
    logger.info(f"  Controller: {'✓ Connected' if hardware_status['controller']['connected'] else '✗ Not detected'}")
    
    try:
        app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
    except KeyboardInterrupt:
        log_activity('system', 'shutdown', {'reason': 'user_interrupt'})
        logger.info("Shutting down gracefully...")
    except Exception as e:
        log_activity('system', 'error', {'error': str(e)})
        logger.error(f"Server error: {e}")
