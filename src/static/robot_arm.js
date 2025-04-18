// Robot Arm Virtual UI v0.2.3-1

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
    scene.background = new THREE.Color(0xf5f5f5);
    
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
