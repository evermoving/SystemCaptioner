import pyaudiowpatch as pyaudio
import wave
import time
import threading

# Constants
CHUNK = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 2  # Stereo
RATE = 44100  # 44.1kHz sampling rate
RECORD_SECONDS = 5  # Record in 3-second intervals
WAVE_OUTPUT_FILENAME = "debug.wav"

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

def record_audio():
    """Record audio from the default speaker and save it to a file."""
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

                # Start a new thread to save the audio
                threading.Thread(target=save_audio, args=(frames, WAVE_OUTPUT_FILENAME)).start()

if __name__ == "__main__":
    record_audio()
