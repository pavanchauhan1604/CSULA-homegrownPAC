#!/bin/bash
# Send Email Reports (Interactive)
# This script runs the Python email sender in interactive mode

# Change to project directory
cd "$(dirname "$0")/.."

# Determine Python executable
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_CMD=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "🚀 Starting Email Sender..."
echo "Using Python: $PYTHON_CMD"
"$PYTHON_CMD" scripts/send_emails.py
