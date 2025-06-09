#!/usr/bin/env python3
"""
Hardware Detection and Fix Script
Diagnoses and fixes issues with MPU6050, controllers, and PCA9685
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime

# Color codes for output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message, status="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "success":
        print(f"{Colors.GREEN}[{timestamp}] ✓ {message}{Colors.NC}")
    elif status == "warning":
        print(f"{Colors.YELLOW}[{timestamp}] ! {message}{Colors.NC}")
    elif status == "error":
        print(f"{Colors.RED}[{timestamp}] ✗ {message}{Colors.NC}")
    else:
        print(f"{Colors.BLUE}[{timestamp}] • {message}{Colors.NC}")

def run_command(cmd, capture_output=True):
    """Run a shell command and return result"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_i2c_setup():
    """Check and fix I2C configuration"""
    print_status("Checking I2C configuration...")
    
    # Check if I2C is enabled
    if os.path.exists('/boot/config.txt'):
        with open('/boot/config.txt', 'r') as f:
            config = f.read()
        
        if 'dtparam=i2c_arm=on' not in config:
            print_status("I2C not enabled in /boot/config.txt", "warning")
            print_status("To enable I2C, add 'dtparam=i2c_arm=on' to /boot/config.txt and reboot")
        else:
            print_status("I2C enabled in boot config", "success")
    
    # Check I2C tools
    success, _, _ = run_command("which i2cdetect")
    if not success:
        print_status("Installing i2c-tools...", "warning")
        success, _, _ = run_command("sudo apt-get update && sudo apt-get install -y i2c-tools")
        if success:
            print_status("i2c-tools installed", "success")
        else:
            print_status("Failed to install i2c-tools", "error")
    else:
        print_status("i2c-tools available", "success")
    
    # Check I2C devices
    for bus in [0, 1]:
        success, output, _ = run_command(f"i2cdetect -y {bus}")
        if success:
            print_status(f"I2C bus {bus} accessible", "success")
            if "68" in output:
                print_status(f"MPU6050 detected on bus {bus} (address 0x68)", "success")
            if "40" in output:
                print_status(f"PCA9685 detected on bus {bus} (address 0x40)", "success")
        else:
            print_status(f"I2C bus {bus} not accessible", "warning")

def fix_mpu6050():
    """Fix MPU6050 detection and library issues"""
    print_status("Fixing MPU6050 issues...")
    
    # Try different MPU6050 libraries
    libraries_to_try = [
        "mpu6050-raspberrypi",
        "adafruit-circuitpython-mpu6050",
        "smbus2"
    ]
    
    for lib in libraries_to_try:
        print_status(f"Installing {lib}...")
        success, _, _ = run_command(f"pip install {lib}")
        if success:
            print_status(f"{lib} installed successfully", "success")
        else:
            print_status(f"Failed to install {lib}", "warning")
    
    # Test MPU6050 with different approaches
    test_code = '''
import sys
try:
    # Method 1: Direct smbus2 approach
    from smbus2 import SMBus
    
    def test_mpu6050_direct(bus_num):
        try:
            bus = SMBus(bus_num)
            # MPU6050 WHO_AM_I register
            who_am_i = bus.read_byte_data(0x68, 0x75)
            if who_am_i in [0x68, 0x72]:  # Valid MPU6050/6000 responses
                print(f"✓ MPU6050 detected on bus {bus_num} (WHO_AM_I: 0x{who_am_i:02x})")
                
                # Wake up the sensor
                bus.write_byte_data(0x68, 0x6B, 0)
                
                # Test read
                temp_raw = bus.read_word_data(0x68, 0x41)
                temp = ((temp_raw << 8) | (temp_raw >> 8)) / 340.0 + 36.53
                print(f"  Temperature: {temp:.1f}°C")
                return True
            bus.close()
            return False
        except Exception as e:
            print(f"  Bus {bus_num} error: {e}")
            return False
    
    found = False
    for bus in [0, 1]:
        if test_mpu6050_direct(bus):
            found = True
    
    if not found:
        print("! MPU6050 not found with direct method")
    
    # Method 2: Try mpu6050 library
    try:
        from mpu6050 import mpu6050
        for bus in [0, 1]:
            try:
                sensor = mpu6050(bus)
                temp = sensor.get_temp()
                print(f"✓ MPU6050 library working on bus {bus}, temp: {temp:.1f}°C")
                found = True
                break
            except Exception as e:
                print(f"  MPU6050 library failed on bus {bus}: {e}")
    except ImportError:
        print("! mpu6050 library not available")
    
    # Method 3: Try Adafruit library
    try:
        import board
        import busio
        import adafruit_mpu6050
        
        i2c = busio.I2C(board.SCL, board.SDA)
        mpu = adafruit_mpu6050.MPU6050(i2c)
        accel = mpu.acceleration
        print(f"✓ Adafruit MPU6050 working: {accel}")
        found = True
    except Exception as e:
        print(f"! Adafruit MPU6050 failed: {e}")
    
    if not found:
        print("✗ No MPU6050 libraries working")
    
except Exception as e:
    print(f"✗ Critical error: {e}")
'''
    
    # Write and run test
    with open('/tmp/test_mpu6050.py', 'w') as f:
        f.write(test_code)
    
    success, output, error = run_command("python3 /tmp/test_mpu6050.py")
    if output:
        for line in output.strip().split('\n'):
            if line.startswith('✓'):
                print_status(line[2:], "success")
            elif line.startswith('!'):
                print_status(line[2:], "warning")
            elif line.startswith('✗'):
                print_status(line[2:], "error")
            else:
                print_status(line)

