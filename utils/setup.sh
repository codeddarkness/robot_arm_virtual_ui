#!/bin/bash

# Robot Arm Virtual UI Setup Script
# This script sets up the environment and organizes the project files

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Robot Arm Virtual UI...${NC}"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Create project directory structure directly (no nested directory)
echo -e "${GREEN}✓ Setting up directory structure${NC}"

# Check if virtualenv is installed
if ! $PYTHON_CMD -c "import virtualenv" &>/dev/null; then
    echo -e "${YELLOW}! virtualenv not found. Installing virtualenv...${NC}"
    $PYTHON_CMD -m pip install virtualenv
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install virtualenv. Please install manually:${NC}"
        echo "   pip install virtualenv"
        exit 1
    fi
    echo -e "${GREEN}✓ virtualenv installed successfully${NC}"
else
    echo -e "${GREEN}✓ virtualenv is already installed${NC}"
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m virtualenv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}! Virtual environment already exists${NC}"
fi

# Determine the activation command based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    ACTIVATE_CMD="source venv/Scripts/activate"
else
    # Linux/Mac
    ACTIVATE_CMD="source venv/bin/activate"
fi

# Create the necessary subdirectories
mkdir -p static templates
echo -e "${GREEN}✓ Created subdirectories: static, templates${NC}"

# Create the main Python application file
echo "Creating application file: robot_arm_app.py"
cat > robot_arm_app.py << 'EOF'
import os
import logging
import socket
from flask import Flask, render_template, jsonify, request

