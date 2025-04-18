// Robot Arm Virtual UI v0.3.1-1 (Dev)

// Global variables
let scene, camera, renderer;
let armBase, armLower, armUpper, armGripper, mpuSensor;
let isDragging = { left: false, right: false };
let servoAngles = { channel0: 135, channel1: 135, channel2: 135, channel3: 135 };
let targetAngles = { channel0: 135, channel1: 135, channel2: 135, channel3: 135 };
let updateTimeout;
let randomMovementInterval;
let mpuUpdateInterval;
let animationInProgress = false;
let holdTimeout;

// Animation parameters
const ANIMATION_SPEED = 0.05; // Slower animation (was 0.1)
const HOLD_DURATION = 1000; // Hold for 1 second at each position

// MPU6050 simulated data
let mpuData = {
    accelX: 0,
    accelY: 0,
    accelZ: 0,
    gyroX: 0,
    gyroY: 0,
    gyroZ: 0
};

// Initialize Three.js scene
function initScene() {
    // Create scene
    scene = new THREE.Scene();
    updateSceneBackground(); // Set background based on theme
    
    // Create camera with better positioning
    camera = new THREE.PerspectiveCamera(60, document.getElementById('model-container').offsetWidth / document.getElementById('model-container').offsetHeight, 0.1, 1000);
    camera.position.set(0, 4, 8);
    camera.lookAt(0, 2, 0);
    
    // Create renderer with responsive sizing
    renderer = new THREE.WebGLRenderer({ antialias: true });
    updateRendererSize();
    document.getElementById('model-container').appendChild(renderer.domElement);
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    // Add a second light from opposite direction for better illumination
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight2.position.set(-1, 1, -1);
    scene.add(directionalLight2);
    
    // Create robot arm
    createRobotArm();
    
    // Add ground with grid for better perspective
    const groundGeometry = new THREE.PlaneGeometry(20, 20);
    const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x999999 });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.5;
    scene.add(ground);
    
    // Add grid for better perspective
    const gridHelper = new THREE.GridHelper(20, 20, 0x555555, 0x777777);
    gridHelper.position.y = -0.49;
    scene.add(gridHelper);
    
    // Initialize zoom controls
    initZoomControls();
    
    // Handle window resize
    window.addEventListener('resize', handleResize);
    
    // Start animation loop
    animate();
}

// Initialize zoom controls
function initZoomControls() {
    const zoomIn = document.getElementById('zoom-in');
    const zoomOut = document.getElementById('zoom-out');
    
    zoomIn.addEventListener('click', () => {
        // Move camera closer
        if (camera.position.z > 3) { // Limit how close we can zoom
            camera.position.z -= 1;
        }
    });
    
    zoomOut.addEventListener('click', () => {
        // Move camera farther
        if (camera.position.z < 15) { // Limit how far we can zoom
            camera.position.z += 1;
        }
    });
}

// Update the scene background based on theme
function updateSceneBackground() {
    if (scene) {
        const theme = document.documentElement.getAttribute('data-theme');
        if (theme === 'dark') {
            scene.background = new THREE.Color(0x121212);
        } else {
            scene.background = new THREE.Color(0xf5f5f5);
        }
    }
}

// Handle window resize
function handleResize() {
    updateRendererSize();
    camera.aspect = document.getElementById('model-container').offsetWidth / document.getElementById('model-container').offsetHeight;
    camera.updateProjectionMatrix();
}