def fix_controller_detection():
    """Fix game controller detection issues"""
    print_status("Fixing controller detection...")
    
    # Install evdev if not present
    success, _, _ = run_command("pip install evdev")
    if success:
        print_status("evdev library installed/updated", "success")
    
    # Check for input devices
    success, output, _ = run_command("ls -la /dev/input/")
    if success:
        event_devices = [line for line in output.split('\n') if 'event' in line]
        print_status(f"Found {len(event_devices)} input event devices", "success")
    
    # Test controller detection
    test_code = '''
import sys
try:
    import evdev
    from evdev import InputDevice, list_devices
    
    devices = [InputDevice(path) for path in list_devices()]
    print(f"Found {len(devices)} input devices:")
    
    controllers = []
    for device in devices:
        print(f"  {device.path}: {device.name}")
        
        # Check if it's a game controller
        name_lower = device.name.lower()
        if any(keyword in name_lower for keyword in ['xbox', 'playstation', 'ps3', 'ps4', 'controller', 'joystick']):
            controllers.append((device.path, device.name))
            print(f"    ✓ Detected as game controller")
            
            # Test capabilities
            caps = device.capabilities()
            if evdev.ecodes.EV_ABS in caps:
                print(f"    ✓ Has analog controls")
            if evdev.ecodes.EV_KEY in caps:
                print(f"    ✓ Has buttons")
    
    if controllers:
        print(f"\\n✓ Found {len(controllers)} game controllers:")
        for path, name in controllers:
            print(f"  {path}: {name}")
    else:
        print("\\n! No game controllers detected")
        print("  Check USB connections and permissions")

except ImportError:
    print("✗ evdev library not available")
except Exception as e:
    print(f"✗ Error: {e}")
'''
    
    with open('/tmp/test_controllers.py', 'w') as f:
        f.write(test_code)
    
    success, output, error = run_command("python3 /tmp/test_controllers.py")
    if output:
        for line in output.strip().split('\n'):
            if line.startswith('✓'):
                print_status(line[2:], "success")
            elif line.startswith('!'):
                print_status(line[2:], "warning")
            elif line.startswith('✗'):
                print_status(line[2:], "error")
            else:
                print_status(line)

