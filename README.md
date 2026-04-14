# WhisperVTT

A custom Linux utility which provides a fast, hotkey-activated voice-to-text solution using OpenAI's Whisper model.

## 🚧 To-Do / Future Improvements 🚧

*   **Automatic Audio Device Detection:** Currently, the script is hardcoded to look for a "Poly Blackwire" headset ([whisper_vtt.py#L27](cci:7://file:///home/loop/vtt-tool/whisper_vtt.py:27:0-27:0)). Future versions should automatically use the system default input device or allow user selection via configuration/arguments.

## Overview

WhisperVTT is a lightweight, local voice-to-text solution for Linux desktops. By harnessing OpenAI's powerful Whisper model, it quickly converts spoken audio into text, copying it to your clipboard with a single hotkey press. No internet access or third party software needed.

## Features

*   **Hotkey Activated:** Start recording instantly with a configurable global hotkey.
*   **Whisper AI Integration:** Uses OpenAI's powerful Whisper model for accurate speech-to-text transcription.
*   **Local Processing:** Runs entirely locally, ensuring privacy and offline capability (after model download).
*   **Clipboard Fallback:** Text is copied to the clipboard using `pyperclip`.
*   **Hardware Targeting:** Attempts to automatically detect and use a specific microphone (e.g., "Poly Blackwire") for optimal input, falling back to the default device if necessary.
*   **Persistent Daemon:** The Whisper model loads once and stays in memory. Subsequent recordings start instantly with no model loading delay.
*   **Desktop Notifications:** All feedback (recording status, transcription results) delivered via desktop notifications — no terminal window needed.
*   **Optimized Model Loading:** Configurable Whisper model size (default 'base'). Supports CUDA acceleration if a compatible GPU is detected.
*   **Virtual Environment:** Uses `uv` for fast, reproducible dependency management.

## Technology Stack

*   **Core Logic:** Python 3
*   **Speech Recognition:** OpenAI Whisper
*   **Machine Learning Framework:** PyTorch (Whisper dependency, handles CPU/GPU execution)
*   **Audio Handling:** `sounddevice` (recording), `soundfile` (saving WAV)
*   **Clipboard:** `pyperclip`
*   **Notifications:** `notify-send` (desktop notifications)
*   **Automation:** `xdotool` (for auto-pasting)

## Workflow

The script runs as a persistent background daemon with a toggle hotkey:

1.  **First Hotkey Press:** If the daemon is not running, it starts in the background, loads the Whisper model into memory, and shows a "WhisperVTT ready" notification. Subsequent presses toggle recording.
2.  **Hotkey Press (start recording):** A `SIGUSR1` signal toggles the daemon into recording mode. A "Recording..." notification appears.
3.  **Hotkey Press (stop recording):** Another `SIGUSR1` signal stops the recording. The audio is transcribed, the text is copied to the clipboard, and `xdotool` simulates `Ctrl+V` to paste it into the active window. A notification shows a preview of the transcribed text.
4.  **Daemon stays alive:** The model remains loaded in memory (GPU/CPU). The next recording starts instantly with no loading delay.
5.  **Shutdown:** Sending `SIGINT` or `SIGTERM` to the daemon process cleanly shuts it down.

## AI Integration Details (Whisper)

This tool's core intelligence comes from OpenAI's Whisper, a state-of-the-art automatic speech recognition (ASR) model.

*   **Model:** Utilizes the official `openai-whisper` Python package.
*   **Model Selection:** The script is currently configured to load the `'small'` model (`whisper.load_model('small')`). This choice prioritizes faster loading times compared to larger models like `'medium'`, albeit potentially with slightly lower accuracy. The original code included logic to select `'medium'` or `'small'` based on available GPU VRAM, which could be re-enabled for dynamic selection. The model files are cached locally (typically in `~/.cache/whisper/`) after the first download.
*   **Execution Backend:** Leverages PyTorch for computation. It automatically utilizes an available NVIDIA GPU via CUDA for significantly faster processing if `torch.cuda.is_available()` returns true. Otherwise, it falls back to CPU execution.
*   **Transcription Process:** The core transcription occurs when `model.transcribe(audio_file_path)` is called, passing the path to the temporarily saved `.wav` recording.

## Setup / Installation

1.  **Prerequisites:**
    *   Linux Operating System
    *   Python 3.10+
    *   [`uv`](https://docs.astral.sh/uv/) (install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)
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
3.  **Install Dependencies:**
    ```bash
    uv sync
    ```
    This creates the virtual environment and installs all dependencies automatically.
4.  **Download Whisper Model:** Pre-download the desired model to avoid delays on first use. Use the included script:
    ```bash
    uv run python scripts/download_model.py --model small
    ```
    *(Replace `small` with `tiny`, `base`, `medium`, or `large` if you modify `whisper_vtt.py` later).*
5.  **Configure Hotkey:**
    *   Set up a global keyboard shortcut in your Linux desktop environment (e.g., KDE System Settings -> Shortcuts -> Custom Shortcuts).
    *   Assign an unused key combination (e.g., `Meta+S`).
    *   Set the command to:
        `uv run --project /path/to/vtt-tool /path/to/vtt-tool/whisper_vtt.py` *(Adjust the path to your clone location)*.

## Usage

1.  Press the configured global hotkey (e.g., `Meta+S`).
2.  On first press, the daemon starts and loads the Whisper model. A "WhisperVTT ready" notification appears.
3.  Press the hotkey again to start recording. A "Recording..." notification appears. Start speaking clearly.
4.  Press the hotkey again to stop recording. The audio is transcribed, copied to the clipboard, and auto-pasted into the active window.
5.  Subsequent recordings start instantly — the model stays loaded in memory.

## Customization

*   **Whisper Model Size:** Edit `whisper_vtt.py` and change the `model_name = "base"` line in the `run_daemon()` function to `"tiny"`, `"small"`, `"medium"`, etc. Remember to download the corresponding model using `scripts/download_model.py`.
*   **Audio Input Device:** Modify the string `"Poly Blackwire"` in the `__init__` method of the `VoiceToText` class in `whisper_vtt.py` to match the name (or part of the name) of your preferred microphone.
*   **Hotkey:** Change the hotkey binding in your desktop environment's settings.
*   **Auto-paste:** If `Ctrl+V` isn't the correct paste command for a specific application, modify the `xdotool` call in the `paste_clipboard()` function in `whisper_vtt.py`.

