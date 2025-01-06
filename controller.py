import os
import sys
import ctypes
import threading
import time
import argparse
import configparser

# Import necessary modules from the project
import recorder
import transcriber
from gui import SubtitleGUI

# Setup CUDA DLL path
cuda_dll_path = os.path.join(os.path.dirname(__file__), "nvidia_dependencies")
os.environ['PATH'] = f"{cuda_dll_path}{os.pathsep}{os.environ['PATH']}"
sys.path.append(cuda_dll_path)

# Add the DLL to the DLL search path
os.add_dll_directory(cuda_dll_path)

# Attempt to load the CUDA DLL
try:
    ctypes.CDLL(os.path.join(cuda_dll_path, "cudnn_ops_infer64_8.dll"))
    print("Successfully loaded cudnn_ops_infer64_8.dll", flush=True)
except Exception as e:
    print(f"Error loading cudnn_ops_infer64_8.dll: {e}", flush=True)

def start_recording(device_index=None):
    """Start the audio recording process."""
    recorder.record_audio(device_index)

def start_transcription(device, args):
    """Start the audio transcription process."""
    transcriber.monitor_audio_file(
        transcriber.AUDIO_INPUT_DIR,
        transcriber.TRANSCRIPTION_OUTPUT,
        check_interval=0.2,
        device=device,
        args=args
    )

def start_gui(update_queue, intelligent_mode):
    """Start the GUI for displaying subtitles."""
    gui = SubtitleGUI(update_queue, intelligent_mode)
    gui.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TranscriberX Application")
    parser.add_argument('--intelligent', action='store_true', help='Enable intelligent mode')
    parser.add_argument('--cuda', action='store_true', help='Enable CUDA for transcription')
    parser.add_argument('--model', type=str, choices=['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium',
                'large-v1', 'large-v2', 'large-v3', 'large', 'distil-large-v2', 'distil-medium.en',
                'distil-small.en', 'distil-large-v3'],
                        help='Select the model size for transcription')
    parser.add_argument('--device-index', type=int, help='Audio device index for recording')
    parser.add_argument('--transcription-timeout', type=int, default=5, help='Transcription timeout in seconds')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--translation-enabled', action='store_true', help='Enable translation')
    parser.add_argument('--source-language', type=str, default='en', help='Source language for transcription')
    parser.add_argument('--filter-hallucinations', action='store_true', help='Filter hallucinations using filter_hallucinations.txt')
    parser.add_argument('--store-output', action='store_true', help='Store transcription output in transcriptions.txt')
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
    recording_thread = threading.Thread(target=start_recording, args=(args.device_index,), daemon=True)
    transcription_thread = threading.Thread(target=start_transcription, args=(device, args), daemon=True)
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

