#!/bin/bash

# Test script for robot arm app
echo "Testing Robot Arm Virtual UI..."

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Test imports
echo "Testing Python imports..."
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import flask
    print(f'✓ Flask version: {flask.__version__}')
except ImportError as e:
    print(f'✗ Flask import failed: {e}')
    sys.exit(1)

try:
    import werkzeug
    print(f'✓ Werkzeug version: {werkzeug.__version__}')
except ImportError as e:
    print(f'✗ Werkzeug import failed: {e}')
    sys.exit(1)

try:
    from flask import Flask, render_template, jsonify, request
    print('✓ All Flask components imported successfully')
except ImportError as e:
    print(f'✗ Flask component import failed: {e}')
    sys.exit(1)

print('✓ All tests passed!')
"

echo "Test completed."
