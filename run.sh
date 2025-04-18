#!/bin/bash

# Robot Arm Virtual UI v0.2.1-1
# Main run script

# Determine the activation command based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Run the application from the src directory
cd src
python robot_arm_app.py