# Setup logging
logging.basicConfig(filename='robot_arm.log', level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Robot arm state
arm_state = {
    'channel0': 135,  # Default to middle position (0-270 degrees)
    'channel1': 135,
    'channel2': 135,
    'channel3': 135
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/servo', methods=['GET'])
def get_servo_positions():
    return jsonify(arm_state)

@app.route('/api/servo', methods=['POST'])
def update_servo_positions():
    data = request.json
    for channel in range(4):
        key = f'channel{channel}'
        if key in data:
            # Ensure value is within 0-270 range
            arm_state[key] = max(0, min(270, data[key]))
            
    # Log the current position
    logger.info(f"Servo positions updated: {arm_state}")
    print(f"\rPositions: Ch0: {arm_state['channel0']}° | Ch1: {arm_state['channel1']}° | " +
          f"Ch2: {arm_state['channel2']}° | Ch3: {arm_state['channel3']}°", end='')
    
    return jsonify({"status": "success", "state": arm_state})

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port  # Default fallback

if __name__ == '__main__':
    # Find available port
    port = find_available_port()
    print(f"Starting robot arm server on http://localhost:{port}")
    print("Press Ctrl+C to exit")
    print("Current servo positions will be displayed below:")
    app.run(debug=True, port=port)
EOF
echo -e "${GREEN}✓ Created robot_arm_app.py${NC}"

# Create the HTML template
echo "Creating HTML template: templates/index.html"
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4DoF Robot Arm Controller</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
        .container { max-width: 900px; margin: 0 auto; }
        .model-container { height: 400px; margin-bottom: 20px; border: 1px solid #ccc; }
        .controls { display: flex; flex-direction: column; gap: 20px; }
        .joysticks-container { display: flex; justify-content: space-around; }
        .joystick { position: relative; width: 150px; height: 150px; border-radius: 50%; background: #eee; }
        .joystick-handle { position: absolute; width: 50px; height: 50px; border-radius: 50%; background: #555; 
                         top: 50px; left: 50px; cursor: pointer; }
        .joystick-label { text-align: center; margin-top: 5px; font-weight: bold; }
        .sliders-container { display: flex; flex-direction: column; gap: 10px; }
        .slider-group { display: flex; align-items: center; }
        .servo-label { width: 80px; }
        .angle-display { width: 50px; text-align: right; padding-right: 10px; }
        input[type="range"] { flex-grow: 1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>4DoF Robot Arm Controller</h1>
        <div id="model-container" class="model-container"></div>
        
        <div class="controls">
            <h2>Joystick Controls</h2>
            <div class="joysticks-container">
                <div class="joystick-wrapper">
                    <div id="left-joystick" class="joystick">
                        <div id="left-handle" class="joystick-handle"></div>
                    </div>
                    <div class="joystick-label">Left Joystick<br>X: Ch0, Y: Ch1</div>
                </div>
                <div class="joystick-wrapper">
                    <div id="right-joystick" class="joystick">
                        <div id="right-handle" class="joystick-handle"></div>
                    </div>
                    <div class="joystick-label">Right Joystick<br>X: Ch3, Y: Ch2</div>
                </div>
            </div>
            
            <h2>Slider Controls</h2>
            <div class="sliders-container">
                <div class="slider-group">
                    <span class="servo-label">Servo 0:</span>
                    <span id="angle0" class="angle-display">135°</span>
                    <input type="range" id="channel0" min="0" max="270" value="135">
                </div>
                <div class="slider-group">
                    <span class="servo-label">Servo 1:</span>
                    <span id="angle1" class="angle-display">135°</span>
                    <input type="range" id="channel1" min="0" max="270" value="135">
                </div>
                <div class="slider-group">
                    <span class="servo-label">Servo 2:</span>
                    <span id="angle2" class="angle-display">135°</span>
                    <input type="range" id="channel2" min="0" max="270" value="135">
                </div>
                <div class="slider-group">
                    <span class="servo-label">Servo 3:</span>
                    <span id="angle3" class="angle-display">135°</span>
                    <input type="range" id="channel3" min="0" max="270" value="135">
                </div>
            </div>
        </div>
    </div>

    <script src="/static/robot_arm.js"></script>
</body>
</html>
EOF
echo -e "${GREEN}✓ Created templates/index.html${NC}"

# Create the JavaScript file
echo "Creating JavaScript file: static/robot_arm.js"
cat > static/robot_arm.js << 'EOF'
// Global variables
let scene, camera, renderer;
let armBase, armLower, armUpper, armGripper;
let isDragging = { left: false, right: false };
let servoAngles = { channel0: 135, channel1: 135, channel2: 135, channel3: 135 };
let updateTimeout;

// Initialize Three.js scene
function initScene() {
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    
    // Create camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / 400, 0.1, 1000);
    camera.position.set(0, 5, 10);
    camera.lookAt(0, 0, 0);
    
    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(document.getElementById('model-container').offsetWidth, 400);
    document.getElementById('model-container').appendChild(renderer.domElement);
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);
    
    // Create robot arm
    createRobotArm();
    
    // Add ground
    const groundGeometry = new THREE.PlaneGeometry(20, 20);
    const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x999999 });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.5;
    scene.add(ground);
    
    // Handle window resize
    window.addEventListener('resize', () => {
        renderer.setSize(document.getElementById('model-container').offsetWidth, 400);
        camera.aspect = document.getElementById('model-container').offsetWidth / 400;
        camera.updateProjectionMatrix();
    });
    
    // Start animation loop
    animate();
}

// Create robot arm segments
function createRobotArm() {
    // Base
    const baseGeometry = new THREE.CylinderGeometry(1, 1, 0.5, 32);
    const baseMaterial = new THREE.MeshStandardMaterial({ color: 0x444444 });
    const base = new THREE.Mesh(baseGeometry, baseMaterial);
    base.position.y = -0.25;
    scene.add(base);
    
    // Arm base (rotates on Y axis - channel 0)
    armBase = new THREE.Group();
    const baseJointGeometry = new THREE.BoxGeometry(0.5, 1, 0.5);
    const baseJointMaterial = new THREE.MeshStandardMaterial({ color: 0xdd0000 });
    const baseJoint = new THREE.Mesh(baseJointGeometry, baseJointMaterial);
    baseJoint.position.y = 0.5;
    armBase.add(baseJoint);
    scene.add(armBase);
    
    // Lower arm segment (rotates on Z axis - channel 1)
    armLower = new THREE.Group();
    const lowerArmGeometry = new THREE.BoxGeometry(0.4, 3, 0.4);
    const lowerArmMaterial = new THREE.MeshStandardMaterial({ color: 0x00dd00 });
    const lowerArm = new THREE.Mesh(lowerArmGeometry, lowerArmMaterial);
    lowerArm.position.y = 1.5;
    armLower.add(lowerArm);
    armBase.add(armLower);
    
    // Upper arm segment (rotates on Z axis - channel 2)
    armUpper = new THREE.Group();
    const upperArmGeometry = new THREE.BoxGeometry(0.3, 2, 0.3);
    const upperArmMaterial = new THREE.MeshStandardMaterial({ color: 0x0000dd });
    const upperArm = new THREE.Mesh(upperArmGeometry, upperArmMaterial);
    upperArm.position.y = 1;
    armUpper.add(upperArm);
    armUpper.position.y = 3;
    armLower.add(armUpper);
    
    // Gripper (rotates on Y axis - channel 3)
    armGripper = new THREE.Group();
    const gripperGeometry = new THREE.BoxGeometry(0.2, 0.2, 1);
    const gripperMaterial = new THREE.MeshStandardMaterial({ color: 0xffaa00 });
    const gripper = new THREE.Mesh(gripperGeometry, gripperMaterial);
    gripper.position.z = 0.5;
    armGripper.add(gripper);
    armGripper.position.y = 2;
    armUpper.add(armGripper);
    
    // Initial arm position
    updateArmPosition();
}

// Update the robot arm position based on servo angles
function updateArmPosition() {
    // Convert angles from 0-270 range to radians for 3D model
    // Channel 0: Base rotation (Y-axis)
    armBase.rotation.y = THREE.MathUtils.degToRad(servoAngles.channel0 - 135);
    
    // Channel 1: Lower arm rotation (Z-axis)
    // Map from 0-270 to appropriate rotation range with offset to make 135 the neutral position
    armLower.rotation.z = THREE.MathUtils.degToRad(-1 * (servoAngles.channel1 - 135) * 0.6);
    
    // Channel 2: Upper arm rotation (Z-axis)
    armUpper.rotation.z = THREE.MathUtils.degToRad(-1 * (servoAngles.channel2 - 135) * 0.6);
    
    // Channel 3: Gripper rotation (Y-axis)
    armGripper.rotation.y = THREE.MathUtils.degToRad(servoAngles.channel3 - 135);
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

// Initialize joystick controls
function initJoysticks() {
    const leftJoystick = document.getElementById('left-joystick');
    const leftHandle = document.getElementById('left-handle');
    const rightJoystick = document.getElementById('right-joystick');
    const rightHandle = document.getElementById('right-handle');
    
    // Left joystick events (Channels 0 and 1)
    leftHandle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isDragging.left = true;
    });
    
    // Right joystick events (Channels 2 and 3)
    rightHandle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isDragging.right = true;
    });
    
    // Mouse move handling for both joysticks
    document.addEventListener('mousemove', (e) => {
        if (isDragging.left) {
            moveJoystick(e, leftJoystick, leftHandle, 'left');
        }
        if (isDragging.right) {
            moveJoystick(e, rightJoystick, rightHandle, 'right');
        }
    });
    
    // Mouse up handling
    document.addEventListener('mouseup', () => {
        isDragging.left = false;
        isDragging.right = false;
    });
    
    // Touch events for mobile
    leftHandle.addEventListener('touchstart', (e) => {
        e.preventDefault();
        isDragging.left = true;
    });
    
    rightHandle.addEventListener('touchstart', (e) => {
        e.preventDefault();
        isDragging.right = true;
    });
    
    document.addEventListener('touchmove', (e) => {
        if (isDragging.left || isDragging.right) {
            e.preventDefault();
            
            const touch = e.touches[0];
            
            if (isDragging.left) {
                moveJoystick({ clientX: touch.clientX, clientY: touch.clientY }, 
                             leftJoystick, leftHandle, 'left');
            }
            
            if (isDragging.right) {
                moveJoystick({ clientX: touch.clientX, clientY: touch.clientY }, 
                             rightJoystick, rightHandle, 'right');
            }
        }
    });
    
    document.addEventListener('touchend', () => {
        isDragging.left = false;
        isDragging.right = false;
    });
}