// Update renderer size based on container
function updateRendererSize() {
    const container = document.getElementById('model-container');
    renderer.setSize(container.offsetWidth, container.offsetHeight);
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
    // CHANGED: Moved connection point to the top of channel 0
    armLower = new THREE.Group();
    const lowerArmGeometry = new THREE.BoxGeometry(0.4, 3, 0.4);
    const lowerArmMaterial = new THREE.MeshStandardMaterial({ color: 0x00dd00 });
    const lowerArm = new THREE.Mesh(lowerArmGeometry, lowerArmMaterial);
    lowerArm.position.y = 1.5;
    armLower.add(lowerArm);
    // Changed position to connect to top of baseJoint
    armLower.position.y = 1.0;
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
    
    // Add MPU6050 sensor visualization
    mpuSensor = new THREE.Group();
    const mpuGeometry = new THREE.BoxGeometry(0.3, 0.05, 0.3);
    const mpuMaterial = new THREE.MeshStandardMaterial({ color: 0x00ffff });
    const mpu = new THREE.Mesh(mpuGeometry, mpuMaterial);
    mpuSensor.add(mpu);
    // Position on top of the gripper
    mpuSensor.position.y = 0.1;
    mpuSensor.position.z = 0.3;
    armGripper.add(mpuSensor);
    
    // Initial arm position
    updateArmPosition();
}

// Animate arm movement to target position
function animateToTarget() {
    // If we're already at the target position, do nothing
    if (isAtTargetPosition()) {
        animationInProgress = false;
        return;
    }
    
    animationInProgress = true;
    
    // Calculate new position by moving a small step toward the target
    for (const channel in servoAngles) {
        const diff = targetAngles[channel] - servoAngles[channel];
        if (Math.abs(diff) > 0.1) {
            servoAngles[channel] += diff * ANIMATION_SPEED;
        } else {
            servoAngles[channel] = targetAngles[channel]; // Snap to exact value when very close
        }
    }
    
    // Update UI to reflect new position
    updateUIFromServoAngles();
    
    // Update 3D model
    updateArmPosition();
    
    // Continue animation if needed
    if (!isAtTargetPosition()) {
        requestAnimationFrame(animateToTarget);
    } else {
        animationInProgress = false;
        sendServoUpdate(); // Send final position to server
    }
}

// Check if current position matches target position
function isAtTargetPosition() {
    for (const channel in servoAngles) {
        if (Math.abs(servoAngles[channel] - targetAngles[channel]) > 0.1) {
            return false;
        }
    }
    return true;
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
    
    // Update MPU6050 data based on current arm position
    updateMPUData();
}