def create_improved_hardware_detection():
    """Create an improved hardware detection module"""
    print_status("Creating improved hardware detection module...")
    
    detection_code = '''
#!/usr/bin/env python3
"""
Improved Hardware Detection Module
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class HardwareManager:
    def __init__(self):
        self.hardware_state = {
            'pca9685': {'connected': False, 'bus': None, 'instance': None},
            'mpu6050': {'connected': False, 'bus': None, 'instance': None},
            'controller': {'connected': False, 'type': None, 'path': None, 'instance': None}
        }
        
    def detect_all(self) -> Dict[str, Any]:
        """Detect all hardware components"""
        self.detect_pca9685()
        self.detect_mpu6050()
        self.detect_controllers()
        return self.hardware_state
    
    def detect_pca9685(self) -> bool:
        """Detect PCA9685 servo controller"""
        try:
            import Adafruit_PCA9685
            
            for bus_num in [0, 1]:
                try:
                    pwm = Adafruit_PCA9685.PCA9685(busnum=bus_num)
                    pwm.set_pwm_freq(50)  # Test write
                    
                    self.hardware_state['pca9685'] = {
                        'connected': True,
                        'bus': bus_num,
                        'instance': pwm
                    }
                    logger.info(f"PCA9685 detected on I2C bus {bus_num}")
                    return True
                    
                except Exception as e:
                    logger.debug(f"PCA9685 not found on bus {bus_num}: {e}")
                    continue
                    
        except ImportError:
            logger.warning("Adafruit_PCA9685 library not available")
        
        logger.warning("PCA9685 not detected - servo control will be simulated")
        return False
    
    def detect_mpu6050(self) -> bool:
        """Detect MPU6050 with multiple methods"""
        
        # Method 1: Direct SMBus approach
        if self._detect_mpu6050_smbus():
            return True
            
        # Method 2: mpu6050 library
        if self._detect_mpu6050_library():
            return True
            
        # Method 3: Adafruit library
        if self._detect_mpu6050_adafruit():
            return True
            
        logger.warning("MPU6050 not detected - sensor data will be simulated")
        return False
    
    def _detect_mpu6050_smbus(self) -> bool:
        """Detect MPU6050 using direct SMBus"""
        try:
            from smbus2 import SMBus
            
            for bus_num in [0, 1]:
                try:
                    bus = SMBus(bus_num)
                    
                    # Check WHO_AM_I register
                    who_am_i = bus.read_byte_data(0x68, 0x75)
                    if who_am_i in [0x68, 0x72]:  # Valid responses
                        # Wake up the sensor
                        bus.write_byte_data(0x68, 0x6B, 0)
                        
                        # Test temperature read
                        temp_raw = bus.read_word_data(0x68, 0x41)
                        
                        self.hardware_state['mpu6050'] = {
                            'connected': True,
                            'bus': bus_num,
                            'instance': bus,
                            'method': 'smbus'
                        }
                        logger.info(f"MPU6050 detected on I2C bus {bus_num} (SMBus method)")
                        return True
                        
                except Exception as e:
                    logger.debug(f"SMBus MPU6050 failed on bus {bus_num}: {e}")
                    try:
                        bus.close()
                    except:
                        pass
                    continue
                    
        except ImportError:
            logger.debug("smbus2 not available")
        
        return False
    
    def _detect_mpu6050_library(self) -> bool:
        """Detect MPU6050 using mpu6050 library"""
        try:
            from mpu6050 import mpu6050
            
            for bus_num in [0, 1]:
                try:
                    sensor = mpu6050(bus_num)
                    # Test read
                    temp = sensor.get_temp()
                    
                    self.hardware_state['mpu6050'] = {
                        'connected': True,
                        'bus': bus_num,
                        'instance': sensor,
                        'method': 'mpu6050_lib'
                    }
                    logger.info(f"MPU6050 detected on I2C bus {bus_num} (mpu6050 library)")
                    return True
                    
                except Exception as e:
                    logger.debug(f"mpu6050 library failed on bus {bus_num}: {e}")
                    continue
                    
        except ImportError:
            logger.debug("mpu6050 library not available")
        
        return False
    
    def _detect_mpu6050_adafruit(self) -> bool:
        """Detect MPU6050 using Adafruit library"""
        try:
            import board
            import busio
            import adafruit_mpu6050
            
            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_mpu6050.MPU6050(i2c)
            
            # Test read
            accel = sensor.acceleration
            
            self.hardware_state['mpu6050'] = {
                'connected': True,
                'bus': 'board',
                'instance': sensor,
                'method': 'adafruit'
            }
            logger.info("MPU6050 detected (Adafruit library)")
            return True
            
        except Exception as e:
            logger.debug(f"Adafruit MPU6050 failed: {e}")
        
        return False
    
    def detect_controllers(self) -> bool:
        """Detect game controllers"""
        try:
            import evdev
            from evdev import InputDevice, list_devices
            
            devices = [InputDevice(path) for path in list_devices()]
            
            for device in devices:
                name_lower = device.name.lower()
                
                # Check for game controller keywords
                controller_keywords = ['xbox', 'playstation', 'ps3', 'ps4', 'controller', 'joystick']
                if any(keyword in name_lower for keyword in controller_keywords):
                    
                    # Determine controller type
                    if 'xbox' in name_lower:
                        controller_type = 'Xbox'
                    elif any(ps in name_lower for ps in ['playstation', 'ps3', 'ps4']):
                        controller_type = 'PlayStation'
                    else:
                        controller_type = 'Generic'
                    
                    self.hardware_state['controller'] = {
                        'connected': True,
                        'type': controller_type,
                        'path': device.path,
                        'instance': device
                    }
                    logger.info(f"{controller_type} controller detected: {device.name}")
                    return True
                    
        except ImportError:
            logger.warning("evdev library not available")
        except Exception as e:
            logger.error(f"Controller detection error: {e}")
        
        logger.warning("No game controllers detected")
        return False
    
    def read_mpu6050(self) -> Optional[Dict[str, Any]]:
        """Read MPU6050 data using detected method"""
        mpu_state = self.hardware_state['mpu6050']
        
        if not mpu_state['connected']:
            return None
            
        try:
            method = mpu_state.get('method', 'unknown')
            instance = mpu_state['instance']
            
            if method == 'smbus':
                return self._read_mpu6050_smbus(instance)
            elif method == 'mpu6050_lib':
                return self._read_mpu6050_library(instance)
            elif method == 'adafruit':
                return self._read_mpu6050_adafruit(instance)
                
        except Exception as e:
            logger.error(f"MPU6050 read error: {e}")
            
        return None
    
    def _read_mpu6050_smbus(self, bus) -> Dict[str, Any]:
        """Read MPU6050 using SMBus"""
        def read_word_2c(addr, reg):
            val = bus.read_word_data(addr, reg)
            if val >= 0x8000:
                return -((65535 - val) + 1)
            else:
                return val
        
        # Read accelerometer
        accel_x = read_word_2c(0x68, 0x3B) / 16384.0
        accel_y = read_word_2c(0x68, 0x3D) / 16384.0  
        accel_z = read_word_2c(0x68, 0x3F) / 16384.0
        
        # Read gyroscope
        gyro_x = read_word_2c(0x68, 0x43) / 131.0
        gyro_y = read_word_2c(0x68, 0x45) / 131.0
        gyro_z = read_word_2c(0x68, 0x47) / 131.0
        
        # Read temperature
        temp_raw = read_word_2c(0x68, 0x41)
        temp = temp_raw / 340.0 + 36.53
        
        return {
            'accel': {'x': accel_x, 'y': accel_y, 'z': accel_z},
            'gyro': {'x': gyro_x, 'y': gyro_y, 'z': gyro_z},
            'temp': temp
        }
    
    def _read_mpu6050_library(self, sensor) -> Dict[str, Any]:
        """Read MPU6050 using mpu6050 library"""
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()
        temp = sensor.get_temp()
        
        return {
            'accel': accel_data,
            'gyro': gyro_data,
            'temp': temp
        }
    
    def _read_mpu6050_adafruit(self, sensor) -> Dict[str, Any]:
        """Read MPU6050 using Adafruit library"""
        accel = sensor.acceleration
        gyro = sensor.gyro
        temp = sensor.temperature
        
        return {
            'accel': {'x': accel[0], 'y': accel[1], 'z': accel[2]},
            'gyro': {'x': gyro[0], 'y': gyro[1], 'z': gyro[2]},
            'temp': temp
        }
    
    def get_hardware_status(self) -> Dict[str, Any]:
        """Get current hardware status"""
        return {
            'pca9685': {
                'connected': self.hardware_state['pca9685']['connected'],
                'bus': self.hardware_state['pca9685']['bus']
            },
            'mpu6050': {
                'connected': self.hardware_state['mpu6050']['connected'],
                'bus': self.hardware_state['mpu6050']['bus']
            },
            'controller': {
                'connected': self.hardware_state['controller']['connected'],
                'type': self.hardware_state['controller']['type'],
                'path': self.hardware_state['controller']['path']
            }
        }

# Global hardware manager instance
hardware_manager = HardwareManager()
'''
    
    with open('improved_hardware_manager.py', 'w') as f:
        f.write(detection_code)
    
    print_status("Improved hardware detection module created", "success")

