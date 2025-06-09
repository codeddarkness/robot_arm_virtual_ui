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
