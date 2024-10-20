import os
import sys
import ctypes
import threading
import recorder
import transcriber
from gui import SubtitleGUI
import queue
import time
import argparse
import configparser

# Update the import statement for the GUI
from gui import SubtitleGUI  # No change needed

# Add the specific path to cudnn_ops_infer64_8.dll to the PATH and sys.path
cuda_dll_path = r"C:\dev\TranscriberX\nvidia_dependencies"
os.environ['PATH'] = f"{cuda_dll_path}{os.pathsep}{os.environ['PATH']}"
sys.path.append(cuda_dll_path)

# Explicitly add the DLL to the DLL search path
os.add_dll_directory(cuda_dll_path)

try:
    ctypes.CDLL(os.path.join(cuda_dll_path, "cudnn_ops_infer64_8.dll"))
    print("Successfully loaded cudnn_ops_infer64_8.dll", flush=True)
except Exception as e:
    print(f"Error loading cudnn_ops_infer64_8.dll: {e}", flush=True)

def start_recording():
    """Start the audio recording process."""
    recorder.record_audio()

def start_transcription(device):
    """Start the audio transcription process."""
    transcriber.monitor_audio_file(
        transcriber.AUDIO_INPUT_DIR,
        transcriber.TRANSCRIPTION_OUTPUT,
        check_interval=0.2,
        device=device
    )

def start_gui(update_queue, intelligent_mode):
    """Start the GUI for displaying subtitles."""
    gui = SubtitleGUI(update_queue, intelligent_mode)
    gui.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TranscriberX Application")
    parser.add_argument('--intelligent', action='store_true', help='Enable intelligent mode')
    parser.add_argument('--cuda', action='store_true', help='Enable CUDA for transcription')
    parser.add_argument('--model', type=str, choices=['tiny', 'base', 'small', 'medium', 'large'], 
                        help='Select the model size for transcription')
    args = parser.parse_args()

    # Update config with the selected model
    config = configparser.ConfigParser()
    config.read('config.ini')
    if args.model:
        config['Settings']['model'] = args.model
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    # Create a queue for GUI updates
    transcription_queue = transcriber.transcription_queue

    # Determine device based on '--cuda' flag
    device = "cuda" if args.cuda else "cpu"

    # Create threads for recording, transcription, and GUI
    recording_thread = threading.Thread(target=start_recording, daemon=True)
    transcription_thread = threading.Thread(target=start_transcription, args=(device,), daemon=True)
    gui_thread = threading.Thread(target=start_gui, args=(transcription_queue, args.intelligent), daemon=True)

    # Start the threads
    recording_thread.start()
    transcription_thread.start()
    gui_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting program.", flush=True)
