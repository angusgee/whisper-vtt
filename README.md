# WhisperVTT

A custom Linux utility which provides a fast, hotkey-activated voice-to-text solution using OpenAI's Whisper model.

## Overview

This project provides a streamlined workflow for converting spoken audio into text directly on a Linux desktop. It was developed to offer a more integrated and efficient alternative to web-based or heavier dictation software. By leveraging the power of OpenAI's Whisper model locally, it allows for quick transcription triggered by a simple hotkey press, with the resulting text automatically pasted into the active application.

## Features

*   **Hotkey Activated:** Start recording instantly with a configurable global hotkey.
*   **Whisper AI Integration:** Utilizes OpenAI's powerful Whisper model for accurate speech-to-text transcription.
*   **Local Processing:** Runs entirely locally, ensuring privacy and offline capability (after model download).
*   **Automatic Pasting:** Transcribed text is automatically pasted into the currently focused window using `xdotool`.
*   **Clipboard Fallback:** Text is also copied to the clipboard using `pyperclip`.
*   **Hardware Targeting:** Attempts to automatically detect and use a specific microphone (e.g., "Poly Blackwire") for optimal input, falling back to the default device if necessary.
*   **Optimized Model Loading:** Configured to use a specific Whisper model size (currently 'small') for a balance between speed and accuracy. Supports CUDA acceleration if a compatible GPU is detected.
*   **Virtual Environment:** Uses a Python virtual environment for clean dependency management.

## Technology Stack

*   **Core Logic:** Python 3
*   **Speech Recognition:** OpenAI Whisper
*   **Machine Learning Framework:** PyTorch (Whisper dependency, handles CPU/GPU execution)
*   **Audio Handling:** `sounddevice` (recording), `soundfile` (saving WAV)
*   **Clipboard:** `pyperclip`
*   **Automation:** `xdotool` (for pasting)
*   **Shell Scripting:** Bash (for wrapper script)

## Workflow

The process from voice input to text output is as follows:

1.  **Hotkey Trigger:** The user presses the configured global hotkey (e.g., F8).
2.  **Shell Script Execution:** The hotkey binding executes the `whisper_vtt.sh` script.
3.  **Environment Activation:** `whisper_vtt.sh` activates the project's Python virtual environment (`venv`).
4.  **Python Script Launch:** The main `whisper_vtt.py` script is executed.
5.  **Initialization:**
    *   The script detects if a CUDA-enabled GPU is available and selects it, otherwise defaults to CPU.
    *   It loads the pre-configured Whisper model (e.g., 'small') into memory using `whisper.load_model()`.
    *   It searches for the preferred audio input device ("Poly Blackwire") using `sounddevice` and selects it, otherwise uses the system default.
6.  **Recording:**
    *   A message "Recording... Press Ctrl+C to stop" is printed to the console where the script was launched (useful for debugging).
    *   Audio recording starts via `sounddevice.InputStream`. Volume feedback is printed to the console.
7.  **Stop Signal:** The user presses `Ctrl+C`.
8.  **Transcription:**
    *   A Python `signal_handler` catches the `SIGINT` (Ctrl+C) signal.
    *   Recording stops, and the captured audio data is saved as a temporary `.wav` file using `soundfile`.
    *   The `model.transcribe()` method processes the audio file.
9.  **Output Handling:**
    *   The transcribed text is extracted from the Whisper result.
    *   The text is copied to the system clipboard using `pyperclip`.
    *   The Python script prints the transcribed text and exits.
10. **Pasting:**
    *   Control returns to `whisper_vtt.sh`.
    *   `xdotool key ctrl+v` is executed, simulating a paste action in the currently active window.
11. **Cleanup:** The temporary audio file is deleted.

## AI Integration Details (Whisper)

This tool's core intelligence comes from OpenAI's Whisper, a state-of-the-art automatic speech recognition (ASR) model.

