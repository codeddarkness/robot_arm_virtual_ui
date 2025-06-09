#!/bin/bash

# Flask Compatibility Fix Script
# This script fixes the Flask/Werkzeug compatibility issue found in setup_debug.log

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Fixing Flask compatibility issues...${NC}"

# Check if we're in the right directory
if [ ! -f "robot_arm_app.py" ]; then
    echo -e "${RED}Error: robot_arm_app.py not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found. Please run setup.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Update requirements.txt with compatible versions
echo -e "${YELLOW}Updating requirements.txt with compatible versions...${NC}"
cat > requirements.txt << 'EOF'
Flask==2.3.3
Werkzeug==2.3.7
Jinja2>=3.0
itsdangerous>=2.0
click>=7.1.2
MarkupSafe>=2.1.1
EOF

echo -e "${GREEN}✓ Updated requirements.txt${NC}"

# Uninstall problematic packages
echo -e "${YELLOW}Uninstalling incompatible packages...${NC}"
pip uninstall -y Flask Werkzeug 2>/dev/null || true

# Install compatible versions
echo -e "${YELLOW}Installing compatible Flask and Werkzeug versions...${NC}"
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install compatible packages.${NC}"
    echo -e "${YELLOW}Trying alternative approach...${NC}"
    
    # Try installing specific versions directly
    pip install Flask==2.3.3 Werkzeug==2.3.7
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Alternative installation failed. Trying fallback...${NC}"
        
        # Fallback to even more compatible versions
        pip install Flask==2.2.5 Werkzeug==2.2.3
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ All installation attempts failed.${NC}"
            echo -e "${YELLOW}Manual fix required:${NC}"
            echo "1. Activate virtual environment: source venv/bin/activate"
            echo "2. Try: pip install 'Flask>=2.0,<3.0' 'Werkzeug>=2.0,<3.0'"
            exit 1
        fi
    fi
fi

echo -e "${GREEN}✓ Compatible packages installed${NC}"

# Update robot_arm_app.py to be more robust
echo -e "${YELLOW}Updating robot_arm_app.py for better compatibility...${NC}"

# Create backup
cp robot_arm_app.py robot_arm_app.py.bak

# Update the app with more robust error handling and compatibility
cat > robot_arm_app.py << 'EOF'
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
EOF

echo -e "${GREEN}✓ Updated robot_arm_app.py with better error handling${NC}"

# Test the installation
echo -e "${YELLOW}Testing Flask installation...${NC}"
python -c "
try:
    from flask import Flask
    print('✓ Flask import successful')
    app = Flask(__name__)
    print('✓ Flask app creation successful')
except Exception as e:
    print(f'✗ Flask test failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Flask compatibility test passed${NC}"
else
    echo -e "${RED}✗ Flask compatibility test failed${NC}"
    exit 1
fi

# Update run.sh with better error handling
echo -e "${YELLOW}Updating run.sh with better error handling...${NC}"
cat > run.sh << 'EOF'
#!/bin/bash

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Robot Arm Virtual UI...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found.${NC}"
    echo "Please run setup.sh first."
    exit 1
fi

# Determine the activation command based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Test Flask before running
echo "Testing Flask installation..."
python -c "from flask import Flask; print('Flask OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Flask is not properly installed.${NC}"
    echo "Please run the fix script: ./fix_flask_compatibility.sh"
    exit 1
fi

# Run the application
echo -e "${GREEN}✓ All checks passed. Starting application...${NC}"
python robot_arm_app.py
EOF

chmod +x run.sh
echo -e "${GREEN}✓ Updated run.sh${NC}"

# Create a test script
echo -e "${YELLOW}Creating test script...${NC}"
cat > test_app.sh << 'EOF'
#!/bin/bash

# Test script for robot arm app
echo "Testing Robot Arm Virtual UI..."

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Test imports
echo "Testing Python imports..."
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import flask
    print(f'✓ Flask version: {flask.__version__}')
except ImportError as e:
    print(f'✗ Flask import failed: {e}')
    sys.exit(1)

try:
    import werkzeug
    print(f'✓ Werkzeug version: {werkzeug.__version__}')
except ImportError as e:
    print(f'✗ Werkzeug import failed: {e}')
    sys.exit(1)

try:
    from flask import Flask, render_template, jsonify, request
    print('✓ All Flask components imported successfully')
except ImportError as e:
    print(f'✗ Flask component import failed: {e}')
    sys.exit(1)

print('✓ All tests passed!')
"

echo "Test completed."
EOF

chmod +x test_app.sh
echo -e "${GREEN}✓ Created test_app.sh${NC}"

echo ""
echo -e "${GREEN}Fix completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the fix: ./test_app.sh"
echo "2. Run the application: ./run.sh"
echo ""
echo "If issues persist, check the backup: robot_arm_app.py.bak"
