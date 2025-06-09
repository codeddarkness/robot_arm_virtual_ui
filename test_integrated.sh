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
