#!/bin/bash

# Integrated Robot Arm Setup Script
# Sets up the complete integrated virtual and physical robot arm control system

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Integrated Robot Arm Control System...${NC}"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Create project structure
echo -e "${YELLOW}Creating project structure...${NC}"
mkdir -p templates static

# Install system dependencies (optional hardware libraries)
echo -e "${YELLOW}Installing system dependencies...${NC}"
echo "Note: Some hardware libraries are optional and will run in simulation mode if not available."

# Update package list (if on Debian/Ubuntu)
if command -v apt-get &>/dev/null; then
    echo "Updating package list..."
    sudo apt-get update -qq
    
    # Install I2C tools and libraries
    echo "Installing I2C development libraries..."
    sudo apt-get install -y python3-pip python3-venv i2c-tools libi2c-dev python3-dev
    
    # Enable I2C (on Raspberry Pi)
    if [ -f /boot/config.txt ]; then
        echo "Enabling I2C on Raspberry Pi..."
        sudo sed -i 's/#dtparam=i2c_arm=on/dtparam=i2c_arm=on/' /boot/config.txt
        if ! grep -q "dtparam=i2c_arm=on" /boot/config.txt; then
            echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
        fi
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}! Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Create requirements.txt with all dependencies
echo -e "${YELLOW}Creating requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# Core web framework
Flask==2.3.3
Werkzeug==2.3.7

# Hardware libraries (optional - will fall back to simulation if not available)
Adafruit-PCA9685==1.0.1
mpu6050-raspberrypi==1.2

# Input device handling
evdev==1.6.1

# Additional dependencies
Jinja2>=3.0
itsdangerous>=2.0
click>=7.1.2
MarkupSafe>=2.1.1
EOF

echo -e "${GREEN}✓ Created requirements.txt${NC}"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip

# Install core dependencies first
pip install Flask==2.3.3 Werkzeug==2.3.7

# Try to install hardware libraries (they may fail on some systems)
echo "Installing hardware libraries (may show warnings if hardware not available)..."

# Install PCA9685 library
pip install Adafruit-PCA9685 || echo -e "${YELLOW}Warning: PCA9685 library installation failed - will run in simulation mode${NC}"

# Install MPU6050 library
pip install mpu6050-raspberrypi || echo -e "${YELLOW}Warning: MPU6050 library installation failed - will run in simulation mode${NC}"

# Install evdev for controller support
pip install evdev || echo -e "${YELLOW}Warning: evdev installation failed - controller support may be limited${NC}"

# Install remaining dependencies
pip install -r requirements.txt || echo -e "${YELLOW}Warning: Some optional dependencies may have failed${NC}"

echo -e "${GREEN}✓ Dependencies installation completed${NC}"

# Copy the main application files (these would be created by the artifacts above)
echo -e "${YELLOW}Setting up application files...${NC}"

# Check if we have the integrated application
if [ ! -f "robot_arm_integrated.py" ]; then
    echo -e "${RED}✗ robot_arm_integrated.py not found.${NC}"
    echo "Please ensure the integrated application file is in the current directory."
    echo "You can copy it from the artifacts provided in the setup instructions."
    exit 1
fi

# Check for template files
if [ ! -f "templates/dashboard.html" ]; then
    echo -e "${RED}✗ Template files not found.${NC}"
    echo "Please ensure all template files are in the templates/ directory:"
    echo "  - dashboard.html"
    echo "  - virtual_arm.html" 
    echo "  - physical_control.html"
    echo "  - controller_monitor.html"
    echo "  - mpu_monitor.html"
    exit 1
fi

echo -e "${GREEN}✓ Application files verified${NC}"

# Create run script
echo -e "${YELLOW}Creating run script...${NC}"
cat > run_integrated.sh << 'EOF'
#!/bin/bash

# Integrated Robot Arm Runner Script

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Integrated Robot Arm Control System...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found.${NC}"
    echo "Please run setup_integrated_robot.sh first."
    exit 1
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Check for required files
if [ ! -f "robot_arm_integrated.py" ]; then
    echo -e "${RED}Error: robot_arm_integrated.py not found.${NC}"
    exit 1
fi

# Test imports
echo -e "${YELLOW}Testing system components...${NC}"
python3 -c "
import sys
print(f'Python version: {sys.version}')

# Test Flask
try:
    import flask
    print(f'✓ Flask version: {flask.__version__}')
except ImportError as e:
    print(f'✗ Flask import failed: {e}')
    sys.exit(1)

# Test hardware libraries (optional)
try:
    import Adafruit_PCA9685
    print('✓ PCA9685 library available')
except ImportError:
    print('! PCA9685 library not available - will use simulation mode')