// Move joystick handle based on mouse/touch position
function moveJoystick(e, joystick, handle, which) {
    const joystickRect = joystick.getBoundingClientRect();
    
    // Calculate joystick center
    const centerX = joystickRect.left + joystickRect.width / 2;
    const centerY = joystickRect.top + joystickRect.height / 2;
    
    // Calculate relative position
    let x = e.clientX - centerX;
    let y = e.clientY - centerY;
    
    // Limit to joystick radius
    const radius = joystickRect.width / 2 - handle.offsetWidth / 2;
    const distance = Math.sqrt(x * x + y * y);
    
    if (distance > radius) {
        x = (x / distance) * radius;
        y = (y / distance) * radius;
    }
    
    // Position handle
    handle.style.left = `${x + joystickRect.width / 2 - handle.offsetWidth / 2}px`;
    handle.style.top = `${y + joystickRect.height / 2 - handle.offsetHeight / 2}px`;
    
    // Map joystick position to servo angles (0-270 degrees)
    let xAngle, yAngle;
    
    // Normalize inputs to -1 to 1
    const normalizedX = x / radius;
    const normalizedY = y / radius;
    
    // Convert to 0-270 range for servos
    xAngle = Math.round(135 + normalizedX * 135);
    yAngle = Math.round(135 - normalizedY * 135);
    
    // Update appropriate channels based on which joystick
    if (which === 'left') {
        // Left joystick: X controls channel0, Y controls channel1
        servoAngles.channel0 = xAngle;
        servoAngles.channel1 = yAngle;
        
        // Update sliders
        document.getElementById('channel0').value = xAngle;
        document.getElementById('channel1').value = yAngle;
        document.getElementById('angle0').textContent = `${xAngle}°`;
        document.getElementById('angle1').textContent = `${yAngle}°`;
    } else {
        // Right joystick: Y controls channel2, X controls channel3
        servoAngles.channel2 = yAngle;
        servoAngles.channel3 = xAngle;
        
        // Update sliders
        document.getElementById('channel2').value = yAngle;
        document.getElementById('channel3').value = xAngle;
        document.getElementById('angle2').textContent = `${yAngle}°`;
        document.getElementById('angle3').textContent = `${xAngle}°`;
    }
    
    // Update 3D model
    updateArmPosition();
    
    // Send updates to server (with debounce)
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(() => {
        sendServoUpdate();
    }, 50);
}

