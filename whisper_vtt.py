#!/usr/bin/env python3
import os
import sys
import tempfile
import signal
import time
import whisper
import torch
import sounddevice as sd
import soundfile as sf
import numpy as np
import pyperclip

class VoiceToText:
    def __init__(self, model_name="medium"):
        print("Initializing Whisper model...")
        self.model = whisper.load_model(model_name)
        print(f"Model {model_name} loaded successfully")
        self.temp_dir = tempfile.mkdtemp()
        self.recording = False
        self.audio_file = os.path.join(self.temp_dir, "recording.wav")
        
        # Find the Poly Blackwire headset
        self.device = None
        self.fs = 16000  # Default sample rate
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if "Poly Blackwire" in device['name']:
                self.device = i
                self.fs = int(device['default_samplerate'])
                print(f"Found Poly Blackwire headset at device {i}, using sample rate {self.fs}Hz")
                break
        
        if self.device is None:
            print("Could not find Poly Blackwire headset, using default device")
            self.device = None  # Use default device
        
    def start_recording(self):
        print("Recording... Press Ctrl+C to stop")
        self.recording = True
        self.recorded_frames = []
        
        # Start recording thread
        self.recording_thread = sd.InputStream(
            samplerate=self.fs,
            device=self.device,
            channels=1,
            callback=self._audio_callback
        )
        self.recording_thread.start()
        print(f"Started recording from device {self.device}")
        
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
        if self.recording:
            self.recorded_frames.append(indata.copy())
            # Calculate volume for feedback
            volume_norm = np.linalg.norm(indata) * 10
            bars = int(volume_norm)
            print(f"Volume: {volume_norm:.2f} {'|' * bars}", end="\r")
            
    def stop_recording(self):
        if self.recording:
            self.recording = False
            if hasattr(self, 'recording_thread'):
                self.recording_thread.stop()
                self.recording_thread.close()
            
            print("\nRecording stopped")
            
            # Combine recorded frames and save to file
            if self.recorded_frames:
                recording = np.concatenate(self.recorded_frames, axis=0)
                sf.write(self.audio_file, recording, self.fs)
                file_size = os.path.getsize(self.audio_file)
                print(f"Saved recording to {self.audio_file} ({file_size} bytes)")
                return True
            else:
                print("No audio data recorded")
                return False
        return False
    
    def transcribe(self):
        if not os.path.exists(self.audio_file):
            print("No recording found")
            return ""
            
        file_size = os.path.getsize(self.audio_file)
        if file_size == 0:
            print("Recording is empty")
            return ""
            
        print(f"Transcribing audio file: {self.audio_file} ({file_size} bytes)")
        try:
            result = self.model.transcribe(self.audio_file, language="en")
            transcribed_text = result["text"].strip()
            print(f"Transcribed: {transcribed_text}")
            return transcribed_text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
    
    def cleanup(self):
        try:
            os.remove(self.audio_file)
        except:
            pass

def signal_handler(sig, frame):
    print("\nStopping...")
    if vtt.recording:
        vtt.stop_recording()
        text = vtt.transcribe()
        if text:
            pyperclip.copy(text)
            print(f"Copied to clipboard: {text}")
        else:
            print("No text transcribed or copied.")
    vtt.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # Use GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Set 'tiny' model for faster loading
    model_name = "tiny"
    
    print(f"Selected model: {model_name}")
    vtt = VoiceToText(model_name=model_name)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    vtt.start_recording()
    
    # Keep the script running until Ctrl+C
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
