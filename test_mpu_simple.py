#!/usr/bin/env python3
"""Simple MPU6050 test script"""

def test_mpu6050():
    print("Testing MPU6050 with multiple methods...")
    
    # Method 1: Direct SMBus
    try:
        from smbus2 import SMBus
        print("\n--- Method 1: Direct SMBus ---")
        
        for bus_num in [0, 1]:
            try:
                bus = SMBus(bus_num)
                # Wake up MPU6050
                bus.write_byte_data(0x68, 0x6B, 0)
                
                # Read WHO_AM_I
                who_am_i = bus.read_byte_data(0x68, 0x75)
                print(f"Bus {bus_num} - WHO_AM_I: 0x{who_am_i:02x}")
                
                if who_am_i in [0x68, 0x72]:
                    # Read temperature
                    temp_h = bus.read_byte_data(0x68, 0x41)
                    temp_l = bus.read_byte_data(0x68, 0x42)
                    temp_raw = (temp_h << 8) | temp_l
                    if temp_raw > 32767:
                        temp_raw -= 65536
                    temp_c = temp_raw / 340.0 + 36.53
                    
                    print(f"✓ MPU6050 working on bus {bus_num}")
                    print(f"  Temperature: {temp_c:.1f}°C")
                    
                    # Read accelerometer
                    ax_h = bus.read_byte_data(0x68, 0x3B)
                    ax_l = bus.read_byte_data(0x68, 0x3C)
                    ax_raw = (ax_h << 8) | ax_l
                    if ax_raw > 32767:
                        ax_raw -= 65536
                    ax = ax_raw / 16384.0
                    
                    print(f"  Accel X: {ax:.2f}g")
                    bus.close()
                    return True
                    
                bus.close()
                    
            except Exception as e:
                print(f"Bus {bus_num} error: {e}")
                
    except ImportError:
        print("smbus2 not available")
    
    # Method 2: mpu6050 library
    try:
        print("\n--- Method 2: mpu6050 library ---")
        from mpu6050 import mpu6050
        
        for bus_num in [0, 1]:
            try:
                sensor = mpu6050(bus_num)
                temp = sensor.get_temp()
                accel = sensor.get_accel_data()
                
                print(f"✓ mpu6050 library working on bus {bus_num}")
                print(f"  Temperature: {temp:.1f}°C")
                print(f"  Accel: X={accel['x']:.2f}, Y={accel['y']:.2f}, Z={accel['z']:.2f}")
                return True
                
            except Exception as e:
                print(f"Bus {bus_num} error: {e}")
                
    except ImportError:
        print("mpu6050 library not available")
    
    print("\n✗ All MPU6050 detection methods failed")
    return False

if __name__ == "__main__":
    test_mpu6050()
