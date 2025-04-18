# Robot Arm Virtual UI v0.2.1-1
#!/bin/bash

# Determine the activation command based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Run the application
python robot_arm_app.py