// Initialize slider controls
function initSliders() {
    for (let i = 0; i < 4; i++) {
        const slider = document.getElementById(`channel${i}`);
        const display = document.getElementById(`angle${i}`);
        
        slider.addEventListener('input', function() {
            const value = parseInt(this.value);
            display.textContent = `${value}°`;
            servoAngles[`channel${i}`] = value;
            
            // Update 3D model
            updateArmPosition();
            
            // Send updates to server (with debounce)
            clearTimeout(updateTimeout);
            updateTimeout = setTimeout(() => {
                sendServoUpdate();
            }, 50);
        });
    }
}

// Send servo updates to server
function sendServoUpdate() {
    fetch('/api/servo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(servoAngles)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Update successful:', data);
    })
    .catch(error => {
        console.error('Error updating servos:', error);
    });
}

// Fetch initial servo positions from server
function fetchInitialPositions() {
    fetch('/api/servo')
    .then(response => response.json())
    .then(data => {
        servoAngles = data;
        
        // Update sliders
        for (let i = 0; i < 4; i++) {
            const channel = `channel${i}`;
            document.getElementById(channel).value = servoAngles[channel];
            document.getElementById(`angle${i}`).textContent = `${servoAngles[channel]}°`;
        }
        
        // Update 3D model
        updateArmPosition();
    })
    .catch(error => {
        console.error('Error fetching initial positions:', error);
    });
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    initScene();
    initJoysticks();
    initSliders();
    fetchInitialPositions();
});
EOF
echo -e "${GREEN}✓ Created static/robot_arm.js${NC}"

# Create requirements.txt
echo "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
Flask==2.0.1
EOF
echo -e "${GREEN}✓ Created requirements.txt${NC}"

# Create directory structure document for reference
echo "Creating directory structure documentation..."
cat > directory_structure.sh << 'EOF'
#!/bin/bash
# This file documents the directory structure of the Robot Arm Virtual UI project

echo "Robot Arm Virtual UI Directory Structure:"
echo ""
echo "robot_arm_virtual_ui/"
echo "├── robot_arm_app.py       # Main Flask application"
echo "├── requirements.txt       # Python dependencies"
echo "├── setup.sh               # Setup script"
echo "├── directory_structure.sh # This file"
echo "├── venv/                  # Virtual environment (created by setup script)"
echo "├── templates/"
echo "│   └── index.html         # HTML template for the web interface"
echo "└── static/"
echo "    └── robot_arm.js       # JavaScript for 3D model and controls"
EOF
chmod +x directory_structure.sh
echo -e "${GREEN}✓ Created directory_structure.sh${NC}"

# Copy current script to setup.sh if needed (for reference)
cp "$0" setup.sh 2>/dev/null || :
chmod +x setup.sh 2>/dev/null || :

# Install requirements inside the virtual environment
echo "Installing Flask dependency..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

$PYTHON_CMD -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install dependencies. Try manually:${NC}"
    echo "   $ACTIVATE_CMD"
    echo "   pip install -r requirements.txt"
else
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
fi

# Create a run script
echo "Creating run script..."
cat > run.sh << 'EOF'
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
EOF
chmod +x run.sh
echo -e "${GREEN}✓ Created run.sh${NC}"

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To run the application:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  $ACTIVATE_CMD"
echo "  python robot_arm_app.py"
