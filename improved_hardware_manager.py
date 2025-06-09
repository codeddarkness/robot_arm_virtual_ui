
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
