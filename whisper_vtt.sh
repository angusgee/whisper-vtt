#!/bin/bash

# Find the PID of the running whisper_vtt.py process
PID=$(pgrep -f "python.*/whisper_vtt.py")

if [ -n "$PID" ]; then
    # If process is running, send SIGINT to stop it
    echo "Stopping existing whisper_vtt.py process (PID: $PID)"
    kill -SIGINT $PID
else
    # If process is not running, start it
    echo "Starting Whisper Voice-to-Text..."
    # Activate venv and run Python script
    source ~/vtt-tool/venv/bin/activate
    python ~/vtt-tool/whisper_vtt.py "$@"
    
    # Simulate Ctrl+V after the python script exits
    # (This happens when the user presses F8 again to stop)
fi
