#!/usr/bin/env python3
import whisper
import torch
import argparse

def main():
    parser = argparse.ArgumentParser(description="Download Whisper model")
    parser.add_argument("--model", type=str, default="medium", 
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Model size to download")
    args = parser.parse_args()
    
    print(f"Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"Available VRAM: {vram_gb:.2f} GB")
    
    print(f"Downloading '{args.model}' Whisper model...")
    model = whisper.load_model(args.model)
    print(f"Model '{args.model}' downloaded successfully to the cache.")
    print(f"Cache location: ~/.cache/whisper/")

if __name__ == "__main__":
    main()