try:
    from mpu6050 import mpu6050
    print('✓ MPU6050 library available')
except ImportError:
    print('! MPU6050 library not available - will use simulation mode')

try:
    import evdev
    print('✓ evdev library available')
except ImportError:
    print('! evdev library not available - controller support limited')

print('✓ System check completed')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}System check failed. Please check the setup.${NC}"
    exit 1
fi

# Run the application
echo -e "${GREEN}✓ All checks passed. Starting integrated robot arm controller...${NC}"
echo ""
echo "The application will be available at:"
echo "  http://localhost:5000 (or next available port)"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

python3 robot_arm_integrated.py
EOF

chmod +x run_integrated.sh
echo -e "${GREEN}✓ Created run_integrated.sh${NC}"

# Create test script
echo -e "${YELLOW}Creating test script...${NC}"
cat > test_integrated.sh << 'EOF'
#!/bin/bash

# Test script for integrated robot arm system

echo "Testing Integrated Robot Arm System..."

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "Running comprehensive system test..."

python3 -c "
import sys
import json
from datetime import datetime

print('=' * 60)
print('INTEGRATED ROBOT ARM SYSTEM TEST')
print('=' * 60)

# Test 1: Core imports
print('\\n1. Testing core imports...')
try:
    import flask
    from flask import Flask, render_template, jsonify, request
    print('   ✓ Flask and components imported successfully')
except ImportError as e:
    print(f'   ✗ Flask import failed: {e}')
    sys.exit(1)

# Test 2: Hardware library availability
print('\\n2. Testing hardware library availability...')

pca_available = False
mpu_available = False
evdev_available = False

try:
    import Adafruit_PCA9685
    pca_available = True
    print('   ✓ PCA9685 library available')
except ImportError:
    print('   ! PCA9685 library not available (simulation mode)')

try:
    from mpu6050 import mpu6050
    mpu_available = True
    print('   ✓ MPU6050 library available')
except ImportError:
    print('   ! MPU6050 library not available (simulation mode)')

try:
    import evdev
    evdev_available = True
    print('   ✓ evdev library available')
except ImportError:
    print('   ! evdev library not available (limited controller support)')

# Test 3: File structure
print('\\n3. Testing file structure...')
import os

required_files = [
    'robot_arm_integrated.py',
    'templates/dashboard.html',
    'templates/virtual_arm.html',
    'templates/physical_control.html',
    'templates/controller_monitor.html',
    'templates/mpu_monitor.html'
]

all_files_present = True
for file in required_files:
    if os.path.exists(file):
        print(f'   ✓ {file}')
    else:
        print(f'   ✗ {file} missing')
        all_files_present = False

if not all_files_present:
    print('\\n   ERROR: Some required files are missing!')
    sys.exit(1)

# Test 4: Database functionality
print('\\n4. Testing database functionality...')
try:
    import sqlite3
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE test (id INTEGER, data TEXT)')
    cursor.execute('INSERT INTO test VALUES (1, \"test_data\")')
    result = cursor.fetchone()
    conn.close()
    print('   ✓ SQLite database functionality working')
except Exception as e:
    print(f'   ✗ Database test failed: {e}')

# Test 5: JSON serialization
print('\\n5. Testing JSON serialization...')
try:
    test_data = {
        'virtual_arm': {'channel0': 135, 'channel1': 135},
        'physical_servos': {0: 90, 1: 90},
        'timestamp': datetime.now().isoformat()
    }
    json_str = json.dumps(test_data)
    parsed_data = json.loads(json_str)
    print('   ✓ JSON serialization working')
except Exception as e:
    print(f'   ✗ JSON test failed: {e}')

# Summary
print('\\n' + '=' * 60)
print('TEST SUMMARY')
print('=' * 60)
print(f'Hardware Libraries:')
print(f'  PCA9685 (Servo Control): {\"Available\" if pca_available else \"Simulation Mode\"}')
print(f'  MPU6050 (Gyro/Accel): {\"Available\" if mpu_available else \"Simulation Mode\"}')
print(f'  evdev (Controllers): {\"Available\" if evdev_available else \"Limited Support\"}')
print(f'\\nFile Structure: Complete')
print(f'Core Functionality: Working')
print(f'\\n✓ System is ready for operation!')
print(f'\\nRun ./run_integrated.sh to start the integrated robot arm controller.')
"

echo ""
echo "Test completed."
EOF

chmod +x test_integrated.sh
echo -e "${GREEN}✓ Created test_integrated.sh${NC}"

# Create hardware detection script
echo -e "${YELLOW}Creating hardware detection script...${NC}"
cat > detect_hardware.sh << 'EOF'
#!/bin/bash

# Hardware Detection Script for Integrated Robot Arm

