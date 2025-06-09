#!/bin/bash
# check_mpu6050.sh - Check MPU6050 Monitor health

echo "Checking MPU6050 Monitor health..."

# Check I2C connection
echo "Checking I2C connection to MPU6050..."
if which i2cdetect >/dev/null; then
    i2cdetect -y 1 | grep -q "68" && echo "MPU6050 found on I2C bus" || echo "WARNING: MPU6050 not detected on I2C bus"
else
    echo "i2cdetect not found, skipping I2C check"
fi

# Check if web server is running
echo "Checking web server..."
curl -s http://localhost:5000 > /dev/null && echo "Web server is running" || echo "WARNING: Web server is not responding"

# Check API endpoint
echo "Checking API endpoints..."
curl -s http://localhost:5000/api/v1/data > /dev/null && echo "API /data endpoint is responding" || echo "WARNING: API /data endpoint is not responding"
curl -s http://localhost:5000/api/v1/log > /dev/null && echo "API /log endpoint is responding" || echo "WARNING: API /log endpoint is not responding"

# Check log file
echo "Checking log file..."
if [ -f "web_server.log" ]; then
    tail -5 web_server.log
    grep -q "ERROR" web_server.log && echo "WARNING: Errors found in log file" || echo "No recent errors in log file"
else
    echo "WARNING: web_server.log not found"
fi

echo "Health check complete"
