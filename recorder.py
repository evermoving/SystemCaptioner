import pyaudiowpatch as pyaudio
import wave
import time
import threading
import os

# Constants
CHUNK = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 2  # Stereo
RATE = 44100  # 44.1kHz sampling rate
RECORD_SECONDS = 3  # Record in 2-second intervals
OUTPUT_DIR = "recordings"  # Directory to save recordings
MAX_FILES = 10  # Maximum number of files to keep

def get_default_loopback_device(p):
    """Get the default loopback device."""
    return p.get_default_wasapi_loopback()

def save_audio(frames, filename):
    """Save the recorded audio frames to a WAV file."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def cleanup_old_files():
    """Delete old WAV files, keeping only the most recent MAX_FILES."""
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.wav')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
    
    for old_file in files[MAX_FILES:]:
        os.remove(os.path.join(OUTPUT_DIR, old_file))
        print(f"Deleted old file: {old_file}")

def record_audio():
    """Record audio from the default speaker and save it to a file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with pyaudio.PyAudio() as p:
        # Get the default loopback device
        loopback_device = get_default_loopback_device(p)
        
        # Open the stream
        with p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=loopback_device['index']) as stream:
            
            while True:
                print("Recording...")
                frames = []

                # Record for the specified duration
                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)

                print("Finished recording.")

                # Generate a unique filename
                filename = os.path.join(OUTPUT_DIR, f"recording_{int(time.time())}.wav")

                # Start a new thread to save the audio
                threading.Thread(target=save_audio, args=(frames, filename)).start()
                
                # Clean up old files after saving new recording
                cleanup_old_files()

if __name__ == "__main__":
    record_audio()