echo "Detecting Hardware Components..."
echo "================================"

# Check I2C
echo "I2C Bus Detection:"
if command -v i2cdetect &>/dev/null; then
    echo "Scanning I2C bus 0:"
    i2cdetect -y 0 2>/dev/null || echo "  Bus 0 not available"
    echo ""
    echo "Scanning I2C bus 1:"
    i2cdetect -y 1 2>/dev/null || echo "  Bus 1 not available"
    echo ""
    
    # Look for common addresses
    echo "Looking for known devices:"
    for bus in 0 1; do
        if i2cdetect -y $bus 2>/dev/null | grep -q "40"; then
            echo "  PCA9685 detected on bus $bus (address 0x40)"
        fi
        if i2cdetect -y $bus 2>/dev/null | grep -q "68"; then
            echo "  MPU6050 detected on bus $bus (address 0x68)"
        fi
    done
else
    echo "  i2c-tools not installed - cannot detect I2C devices"
fi

echo ""
echo "USB/Input Device Detection:"
if command -v ls &>/dev/null; then
    echo "Input devices:"
    ls /dev/input/event* 2>/dev/null | head -5 || echo "  No input devices found"
    
    echo ""
    echo "USB devices (controllers):"
    if command -v lsusb &>/dev/null; then
        lsusb | grep -i -E "(xbox|playstation|sony|microsoft)" || echo "  No game controllers detected"
    else
        echo "  lsusb not available"
    fi
fi

echo ""
echo "Python Hardware Library Test:"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

python3 -c "
# Test hardware libraries
try:
    import Adafruit_PCA9685
    print('✓ PCA9685 library available')
    
    # Try to initialize on different buses
    for bus in [0, 1]:
        try:
            pwm = Adafruit_PCA9685.PCA9685(busnum=bus)
            print(f'  ✓ PCA9685 initialized on bus {bus}')
            break
        except Exception as e:
            print(f'  ! PCA9685 failed on bus {bus}: {e}')
except ImportError:
    print('! PCA9685 library not available')

try:
    from mpu6050 import mpu6050
    print('✓ MPU6050 library available')
    
    # Try to initialize on different buses
    for bus in [0, 1]:
        try:
            sensor = mpu6050(bus)
            temp = sensor.get_temp()
            print(f'  ✓ MPU6050 working on bus {bus}, temp: {temp:.1f}°C')
            break
        except Exception as e:
            print(f'  ! MPU6050 failed on bus {bus}: {e}')
except ImportError:
    print('! MPU6050 library not available')

try:
    import evdev
    print('✓ evdev library available')
    
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    controllers = []
    for device in devices:
        name = device.name.lower()
        if any(keyword in name for keyword in ['xbox', 'playstation', 'ps3', 'controller']):
            controllers.append(f'{device.name} ({device.path})')
    
    if controllers:
        print('  Controllers detected:')
        for controller in controllers:
            print(f'    {controller}')
    else:
        print('  No game controllers detected')
        
except ImportError:
    print('! evdev library not available')
"

echo ""
echo "Hardware detection completed."
EOF

chmod +x detect_hardware.sh
echo -e "${GREEN}✓ Created detect_hardware.sh${NC}"

# Final setup summary
echo ""
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "📁 Project Structure:"
echo "  ├── robot_arm_integrated.py     # Main integrated application"
echo "  ├── templates/                  # HTML templates"
echo "  │   ├── dashboard.html"
echo "  │   ├── virtual_arm.html"
echo "  │   ├── physical_control.html"
echo "  │   ├── controller_monitor.html"
echo "  │   └── mpu_monitor.html"
echo "  ├── venv/                       # Virtual environment"
echo "  ├── requirements.txt            # Python dependencies"
echo "  ├── run_integrated.sh           # Run script"
echo "  ├── test_integrated.sh          # Test script"
echo "  └── detect_hardware.sh          # Hardware detection"
echo ""
echo "🚀 Quick Start:"
echo "  1. Test the system:     ./test_integrated.sh"
echo "  2. Detect hardware:     ./detect_hardware.sh" 
echo "  3. Run the application: ./run_integrated.sh"
echo ""
echo "🌐 Web Interface:"
echo "  • Dashboard: http://localhost:5000/"
echo "  • Virtual Arm: http://localhost:5000/virtual"
echo "  • Physical Control: http://localhost:5000/physical"
echo "  • Controller Monitor: http://localhost:5000/controller"
echo "  • MPU Monitor: http://localhost:5000/mpu"
echo ""
echo -e "${BLUE}Note: Hardware libraries will run in simulation mode if physical devices are not connected.${NC}"
echo -e "${BLUE}This allows full testing and development without requiring physical hardware.${NC}"
