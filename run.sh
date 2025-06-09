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
