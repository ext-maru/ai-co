#!/bin/bash
# Start Flask app with Docker API support

cd /home/aicompany/ai_co

# Source environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "Starting Flask app with Docker API..."

# Check if Flask is already running
if lsof -i:5555 > /dev/null 2>&1; then
    echo "Flask app already running on port 5555"
    exit 1
fi

# Start Flask in development mode
export FLASK_APP=web/flask_app.py
export FLASK_ENV=development
export PYTHONPATH=/home/aicompany/ai_co:$PYTHONPATH

# Run Flask
python3 -m flask run --host=0.0.0.0 --port=5555 &

echo "Flask app started with PID: $!"
echo "Docker API available at: http://localhost:5555/api/docker"
echo "Dashboard available at: http://localhost:5555"

# Save PID
echo $! > flask_docker_api.pid

# Wait a moment for startup
sleep 3

# Test health endpoint
curl -s http://localhost:5555/api/docker/health | jq . || echo "Health check failed"