# Robot Arm Virtual UI v0.2.3-1

A web-based 3D interface for controlling a 4DoF (4 Degrees of Freedom) robot arm with real-time visualization.

![Robot Arm Virtual UI Screenshot](https://via.placeholder.com/800x450.png?text=Robot+Arm+Virtual+UI)

## Features

- Interactive 3D visualization of a 4-servo robot arm
- Dual virtual joystick controls with intuitive mapping
- Precision slider controls for exact angle positioning
- Responsive design that works on desktop and mobile
- Automatic port selection and configuration
- Status display and logging for monitoring

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/robot-arm-virtual-ui.git
cd robot-arm-virtual-ui

# Run the application
./run.sh
```

Then open your browser and navigate to the URL displayed in the console (typically http://localhost:5000).

## Installation

### Prerequisites

- Python 3.6 or higher
- Flask 2.0.1

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/robot-arm-virtual-ui.git
   cd robot-arm-virtual-ui
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Linux/Mac
   source venv/bin/activate
   
   # Activate on Windows
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Run the application with the included script:
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate  # Activate virtual environment
cd src
python robot_arm_app.py
```

The application will automatically find an available port and display the URL in the console.

### Interface Controls

#### Joystick Controls

The interface provides two virtual joysticks:

- **Left Joystick**:
  - X-axis: Controls Servo 0 (base rotation, left/right)
  - Y-axis: Controls Servo 1 (lower joint, up/down)

- **Right Joystick**:
  - X-axis: Controls Servo 3 (gripper rotation, left/right)
  - Y-axis: Controls Servo 2 (upper joint, up/down)

#### Slider Controls

Each servo can be precisely controlled with its own slider:

- **Servo 0**: Base rotation (0-270 degrees)
- **Servo 1**: Lower arm joint (0-270 degrees)
- **Servo 2**: Upper arm joint (0-270 degrees)
- **Servo 3**: Gripper rotation (0-270 degrees)

The joysticks and sliders are synchronized and will update each other in real time.

### Configuration Options

#### Changing the Port Range

By default, the application searches for available ports starting from 5000. To change this:

1. Open `src/robot_arm_app.py`
2. Locate the `find_available_port` function call
3. Modify the `start_port` parameter:
   ```python
   port = find_available_port(start_port=8000)  # Start from port 8000
   ```

#### Adjusting Servo Limits

To change the range of motion for the servos:

1. Open `src/templates/index.html`
2. Find the slider inputs and adjust the `min` and `max` attributes:
   ```html
   <input type="range" id="channel0" min="0" max="270" value="135">
   ```

3. Also update the corresponding JavaScript calculations in `src/static/robot_arm.js`

## Project Structure

```
robot_arm_virtual_ui/
├── run.sh              # Main run script
├── robot_arm_app.py    # Symlink to src/robot_arm_app.py
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
├── src/                # Source code
│   ├── robot_arm_app.py  # Main Flask application
│   ├── static/           # Static web assets
│   │   └── robot_arm.js  # JavaScript for 3D model and controls
│   └── templates/        # HTML templates
│       └── index.html    # Main web interface
├── utils/              # Utility scripts
├── venv/               # Python virtual environment
└── backups/            # Backup directory
```

## Extension Points

### Connecting to Real Hardware

The current implementation simulates a robot arm, but it can be extended to control real hardware:

1. Modify the `update_servo_positions` function in `src/robot_arm_app.py` to send commands to your hardware
2. Implement hardware communication through GPIO pins, serial communication, or other interfaces

Example for Raspberry Pi with Adafruit ServoKit:
```python
# Add to imports
from adafruit_servokit import ServoKit

# Initialize servo controller
kit = ServoKit(channels=16)

# In update_servo_positions function
def update_servo_positions():
    data = request.json
    for channel in range(4):
        key = f'channel{channel}'
        if key in data:
            value = max(0, min(270, data[key]))
            arm_state[key] = value
            
            # Convert from 0-270 to 0-180 for standard servos
            servo_value = int(value * 180 / 270)
            kit.servo[channel].angle = servo_value
    
    # Rest of the function...
```

### Customizing the 3D Model

To change the appearance or proportions of the 3D robot arm:

1. Modify the `createRobotArm` function in `src/static/robot_arm.js`
2. Adjust the geometry, materials, and positioning of the arm segments

## Troubleshooting

### Port Conflicts

If you see an error about the port being in use:
- The application will automatically try the next available port
- If it still fails, try manually specifying a different port:
  ```python
  app.run(host='0.0.0.0', port=8080, debug=False)
  ```

### Display Issues

If the 3D model doesn't render correctly:
- Ensure your browser supports WebGL
- Try a different browser (Chrome or Firefox recommended)
- Update your graphics drivers

## Version History

- **v0.2.3-1**: Added fully responsive design that scales to browser size with improved visual styling
- **v0.2.2-1**: Improved 3D rendering with better camera position and fixed port configuration
- **v0.2.1-1**: Updated interface with larger 3D view and reorganized controls
- **v0.1.0**: Initial release
## Development Version (v0.3.1-1)

A development version of the robot arm interface is available with additional features:

### Accessing the Development Version

The development version is available at:
```
http://localhost:[PORT]/dev
```

While the stable version continues to be available at:
```
http://localhost:[PORT]/
```

### New Features in v0.3.1-1

1. **Dark Mode**
   - Click the moon/sun icon in the top right to toggle between light and dark modes

2. **Repositioned Servo Joint**
   - The connection point of servo/channel 1 has been moved from the base to the top of servo/channel 0 block

3. **Preset Position Buttons**
   - "Move Left [000]" - Sets all servos to 0 degrees
   - "Center [135]" - Sets all servos to 135 degrees (center position)
   - "Move Right [270]" - Sets all servos to 270 degrees

4. **Random Movement Generator**
   - Click "Random Movement" to automatically move the arm through 10 random positions
   - Click again to stop the random movement

5. **Reset Button**
   - Returns all servos to their initial center position (135 degrees)

6. **MPU6050 Sensor Simulation**
   - A virtual MPU6050 sensor is attached to servo/channel 3
   - Real-time accelerometer and gyroscope readings are displayed
   - Values update based on the current position and orientation of the arm

### Coming Soon

- Position recording and playback
- Custom sequence programming
- Inverse kinematics support
- Additional sensor simulations
## UI Refinements Update

Recent updates to the Robot Arm Virtual UI include:

### Development Version (v0.3.1-1) Improvements

1. **UI Layout Refinements**
   - All control buttons are now in a single row for easier access
   - MPU6050 sensor information moved to a compact panel next to control buttons
   - Enlarged 3D render frame to better accommodate the robot arm's full range
   
2. **Improved User Experience**
   - Joystick handles now automatically return to center when released
   - Servo positions are maintained when joysticks are released
   - Random movement now has fluid transitions between positions
   
3. **Stable Version Update**
   - Changed servo joint connection point in the stable version to match development version
   - Servo 1 now connects to the top of servo 0 block for better arm movement

### Accessing the Development Version

The development version with all new features is available at:
```
http://localhost:[PORT]/dev
```

While the regular version with only the servo position update is available at:
```
http://localhost:[PORT]/
```
