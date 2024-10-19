import time
import os
import configparser
from faster_whisper import WhisperModel
import queue  # New import
from gui import SubtitleGUI  # New import
import soundfile as sf
import concurrent.futures

# Constants
AUDIO_INPUT_DIR = "recordings"
TRANSCRIPTION_OUTPUT = "transcriptions.txt"

# Load configuration
config = configparser.ConfigParser()
config.read("config.ini")
MODEL_SIZE = config.get('Settings', 'model')

# Queue for GUI updates
transcription_queue = queue.Queue()

def initialize_model(device):
    """
    Initialize the WhisperModel with the specified device.

    Args:
        device (str): The device to use ('cuda' or 'cpu').

    Returns:
        WhisperModel: The initialized model.
    """
    print(f"Loading model: {MODEL_SIZE} on {device}", flush=True)
    model = WhisperModel(MODEL_SIZE, device=device)
    print("Model loaded.", flush=True)
    return model

def transcribe_audio(model, audio_path):
    """
    Transcribe the given audio file using the preloaded Faster Whisper model.
    """
    print(f"Starting transcription for {audio_path}...", flush=True)
    try:
        with sf.SoundFile(audio_path) as sound_file:
            if sound_file.frames == 0:
                print(f"Warning: Empty audio file: {audio_path}")
                return ""
    except Exception as e:
        print(f"Error reading audio file {audio_path}: {e}")
        return ""

    segments, _ = model.transcribe(audio_path, beam_size=1, vad_filter=True, word_timestamps=True)
    transcription = " ".join(segment.text for segment in segments)
    print("Transcription completed.", flush=True)
    return transcription.strip()

def save_transcription(transcription, output_path):
    """
    Save the transcription text to a file and send it to the GUI.
    
    Args:
        transcription (str): The transcribed text.
        output_path (str): Path to the output transcription file.
    """
    with open(output_path, "a") as f:
        f.write(transcription + "\n")
    print(f"Transcription saved to {output_path}", flush=True)
    # Send transcription to GUI queue
    transcription_queue.put(transcription)

def monitor_audio_file(input_dir, output_path, check_interval=0.5, device="cuda"):
    """
    Continuously monitor the directory for new audio files and transcribe them.
    
    Args:
        input_dir (str): Directory to monitor for audio files.
        output_path (str): Path to save the transcriptions.
        check_interval (int): Time in seconds between checks.
        device (str): Device to use for transcription ('cuda' or 'cpu').
    """
    processed_files = set()
    model = initialize_model(device)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)  # Allows parallel processing
    while True:
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            if file_path not in processed_files:
                executor.submit(transcribe_and_save, model, file_path, output_path)
                processed_files.add(file_path)
        time.sleep(check_interval)

def transcribe_and_save(model, file_path, output_path):
    try:
        print(f"Transcribing {file_path}...", flush=True)
        transcription = transcribe_audio(model, file_path)
        if transcription:
            save_transcription(transcription, output_path)
    except Exception as e:
        print(f"Can't transcribe audio chunk {file_path}: {e}", flush=True)

if __name__ == "__main__":
    monitor_audio_file(AUDIO_INPUT_DIR, TRANSCRIPTION_OUTPUT)