// Update MPU6050 simulated data based on current arm position
function updateMPUData() {
    // Calculate world position and orientation of the MPU sensor
    mpuSensor.updateMatrixWorld();
    const position = new THREE.Vector3();
    position.setFromMatrixPosition(mpuSensor.matrixWorld);
    
    // Calculate acceleration based on position and orientation
    // In a real MPU, acceleration would be affected by gravity and movement
    const gravityVector = new THREE.Vector3(0, -9.81, 0);
    const localGravity = gravityVector.clone();
    
    // Transform gravity to local space of the MPU
    const rotationMatrix = new THREE.Matrix4();
    rotationMatrix.extractRotation(mpuSensor.matrixWorld);
    localGravity.applyMatrix4(rotationMatrix.invert());
    
    // Set accelerometer data (local gravity vector in m/s²)
    mpuData.accelX = parseFloat(localGravity.x.toFixed(2));
    mpuData.accelY = parseFloat(localGravity.y.toFixed(2));
    mpuData.accelZ = parseFloat(localGravity.z.toFixed(2));
    
    // Calculate gyroscope data (angular velocity in degrees/s)
    // This is simplified - in reality would depend on actual movement speed
    const rotationSpeed = 5; // Arbitrary rotation speed for visualization
    mpuData.gyroX = parseFloat((Math.sin(Date.now() / 1000) * rotationSpeed).toFixed(2));
    mpuData.gyroY = parseFloat((Math.cos(Date.now() / 1000) * rotationSpeed).toFixed(2));
    mpuData.gyroZ = parseFloat((Math.sin(Date.now() / 500) * rotationSpeed).toFixed(2));
    
    // Update the UI with new MPU data
    document.getElementById('accel-x').textContent = mpuData.accelX.toFixed(2);
    document.getElementById('accel-y').textContent = mpuData.accelY.toFixed(2);
    document.getElementById('accel-z').textContent = mpuData.accelZ.toFixed(2);
    document.getElementById('gyro-x').textContent = mpuData.gyroX.toFixed(2);
    document.getElementById('gyro-y').textContent = mpuData.gyroY.toFixed(2);
    document.getElementById('gyro-z').textContent = mpuData.gyroZ.toFixed(2);
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
    
    // Mouse up handling - UPDATED: Return joystick to center
    document.addEventListener('mouseup', () => {
        if (isDragging.left) {
            returnJoystickToCenter(leftHandle);
            isDragging.left = false;
        }
        if (isDragging.right) {
            returnJoystickToCenter(rightHandle);
            isDragging.right = false;
        }
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
    
    // Touch end handling - UPDATED: Return joystick to center
    document.addEventListener('touchend', () => {
        if (isDragging.left) {
            returnJoystickToCenter(leftHandle);
            isDragging.left = false;
        }
        if (isDragging.right) {
            returnJoystickToCenter(rightHandle);
            isDragging.right = false;
        }
    });
}

// Return joystick handle to center position
function returnJoystickToCenter(handle) {
    // Animate the handle back to center
    handle.style.transition = 'top 0.3s, left 0.3s';
    handle.style.left = '33%';
    handle.style.top = '33%';
    
    // Remove transition after animation completes
    setTimeout(() => {
        handle.style.transition = '';
    }, 300);
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
        targetAngles.channel0 = xAngle;
        targetAngles.channel1 = yAngle;
        
        // Update sliders
        document.getElementById('channel0').value = xAngle;
        document.getElementById('channel1').value = yAngle;
        document.getElementById('angle0').textContent = `${xAngle}°`;
        document.getElementById('angle1').textContent = `${xAngle}°`;
    } else {
        // Right joystick: Y controls channel2, X controls channel3
        targetAngles.channel2 = yAngle;
        targetAngles.channel3 = xAngle;
        
        // Update sliders
        document.getElementById('channel2').value = yAngle;
        document.getElementById('channel3').value = xAngle;
        document.getElementById('angle2').textContent = `${yAngle}°`;
        document.getElementById('angle3').textContent = `${xAngle}°`;
    }
    
    // Start animation to the target position
    if (!animationInProgress) {
        animateToTarget();
    }
}

// Initialize slider controls
function initSliders() {
    for (let i = 0; i < 4; i++) {
        const slider = document.getElementById(`channel${i}`);
        const display = document.getElementById(`angle${i}`);
        
        slider.addEventListener('input', function() {
            const value = parseInt(this.value);
            display.textContent = `${value}°`;
            
            // Set as target angle
            targetAngles[`channel${i}`] = value;
            
            // Start animation to the target position
            if (!animationInProgress) {
                animateToTarget();
            }
        });
    }
}

// Initialize preset buttons and new functionality
function initButtons() {
    // Reset button
    document.getElementById('reset-button').addEventListener('click', () => {
        clearInterval(randomMovementInterval); // Stop any random movement
        clearTimeout(holdTimeout); // Clear any hold timeout
        document.getElementById('random-button').textContent = "Random Movement";
        
        // Reset to initial positions
        targetAngles = { channel0: 135, channel1: 135, channel2: 135, channel3: 135 };
        
        // Update UI
        updateUIFromServoAngles(targetAngles);
        
        // Start animation to the target position
        if (!animationInProgress) {
            animateToTarget();
        }
    });
    
    // Random movement button - IMPROVED for more fluid motion and pausing
    document.getElementById('random-button').addEventListener('click', () => {
        // If already running, stop it
        if (randomMovementInterval) {
            clearInterval(randomMovementInterval);
            clearTimeout(holdTimeout);
            randomMovementInterval = null;
            document.getElementById('random-button').textContent = "Random Movement";
            return;
        }
        
        // Start random movement
        document.getElementById('random-button').textContent = "Stop Random";
        
        let count = 0;
        const maxPositions = 10;
        
        // Function to generate and animate to next random position
        function nextRandomPosition() {
            // Generate random positions for all servos
            targetAngles = {
                channel0: Math.floor(Math.random() * 271),
                channel1: Math.floor(Math.random() * 271),
                channel2: Math.floor(Math.random() * 271),
                channel3: Math.floor(Math.random() * 271)
            };
            
            // Update UI
            updateUIFromServoAngles(targetAngles);
            
            // Start animation to the target position
            if (!animationInProgress) {
                animateToTarget();
            }
            
            // Hold at position for 1 second before next move
            holdTimeout = setTimeout(() => {
                count++;
                if (count >= maxPositions) {
                    clearInterval(randomMovementInterval);
                    randomMovementInterval = null;
                    document.getElementById('random-button').textContent = "Random Movement";
                } else {
                    nextRandomPosition();
                }
            }, HOLD_DURATION);
        }
        
        // Start the first random position
        nextRandomPosition();
    });
    
    // Preset position buttons
    document.getElementById('preset-left').addEventListener('click', () => {
        clearInterval(randomMovementInterval); // Stop any random movement
        clearTimeout(holdTimeout); // Clear any hold timeout
        document.getElementById('random-button').textContent = "Random Movement";
        
        // Set to left position (0 degrees for all servos)
        targetAngles = { channel0: 0, channel1: 0, channel2: 0, channel3: 0 };
        
        // Update UI
        updateUIFromServoAngles(targetAngles);
        
        // Start animation to the target position
        if (!animationInProgress) {
            animateToTarget();
        }
    });
    
    document.getElementById('preset-center').addEventListener('click', () => {
        clearInterval(randomMovementInterval); // Stop any random movement
        clearTimeout(holdTimeout); // Clear any hold timeout
        document.getElementById('random-button').textContent = "Random Movement";
        
        // Set to center position (135 degrees for all servos)
        targetAngles = { channel0: 135, channel1: 135, channel2: 135, channel3: 135 };
        
        // Update UI
        updateUIFromServoAngles(targetAngles);
        
        // Start animation to the target position
        if (!animationInProgress) {
            animateToTarget();
        }
    });
    
    document.getElementById('preset-right').addEventListener('click', () => {
        clearInterval(randomMovementInterval); // Stop any random movement
        clearTimeout(holdTimeout); // Clear any hold timeout
        document.getElementById('random-button').textContent = "Random Movement";
        
        // Set to right position (270 degrees for all servos)
        targetAngles = { channel0: 270, channel1: 270, channel2: 270, channel3: 270 };
        
        // Update UI
        updateUIFromServoAngles(targetAngles);
        
        // Start animation to the target position
        if (!animationInProgress) {
            animateToTarget();
        }
    });
    
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme');
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
        
        // Update scene background
        updateSceneBackground();
    });
}

// Update UI elements from servoAngles object
function updateUIFromServoAngles(angles = servoAngles) {
    for (let i = 0; i < 4; i++) {
        const channel = `channel${i}`;
        document.getElementById(channel).value = Math.round(angles[channel]);
        document.getElementById(`angle${i}`).textContent = `${Math.round(angles[channel])}°`;
    }
}

// Send servo updates to server
function sendServoUpdate() {
    // Create a copy with rounded values
    const roundedAngles = {};
    for (const channel in servoAngles) {
        roundedAngles[channel] = Math.round(servoAngles[channel]);
    }
    
    fetch('/api/servo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(roundedAngles)
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
        targetAngles = { ...data }; // Copy initial values to targetAngles
        
        // Update sliders
        updateUIFromServoAngles();
        
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
    initButtons(); // Initialize new functionality
    fetchInitialPositions();
    
    // Start MPU6050 continuous updates
    mpuUpdateInterval = setInterval(updateMPUData, 100); // Update MPU data 10 times per second
});
