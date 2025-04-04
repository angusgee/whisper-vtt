#!/bin/bash

# activate venv, run script and pass args directly
source ~/vtt-tool/venv/bin/activate
python ~/vtt-tool/whisper_vtt.py "$@"

# Simulate Ctrl+V after the python script exits
xdotool key ctrl+v

