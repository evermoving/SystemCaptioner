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

# Get the sample rate from the config, defaulting to 16000
SAMPLE_RATE = int(float(config.get('Settings', 'sample_rate', fallback='16000')))

# Constants
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 2
RECORD_SECONDS = 3
OUTPUT_DIR = "recordings"
MAX_FILES = 100


def get_default_loopback_device(audio_interface):
    """Get the default loopback device."""
    return audio_interface.get_default_wasapi_loopback()


def save_audio(frames, filename):
    """Save the recorded audio frames to a WAV file."""
    if not frames:
        logger.warning(f"No audio data to save for {filename}")
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
        logger.info(f"Deleted old file: {old_file}")


def get_audio_devices():
    """Get all available WASAPI loopback devices."""
    devices = []
    try:
        audio_interface = pyaudio.PyAudio()
        wasapi_info = audio_interface.get_host_api_info_by_type(pyaudio.paWASAPI)

        for i in range(audio_interface.get_device_count()):
            device_info = audio_interface.get_device_info_by_index(i)
            if device_info.get('hostApi') == wasapi_info['index'] and device_info.get('isLoopbackDevice', False):
                devices.append({
                    'index': i,
                    'name': device_info.get('name', 'Unknown Device'),
                    'defaultSampleRate': device_info.get('defaultSampleRate', 44100),
                    'maxInputChannels': device_info.get('maxInputChannels', 2)
                })
                logger.info(f"Found loopback audio device: {device_info.get('name')} (Index: {i})")

        audio_interface.terminate()
    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")
    return devices


def record_audio(device_index=None):
    """Record audio from the specified or default speaker and save it to a file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

    try:
        with pyaudio.PyAudio() as audio_interface:
            if device_index is not None:
                device_info = audio_interface.get_device_info_by_index(device_index)
                logger.info(f"Using selected device: {device_info.get('name')} (Index: {device_index})")
            else:
                device_info = get_default_loopback_device(audio_interface)
                device_index = device_info['index']
                logger.info(f"Using default loopback device: {device_info.get('name')} (Index: {device_index})")

            logger.info(f"Device properties: {device_info}")

            try:
                stream = audio_interface.open(format=FORMAT,
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

