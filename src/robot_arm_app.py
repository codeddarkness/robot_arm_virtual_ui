import os
import logging
import socket
try:
    from flask import Flask, render_template, jsonify, request
except ImportError as e:
    print(f"Flask import error: {e}")
    print("Please check Flask installation: pip install Flask")
    exit(1)

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
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return f"Error: {e}", 500

@app.route('/api/servo', methods=['GET'])
def get_servo_positions():
    return jsonify(arm_state)

@app.route('/api/servo', methods=['POST'])
def update_servo_positions():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        for channel in range(4):
            key = f'channel{channel}'
            if key in data:
                # Ensure value is within 0-270 range
                value = data[key]
                if isinstance(value, (int, float)):
                    arm_state[key] = max(0, min(270, int(value)))
                
        # Log the current position
        logger.info(f"Servo positions updated: {arm_state}")
        print(f"\rPositions: Ch0: {arm_state['channel0']}° | Ch1: {arm_state['channel1']}° | " +
              f"Ch2: {arm_state['channel2']}° | Ch3: {arm_state['channel3']}°", end='')
        
        return jsonify({"status": "success", "state": arm_state})
    except Exception as e:
        logger.error(f"Error updating servo positions: {e}")
        return jsonify({"error": str(e)}), 500

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        except Exception:
            continue
    return start_port  # Default fallback

if __name__ == '__main__':
    try:
        # Find available port
        port = find_available_port()
        print(f"Starting robot arm server on http://localhost:{port}")
        print("Press Ctrl+C to exit")
        print("Current servo positions will be displayed below:")
        
        # Run with more compatible settings
        app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        logger.error(f"Server startup error: {e}")
        exit(1)
