import pyaudiowpatch as pyaudio
import wave
import time
import threading
import os
import logging
import configparser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
config = configparser.ConfigParser()
config.read("config.ini")

# Convert the sample rate to a float first, then to an integer
SAMPLE_RATE = int(float(config.get('Settings', 'sample_rate', fallback='44100')))  # Default to 44100 if not set

# Constants
CHUNK = 2048  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 2  # Stereo
RECORD_SECONDS = 3  # Record in 2-second intervals
OUTPUT_DIR = "recordings"  # Directory to save recordings
MAX_FILES = 10  # Maximum number of files to keep

def get_default_loopback_device(p):
    """Get the default loopback device."""
    return p.get_default_wasapi_loopback()

def save_audio(frames, filename):
    """Save the recorded audio frames to a WAV file."""
    if not frames:  # Check if frames is empty
        print(f"Warning: No audio data to save for {filename}")
        return
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))

def cleanup_old_files():
    """Delete old WAV files, keeping only the most recent MAX_FILES."""
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.wav')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
    
    for old_file in files[MAX_FILES:]:
        os.remove(os.path.join(OUTPUT_DIR, old_file))
        print(f"Deleted old file: {old_file}")

def get_audio_devices():
    """Get all available WASAPI loopback devices."""
    devices = []
    try:
        p = pyaudio.PyAudio()
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('hostApi') == wasapi_info['index']:
                devices.append({
                    'index': i,
                    'name': device_info.get('name', 'Unknown Device'),
                    'defaultSampleRate': device_info.get('defaultSampleRate', 44100),
                    'maxInputChannels': device_info.get('maxInputChannels', 2)
                })
                logger.info(f"Found audio device: {device_info.get('name')} (Index: {i})")
        
        p.terminate()
    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")
    return devices

def record_audio(device_index=None):
    """Record audio from the specified or default speaker and save it to a file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

    try:
        with pyaudio.PyAudio() as p:
            # Get the specified or default loopback device
            if device_index is not None:
                device_info = p.get_device_info_by_index(device_index)
                logger.info(f"Using selected device: {device_info.get('name')} (Index: {device_index})")
            else:
                device_info = get_default_loopback_device(p)
                device_index = device_info['index']
                logger.info(f"Using default loopback device: {device_info.get('name')} (Index: {device_index})")

            # Log device properties
            logger.info(f"Device properties: {device_info}")
            
            try:
                # Open the stream with the detected sample rate
                stream = p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=SAMPLE_RATE,
                                input=True,
                                frames_per_buffer=CHUNK,
                                input_device_index=device_index)
                
                logger.info("Audio stream opened successfully")
                
                while True:
                    frames = []
                    for _ in range(0, int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)):
                        try:
                            data = stream.read(CHUNK)
                            frames.append(data)
                        except Exception as e:
                            logger.error(f"Error reading audio chunk: {e}")
                            continue

                    if frames:  # Only save if we have captured frames
                        filename = os.path.join(OUTPUT_DIR, f"recording_{int(time.time())}.wav")
                        threading.Thread(target=save_audio, args=(frames, filename)).start()
                        cleanup_old_files()
                    else:
                        logger.warning("No frames captured in this segment")

            except Exception as e:
                logger.error(f"Error opening audio stream: {e}")
                raise

    except Exception as e:
        logger.error(f"Critical error in record_audio: {e}")
        raise

if __name__ == "__main__":
    record_audio()
