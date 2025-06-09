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
