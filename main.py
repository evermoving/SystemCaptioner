import sounddevice as sd
import numpy as np
import wave
import time
import threading

# Configuration
DURATION = 5  # Duration to record in seconds
FILENAME = "debug.wav"

def record_audio(duration, filename):
    """
    Records audio from the default output device (loopback) for a specified duration
    and saves it to a WAV file.
    """
    try:
        # Get the default output device
        device_info = sd.query_devices(kind='output')
        samplerate = int(device_info['default_samplerate'])
        channels = device_info['max_output_channels']

        # Open an input stream with loopback=True to capture the output audio
        with sd.InputStream(samplerate=samplerate,
                            device=device_info['name'],
                            channels=channels,
                            callback=None,
                            blocksize=1024,
                            dtype='int16',
                            latency='low',
                            loopback=True) as stream:
            print(f"Recording for {duration} seconds...")
            recording = stream.read(int(samplerate * duration))[0]

            # Save the recording to a WAV file
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16 bits -> 2 bytes
                wf.setframerate(samplerate)
                wf.writeframes(recording.tobytes())
            print(f"Saved recording to {filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

def continuous_recording(duration, filename):
    """
    Continuously records audio at specified intervals.
    """
    while True:
        record_audio(duration, filename)
        time.sleep(duration)

if __name__ == "__main__":
    # Start continuous recording in a separate thread
    recording_thread = threading.Thread(target=continuous_recording, args=(DURATION, FILENAME))
    recording_thread.daemon = True
    recording_thread.start()

    print("Audio capture started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nAudio capture stopped.")

