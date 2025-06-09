#!/bin/bash

# Fix watchdog compatibility issue - comprehensive solution

echo "Fixing watchdog compatibility issue comprehensively..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

# Update requirements.txt with all compatible versions
cat > requirements.txt << 'EOF'
Flask==2.3.2
Werkzeug==2.3.6
watchdog==2.1.9
EOF

# Install/reinstall packages
echo "Installing compatible packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Packages updated. The application should now run with debug mode enabled."
echo ""
echo "To run the application:"
echo "  python3 robot_arm_app.py"
