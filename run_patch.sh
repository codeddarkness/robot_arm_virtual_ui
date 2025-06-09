#!/bin/bash

# Fix Flask/Werkzeug compatibility issue

echo "Fixing Flask/Werkzeug compatibility issue..."

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Uninstall current packages
echo "Uninstalling current Flask and Werkzeug..."
pip uninstall -y Flask Werkzeug

# Update requirements.txt with compatible versions
echo "Updating requirements.txt with compatible versions..."
cat > requirements.txt << 'EOF'
Flask==2.3.2
Werkzeug==2.3.6
EOF

# Install compatible versions
echo "Installing compatible Flask and Werkzeug versions..."
pip install -r requirements.txt

# Verify installation
echo "Verifying installation..."
python -c "import flask; print(f'Flask version: {flask.__version__}')"
python -c "import werkzeug; print(f'Werkzeug version: {werkzeug.__version__}')"

echo "Fix applied. Try running the application again with:"
echo "  ./run.sh"
