#!/usr/bin/env python3
import os
import sys
import tempfile
import signal
import subprocess
import time
import whisper
import torch
import sounddevice as sd
import soundfile as sf
import numpy as np
import pyperclip

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(PROJECT_DIR, ".whisper_vtt.pid")
LOG_FILE = os.path.join(PROJECT_DIR, "whisper_vtt.log")


def notify(summary, body="", urgency="normal", timeout=3000):
    """Send a desktop notification via notify-send."""
    cmd = [
        "notify-send",
        "--app-name=WhisperVTT",
        f"--urgency={urgency}",
        f"--expire-time={timeout}",
        summary,
    ]
    if body:
        cmd.append(body)
    try:
        subprocess.run(cmd, check=False, timeout=5)
    except Exception:
        pass


def log(msg):
    """Log to file and stdout (stdout useful when running interactively)."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def paste_clipboard():
    """Simulate Ctrl+V via xdotool after a brief delay."""
    time.sleep(0.3)
    try:
        subprocess.run(["xdotool", "key", "ctrl+v"], check=False, timeout=5)
    except FileNotFoundError:
        log("xdotool not found — text copied to clipboard but not auto-pasted")


def read_pid():
    """Read the PID from the PID file, return None if stale or missing."""
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        # Check if process is actually alive
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return None


def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


class VoiceToText:
    def __init__(self, model_name="base"):
        log(f"Loading Whisper model '{model_name}'...")
        self.model = whisper.load_model(model_name)
        log(f"Model '{model_name}' loaded successfully")
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
                log(f"Found Poly Blackwire headset at device {i}, sample rate {self.fs}Hz")
                break

        # Use default device if mine is not found
        if self.device is None:
            log("Poly Blackwire not found, using default input device")

    def start_recording(self):
        self.recording = True
        self.recorded_frames = []

        self.stream = sd.InputStream(
            samplerate=self.fs,
            device=self.device,
            channels=1,
            callback=self._audio_callback,
        )
        self.stream.start()
        log("Recording started")
        notify("Recording...", "Press hotkey again to stop")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            log(f"Audio status: {status}")
        if self.recording:
            self.recorded_frames.append(indata.copy())

    def stop_recording(self):
        if not self.recording:
            return False
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        if self.recorded_frames:
            recording = np.concatenate(self.recorded_frames, axis=0)
            sf.write(self.audio_file, recording, self.fs)
            file_size = os.path.getsize(self.audio_file)
            log(f"Saved recording ({file_size} bytes)")
            return True
        else:
            log("No audio data recorded")
            return False

    def transcribe(self):
        if not os.path.exists(self.audio_file):
            return ""

        file_size = os.path.getsize(self.audio_file)
        if file_size == 0:
            return ""

        log("Transcribing...")
        notify("Transcribing...", timeout=10000)
        try:
            # Use a Scottish accent prompt to improve transcription accuracy
            result = self.model.transcribe(
                self.audio_file,
                language="en",
                initial_prompt="This is a Scottish person speaking English with a Scottish accent.",
            )
            text = result["text"].strip()
            log(f"Transcribed: {text}")
            return text
        except Exception as e:
            log(f"Transcription error: {e}")
            return ""

    def cleanup(self):
        try:
            os.remove(self.audio_file)
        except FileNotFoundError:
            pass


# Global state
vtt = None


def handle_toggle(sig, frame):
    """SIGUSR1 handler: toggle recording on/off."""
    global vtt
    if vtt.recording:
        # Stop recording, transcribe, paste
        has_audio = vtt.stop_recording()
        if has_audio:
            text = vtt.transcribe()
            if text:
                pyperclip.copy(text)
                preview = text[:80] + ("..." if len(text) > 80 else "")
                notify("Copied to clipboard", preview)
                paste_clipboard()
            else:
                notify("No speech detected", urgency="low")
        else:
            notify("No audio recorded", urgency="low")
        vtt.cleanup()
    else:
        vtt.start_recording()


def handle_shutdown(sig, frame):
    """SIGINT/SIGTERM handler: clean shutdown."""
    global vtt
    log("Shutting down...")
    if vtt and vtt.recording:
        vtt.stop_recording()
    if vtt:
        vtt.cleanup()
    remove_pid()
    notify("WhisperVTT stopped")
    sys.exit(0)


def run_daemon():
    """Start the persistent daemon."""
    global vtt

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"Using device: {device}")

    # Configure model name here - tiny, base, medium, etc
    # Make sure to run scripts/download_model.py first
    model_name = "base"
    log(f"Selected model: {model_name}")

    vtt = VoiceToText(model_name=model_name)
    write_pid()

    signal.signal(signal.SIGUSR1, handle_toggle)
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    notify("WhisperVTT ready", f"Model '{model_name}' loaded on {device}")
    log("Daemon ready, waiting for signals...")

    # Keep the daemon alive
    while True:
        signal.pause()


def main():
    existing_pid = read_pid()

    if existing_pid:
        # Daemon is already running — send toggle signal
        log(f"Sending toggle signal to daemon (PID {existing_pid})")
        try:
            os.kill(existing_pid, signal.SIGUSR1)
        except ProcessLookupError:
            # Stale PID file
            remove_pid()
            log("Stale PID file removed, restarting daemon...")
            run_daemon()
    else:
        # No daemon running — become the daemon
        run_daemon()


if __name__ == "__main__":
    main()