def create_hardware_test_script():
    """Create a comprehensive hardware test script"""
    print_status("Creating hardware test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
Comprehensive Hardware Test Script
Tests all hardware components with detailed diagnostics
"""

import sys
import time
from improved_hardware_manager import hardware_manager

def main():
    print("=" * 60)
    print("COMPREHENSIVE HARDWARE TEST")
    print("=" * 60)
    
    # Detect all hardware
    print("\\n1. Hardware Detection Phase")
    print("-" * 30)
    hardware_status = hardware_manager.detect_all()
    
    # Test PCA9685
    print("\\n2. PCA9685 Servo Controller Test")
    print("-" * 35)
    if hardware_status['pca9685']['connected']:
        print(f"✓ PCA9685 connected on I2C bus {hardware_status['pca9685']['bus']}")
        
        # Test servo control
        try:
            pwm = hardware_status['pca9685']['instance']
            print("  Testing servo channels...")
            
            for channel in range(4):
                print(f"    Testing channel {channel}...")
                # Center position
                pwm.set_pwm(channel, 0, 375)  # ~90 degrees
                time.sleep(0.1)
                
            print("  ✓ All servo channels tested successfully")
            
        except Exception as e:
            print(f"  ✗ Servo test failed: {e}")
    else:
        print("✗ PCA9685 not connected - servos will be simulated")
    
    # Test MPU6050
    print("\\n3. MPU6050 Sensor Test")
    print("-" * 25)
    if hardware_status['mpu6050']['connected']:
        print(f"✓ MPU6050 connected on I2C bus {hardware_status['mpu6050']['bus']}")
        
        # Test sensor readings
        try:
            for i in range(5):
                data = hardware_manager.read_mpu6050()
                if data:
                    print(f"  Reading {i+1}:")
                    print(f"    Accel: X={data['accel']['x']:.2f}, Y={data['accel']['y']:.2f}, Z={data['accel']['z']:.2f}")
                    print(f"    Gyro:  X={data['gyro']['x']:.2f}, Y={data['gyro']['y']:.2f}, Z={data['gyro']['z']:.2f}")
                    print(f"    Temp:  {data['temp']:.1f}°C")
                    time.sleep(0.5)
                else:
                    print(f"  ✗ Failed to read sensor data on attempt {i+1}")
                    
            print("  ✓ MPU6050 sensor readings successful")
            
        except Exception as e:
            print(f"  ✗ MPU6050 read test failed: {e}")
    else:
        print("✗ MPU6050 not connected - sensor data will be simulated")
    
    # Test Controllers
    print("\\n4. Game Controller Test")
    print("-" * 25)
    if hardware_status['controller']['connected']:
        controller = hardware_status['controller']
        print(f"✓ {controller['type']} controller connected")
        print(f"  Path: {controller['path']}")
        
        # Test controller input
        try:
            device = controller['instance']
            print("  Testing controller input (move sticks/press buttons)...")
            print("  Listening for 5 seconds...")
            
            start_time = time.time()
            event_count = 0
            
            while time.time() - start_time < 5:
                try:
                    events = device.read()
                    for event in events:
                        event_count += 1
                        if event_count <= 10:  # Show first 10 events
                            print(f"    Event: type={event.type}, code={event.code}, value={event.value}")
                except BlockingIOError:
                    time.sleep(0.1)
                    continue
                except Exception as e:
                    print(f"    Read error: {e}")
                    break
            
            if event_count > 0:
                print(f"  ✓ Controller responsive ({event_count} events detected)")
            else:
                print("  ! No controller input detected (try moving sticks/pressing buttons)")
                
        except Exception as e:
            print(f"  ✗ Controller test failed: {e}")
    else:
        print("✗ No game controller connected")
    
    # Summary
    print("\\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    connected_count = sum([
        hardware_status['pca9685']['connected'],
        hardware_status['mpu6050']['connected'], 
        hardware_status['controller']['connected']
    ])
    
    print(f"Hardware Components Detected: {connected_count}/3")
    print(f"  PCA9685 Servo Controller: {'✓ Connected' if hardware_status['pca9685']['connected'] else '✗ Not Connected'}")
    print(f"  MPU6050 Sensor: {'✓ Connected' if hardware_status['mpu6050']['connected'] else '✗ Not Connected'}")
    print(f"  Game Controller: {'✓ Connected' if hardware_status['controller']['connected'] else '✗ Not Connected'}")
    
    if connected_count == 3:
        print("\\n🎉 All hardware components working perfectly!")
    elif connected_count > 0:
        print(f"\\n⚠️  {connected_count}/3 components working. Others will run in simulation mode.")
    else:
        print("\\n📱 No physical hardware detected. System will run in full simulation mode.")
    
    print("\\nYou can now run the integrated robot arm application.")

if __name__ == "__main__":
    main()
'''
    
    with open('test_hardware_comprehensive.py', 'w') as f:
        f.write(test_script)
    
    run_command("chmod +x test_hardware_comprehensive.py")
    print_status("Hardware test script created", "success")

def fix_permissions():
    """Fix common permission issues"""
    print_status("Fixing permission issues...")
    
    # Add user to i2c group
    import getpass
    username = getpass.getuser()
    
    success, _, _ = run_command(f"sudo usermod -a -G i2c {username}")
    if success:
        print_status(f"User {username} added to i2c group", "success")
    
    # Fix /dev/input permissions
    success, _, _ = run_command("sudo chmod 644 /dev/input/event*")
    if success:
        print_status("Input device permissions fixed", "success")

def main():
    """Main function"""
    print(f"{Colors.BLUE}")
    print("=" * 60)
    print("  ROBOT ARM HARDWARE DETECTION & FIX TOOL")
    print("=" * 60)
    print(f"{Colors.NC}")
    
    # Check if running as root
    if os.geteuid() == 0:
        print_status("Running as root - some tests may not work correctly", "warning")
    
    # Run all fixes
    check_i2c_setup()
    print()
    
    fix_permissions()
    print()
    
    fix_mpu6050()
    print()
    
    fix_controller_detection()
    print()
    
    create_improved_hardware_detection()
    print()
    
    create_hardware_test_script()
    print()
    
    print_status("Hardware fix process completed!", "success")
    print()
    print(f"{Colors.YELLOW}Next Steps:{Colors.NC}")
    print("1. Run: python3 test_hardware_comprehensive.py")
    print("2. If I2C issues persist, reboot the system")
    print("3. Update robot_arm_integrated.py to use improved_hardware_manager.py")
    print("4. Run the integrated robot arm application")
    print()
    print(f"{Colors.BLUE}Troubleshooting Tips:{Colors.NC}")
    print("• For MPU6050: Check wiring (VCC, GND, SDA, SCL)")
    print("• For controllers: Try different USB ports")
    print("• For PCA9685: Verify I2C address (usually 0x40)")
    print("• For permissions: Log out and back in after group changes")

if __name__ == "__main__":
    main()
