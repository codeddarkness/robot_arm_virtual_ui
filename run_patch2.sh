#!/bin/bash

# Fix Git merge conflict in robot_arm_app.py

echo "Fixing Git merge conflict in robot_arm_app.py..."

# Backup the current file
cp robot_arm_app.py robot_arm_app.py.backup

# Create a clean version of robot_arm_app.py
cat > robot_arm_app.py << 'EOF'
import os
import logging
import socket
from flask import Flask, render_template, jsonify, request

# Setup logging
logging.basicConfig(filename='robot_arm.log', level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

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

if __name__ == '__main__':
    # Find available port
    port = find_available_port()
    print(f"Starting robot arm server on http://localhost:{port}")
    print("Press Ctrl+C to exit")
    print("Current servo positions will be displayed below:")
    app.run(debug=True, port=port)
EOF

echo "Git merge conflict fixed in robot_arm_app.py"
echo "A backup was saved as robot_arm_app.py.backup"
echo ""
echo "Now you can run the application with:"
echo "  python3 robot_arm_app.py"
