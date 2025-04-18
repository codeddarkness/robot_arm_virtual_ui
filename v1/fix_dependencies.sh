#!/bin/bash

# Fix dependencies script for Robot Arm Virtual UI
# This script fixes the package version conflicts

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Fixing package dependencies for Robot Arm Virtual UI...${NC}"

# Determine the activation command based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    ACTIVATE_CMD="source venv/Scripts/activate"
else
    # Linux/Mac
    ACTIVATE_CMD="source venv/bin/activate"
fi

# Create updated requirements file
echo "Creating updated requirements.txt file..."
cat > requirements.txt << 'EOF'
Flask==2.0.1
Werkzeug==2.0.1
Jinja2==3.0.1
itsdangerous==2.0.1
click==8.0.1
MarkupSafe==2.0.1
EOF
echo -e "${GREEN}✓ Updated requirements.txt with compatible versions${NC}"

# Activate the virtual environment and reinstall packages
echo "Reinstalling dependencies with correct versions..."
$ACTIVATE_CMD

python -m pip uninstall -y Flask Werkzeug Jinja2 itsdangerous click MarkupSafe
python -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install dependencies. Try manually:${NC}"
    echo "   $ACTIVATE_CMD"
    echo "   python -m pip uninstall -y Flask Werkzeug Jinja2 itsdangerous click MarkupSafe"
    echo "   python -m pip install -r requirements.txt"
else
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
fi

echo ""
echo -e "${GREEN}Fix complete!${NC}"
echo ""
echo "To run the application:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  $ACTIVATE_CMD"
echo "  python robot_arm_app.py"
