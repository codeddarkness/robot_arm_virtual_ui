#!/usr/bin/env python3
"""Simple controller test script"""

def test_controller():
    print("Testing game controller detection...")
    
    try:
        import evdev
        from evdev import InputDevice, list_devices, ecodes
        
        devices = list_devices()
        print(f"\nFound {len(devices)} input devices:")
        
        controllers = []
        
        for device_path in devices:
            try:
                device = InputDevice(device_path)
                print(f"\n{device_path}:")
                print(f"  Name: {device.name}")
                
                # Check if it looks like a game controller
                name_lower = device.name.lower()
                controller_keywords = ['xbox', 'playstation', 'ps3', 'ps4', 'controller', 'joystick', 'gamepad']
                
                is_controller = any(keyword in name_lower for keyword in controller_keywords)
                
                if is_controller:
                    print("  ✓ DETECTED AS GAME CONTROLLER")
                    
                    # Determine type
                    if 'xbox' in name_lower:
                        controller_type = 'Xbox'
                    elif any(ps in name_lower for ps in ['playstation', 'ps3', 'ps4']):
                        controller_type = 'PlayStation'
                    else:
                        controller_type = 'Generic'
                    
                    controllers.append({
                        'path': device_path,
                        'name': device.name,
                        'type': controller_type
                    })
                else:
                    print("  - Not recognized as game controller")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        if controllers:
            print(f"\n{'='*50}")
            print(f"FOUND {len(controllers)} GAME CONTROLLER(S):")
            print(f"{'='*50}")
            
            for i, ctrl in enumerate(controllers):
                print(f"\nController {i+1}:")
                print(f"  Type: {ctrl['type']}")
                print(f"  Name: {ctrl['name']}")
                print(f"  Path: {ctrl['path']}")
            
            return True
            
        else:
            print(f"\n{'='*50}")
            print("NO GAME CONTROLLERS DETECTED")
            print(f"{'='*50}")
            print("\nTroubleshooting:")
            print("1. Connect controller via USB")
            print("2. Try different USB port")
            print("3. Check USB cable")
            print("4. For wireless controllers, ensure they're paired")
            print("5. Run: sudo chmod 644 /dev/input/event*")
            
            return False
            
    except ImportError:
        print("✗ evdev library not available")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_controller()
