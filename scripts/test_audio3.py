#!/usr/bin/env python3
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import time

# Use device 7 explicitly (Poly Blackwire 3320 Series)
device = 7
device_info = sd.query_devices(device)
print(f"Using device {device}: {device_info['name']}")

# Use the default sample rate that the device supports
fs = int(device_info['default_samplerate'])
print(f"Using device's default sample rate: {fs}Hz")

# Record settings
duration = 5  # seconds
channels = 1

# Start with a countdown
print("Preparing to record in...")
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

print(f"Recording {duration} seconds - SPEAK NOW")
print("=" * 40)

# Record with volume monitoring
recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, 
                   device=device, blocking=False)

# Monitor volume while recording
start_time = time.time()
while time.time() - start_time < duration:
    current_samples = int((time.time() - start_time) * fs)
    if current_samples > 0:
        current_audio = recording[:current_samples]
        volume_norm = np.linalg.norm(current_audio) * 10
        bars = int(volume_norm)
        print(f"Volume: {volume_norm:.2f} {'|' * bars}", end="\r")
    time.sleep(0.1)

sd.wait()  # Wait until recording is finished
print("\nRecording finished")

# Save to file
output_file = os.path.expanduser("~/vtt-tool/test_audio3.wav")
sf.write(output_file, recording, fs)

file_size = os.path.getsize(output_file)
print(f"Recording saved to {output_file} ({file_size} bytes)")

# Check recording stats
max_amplitude = np.max(np.abs(recording))
mean_amplitude = np.mean(np.abs(recording))
print(f"Max amplitude: {max_amplitude:.6f}")
print(f"Mean amplitude: {mean_amplitude:.6f}")

if mean_amplitude > 0.001:
    print("Audio detected in recording")
else:
    print("Recording seems to be silent or very quiet")
    
print("\nTrying to play back the recording...")
sd.play(recording, fs)
sd.wait()
