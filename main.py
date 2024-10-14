import os
import sys

# Add the specific path to cudnn_ops_infer64_8.dll to the PATH and sys.path
cuda_dll_path = r"C:\dev\TranscriberX\nvidia_dependencies"
os.environ['PATH'] = f"{cuda_dll_path}{os.pathsep}{os.environ['PATH']}"
sys.path.append(cuda_dll_path)

# Explicitly add the DLL to the DLL search path
os.add_dll_directory(cuda_dll_path)

import ctypes
try:
    ctypes.CDLL(os.path.join(cuda_dll_path, "cudnn_ops_infer64_8.dll"))
    print("Successfully loaded cudnn_ops_infer64_8.dll")
except Exception as e:
    print(f"Error loading cudnn_ops_infer64_8.dll: {e}")

import threading
import recorder
import transcriber

def start_recording():
    """Start the audio recording process."""
    recorder.record_audio()

def start_transcription():
    """Start the audio transcription process."""
    transcriber.monitor_audio_file(
        transcriber.AUDIO_INPUT_DIR,
        transcriber.TRANSCRIPTION_OUTPUT,
        check_interval=1
    )

if __name__ == "__main__":
    # Create threads for recording and transcription
    recording_thread = threading.Thread(target=start_recording)
    transcription_thread = threading.Thread(target=start_transcription)

    # Start the threads
    recording_thread.start()
    transcription_thread.start()

    # Wait for both threads to complete
    recording_thread.join()
    transcription_thread.join()