*   **Model:** Utilizes the official `openai-whisper` Python package.
*   **Model Selection:** The script is currently configured to load the `'small'` model (`whisper.load_model('small')`). This choice prioritizes faster loading times compared to larger models like `'medium'`, albeit potentially with slightly lower accuracy. The original code included logic to select `'medium'` or `'small'` based on available GPU VRAM, which could be re-enabled for dynamic selection. The model files are cached locally (typically in `~/.cache/whisper/`) after the first download.
*   **Execution Backend:** Leverages PyTorch for computation. It automatically utilizes an available NVIDIA GPU via CUDA for significantly faster processing if `torch.cuda.is_available()` returns true. Otherwise, it falls back to CPU execution.
*   **Transcription Process:** The core transcription occurs when `model.transcribe(audio_file_path)` is called, passing the path to the temporarily saved `.wav` recording.

## Setup / Installation

1.  **Prerequisites:**
    *   Linux Operating System
    *   Python 3.8+ and `pip`
    *   `python3-venv` (usually installed via `sudo apt update && sudo apt install python3-venv` on Debian/Ubuntu)
    *   `portaudio` development libraries (required by `sounddevice`):
        ```bash
        sudo apt update && sudo apt install portaudio19-dev
        ```
    *   `xdotool` (for automatic pasting):
        ```bash
        sudo apt update && sudo apt install xdotool
        ```
2.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url> vtt-tool
    cd vtt-tool
    ```
3.  **Create Virtual Environment:**
    ```bash
    python3 -m venv venv
    ```
4.  **Activate Environment:**
    ```bash
    source venv/bin/activate
    ```
    *(Note: You'll need to activate the environment in each new terminal session before running the scripts directly, although the `whisper_vtt.sh` wrapper handles this automatically when run via hotkey).*
5.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(We will create `requirements.txt` next).*
6.  **Download Whisper Model:** Pre-download the desired model to avoid delays on first use. Use the included script:
    ```bash
    python scripts/download_model.py --model small
    ```
    *(Replace `small` with `tiny`, `base`, `medium`, or `large` if you modify `whisper_vtt.py` later).*
7.  **Configure Hotkey:**
    *   Set up a global keyboard shortcut in your Linux desktop environment (e.g., KDE System Settings -> Shortcuts, GNOME Settings -> Keyboard -> Keyboard Shortcuts -> Custom Shortcuts).
    *   Assign an unused key combination (like F8).
    *   Set the command/action to execute the *full path* to the `whisper_vtt.sh` script:
        `/home/loop/vtt-tool/whisper_vtt.sh` *(Adjust the path if you cloned it elsewhere)*.

## Usage

1.  Ensure no conflicting application is using the chosen hotkey and that you have an application window ready to receive the pasted text.
2.  Press the configured global hotkey (e.g., F8).
3.  A new terminal opens and recording starts momentarily, shown by the volume indicator like `Volume: 15.23 |||||||||||||||`. Start speaking clearly.
4.  When finished speaking, press `Ctrl+C`. This signal stops the recording and initiates transcription.
5.  The terminal closes and the script will process the audio using the Whisper model.
6.  The transcribed text will be copied to the system clipboard.

## Customization

*   **Whisper Model Size:** Edit `whisper_vtt.py` and change the `model_name = "small"` line (around line 129) to `"tiny"`, `"base"`, `"medium"`, etc. Remember to download the corresponding model using `scripts/download_model.py`.
*   **Audio Input Device:** Modify the string `"Poly Blackwire"` in the `__init__` method of the `VoiceToText` class in `whisper_vtt.py` (around line 27) to match the name (or part of the name) of your preferred microphone as listed by audio utilities.
*   **Hotkey:** Change the hotkey binding in your desktop environment's settings.
*   **Paste Keystroke:** If `Ctrl+V` isn't the correct paste command for some specific application, modify the `xdotool key ctrl+v` line in `whisper_vtt.sh`.
