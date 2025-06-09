#!/usr/bin/env python3
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
    print("\n1. Hardware Detection Phase")
    print("-" * 30)
    hardware_status = hardware_manager.detect_all()
    
    # Test PCA9685
    print("\n2. PCA9685 Servo Controller Test")
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
    print("\n3. MPU6050 Sensor Test")
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
    print("\n4. Game Controller Test")
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
    print("\n" + "=" * 60)
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
        print("\n🎉 All hardware components working perfectly!")
    elif connected_count > 0:
        print(f"\n⚠️  {connected_count}/3 components working. Others will run in simulation mode.")
    else:
        print("\n📱 No physical hardware detected. System will run in full simulation mode.")
    
    print("\nYou can now run the integrated robot arm application.")

if __name__ == "__main__":
    main()
