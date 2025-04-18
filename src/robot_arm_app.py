# Robot Arm Virtual UI v0.3.1-1

import os
import logging
import socket
from flask import Flask, render_template, jsonify, request

# Setup logging
logging.basicConfig(filename='robot_arm.log', level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Import development route
try:
    from dev_route import add_dev_route
    # Add development route
    add_dev_route(app)
    has_dev_route = True
except ImportError:
    has_dev_route = False
    logger.warning("Development route module not found. Dev page will not be available.")

# Robot arm state
arm_state = {
    'channel0': 135,  # Default to middle position (0-270 degrees)
    'channel1': 135,
    'channel2': 135,
    'channel3': 135
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/servo', methods=['GET'])
def get_servo_positions():
    return jsonify(arm_state)

@app.route('/api/servo', methods=['POST'])
def update_servo_positions():
    data = request.json
    for channel in range(4):
        key = f'channel{channel}'
        if key in data:
            # Ensure value is within 0-270 range
            arm_state[key] = max(0, min(270, data[key]))
            
    # Log the current position
    logger.info(f"Servo positions updated: {arm_state}")
    print(f"\rPositions: Ch0: {arm_state['channel0']}° | Ch1: {arm_state['channel1']}° | " +
          f"Ch2: {arm_state['channel2']}° | Ch3: {arm_state['channel3']}°", end='')
    
    return jsonify({"status": "success", "state": arm_state})

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port  # Default fallback

def get_ip():
    """Get local IP address for network access"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public address to determine the interface
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    # Find available port
    port = find_available_port()
    
    # Get network IP for display
    network_ip = get_ip()

    print(f"Starting Robot Arm Virtual UI v0.3.1-1 on http://localhost:{port}")
    print(f"Network access URL: http://{network_ip}:{port}")
    
    if has_dev_route:
        print(f"Development version: http://{network_ip}:{port}/dev")
    
    print("Press Ctrl+C to exit")
    print("Current servo positions will be displayed below:")
    
    # Use host='0.0.0.0' to allow connections from other devices on the network
    app.run(host='0.0.0.0', port=port, debug=False)
