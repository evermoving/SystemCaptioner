import time
import os
from faster_whisper import WhisperModel
import queue  # New import
from gui import SubtitleGUI  # New import

# Constants
AUDIO_INPUT_DIR = "recordings"
TRANSCRIPTION_OUTPUT = "transcriptions.txt"
MODEL_SIZE = "medium"  # Changed to "small"

# Queue for GUI updates
transcription_queue = queue.Queue()

# Load the model once at the start
print(f"Loading model: {MODEL_SIZE}", flush=True)
model = WhisperModel(MODEL_SIZE, device="cuda")  # Changed to "cuda"
print("Model loaded.", flush=True)

def transcribe_audio(audio_path):
    """
    Transcribe the given audio file using the preloaded Faster Whisper model.
    
    Args:
        audio_path (str): Path to the audio file to transcribe.
        
    Returns:
        str: Transcribed text.
    """
    print(f"Starting transcription for {audio_path}...", flush=True)
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

def monitor_audio_file(input_dir, output_path, check_interval=2):
    """
    Continuously monitor the directory for new audio files and transcribe them.
    
    Args:
        input_dir (str): Directory to monitor for audio files.
        output_path (str): Path to save the transcriptions.
        check_interval (int): Time in seconds between checks.
    """
    processed_files = set()
    while True:
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            if file_path not in processed_files:
                try:
                    print(f"Transcribing {file_path}...", flush=True)
                    transcription = transcribe_audio(file_path)
                    save_transcription(transcription, output_path)
                    processed_files.add(file_path)
                except Exception as e:
                    print(f"Error during transcription: {e}", flush=True)
        time.sleep(check_interval)

if __name__ == "__main__":
    monitor_audio_file(AUDIO_INPUT_DIR, TRANSCRIPTION_OUTPUT)