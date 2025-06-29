#!/bin/bash

# Log file for the restart process
LOG_FILE="restart.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create or clear log file
> "$LOG_FILE"

log "Starting application restart process..."

# Find and kill existing process
PID=$(pgrep -f "uvicorn main:app")
if [ -n "$PID" ]; then
    log "Found existing process with PID: $PID. Stopping..."
    kill $PID
    sleep 2

    # Check if process is still running and force kill if necessary
    if ps -p $PID > /dev/null; then
        log "Process still running. Force killing..."
        kill -9 $PID
        sleep 1
    fi

    log "Previous process stopped."
else
    log "No existing process found."
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    log "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    log "Activating virtual environment..."
    source .venv/bin/activate
fi

# Start the application
log "Starting the application..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > app.log 2>&1 &

NEW_PID=$!
log "Application started with PID: $NEW_PID"

# Wait a moment and check if the process is running
sleep 2
if ps -p $NEW_PID > /dev/null; then
    log "Application is running successfully."
    echo "✅ Application restarted successfully (PID: $NEW_PID)"
else
    log "ERROR: Application failed to start. Check app.log for details."
    echo "❌ Failed to restart application. See restart.log and app.log for details."
    exit 1
fi

# Make the script print the URL where the application is accessible
echo "🚀 Application running at: http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/docs"