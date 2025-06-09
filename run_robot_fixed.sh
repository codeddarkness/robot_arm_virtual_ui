#!/bin/bash

# Robust Robot Arm Startup Script
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Robot Arm Controller (Fixed Version)${NC}"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    exit 1
fi

# Check for required files
if [ -f "robot_arm_integrated_fixed.py" ]; then
    echo "Using fixed version..."
    python3 robot_arm_integrated_fixed.py
elif [ -f "robot_arm_integrated.py" ]; then
    echo "Using original integrated file..."
    python3 robot_arm_integrated.py
else
    echo -e "${RED}✗ No robot arm application found${NC}"
    exit 1
fi
