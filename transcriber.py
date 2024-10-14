import time
import os
from faster_whisper import WhisperModel

# Constants
AUDIO_INPUT = "debug.wav"
TRANSCRIPTION_OUTPUT = "transcriptions.txt"
MODEL_SIZE = "small"  # Changed to "small"

# Load the model once at the start
print(f"Loading model: {MODEL_SIZE}")
model = WhisperModel(MODEL_SIZE, device="cpu")
print("Model loaded.")

def transcribe_audio(audio_path):
    """
    Transcribe the given audio file using the preloaded Faster Whisper model.
    
    Args:
        audio_path (str): Path to the audio file to transcribe.
        
    Returns:
        str: Transcribed text.
    """
    print("Starting transcription...")
    segments, _ = model.transcribe(audio_path)  # Adjusted for faster-whisper
    transcription = " ".join(segment.text for segment in segments)  # Combine segments
    print("Transcription completed.")
    return transcription.strip()

def save_transcription(transcription, output_path):
    """
    Save the transcription text to a file.
    
    Args:
        transcription (str): The transcribed text.
        output_path (str): Path to the output transcription file.
    """
    with open(output_path, "a") as f:
        f.write(transcription + "\n")
    print(f"Transcription saved to {output_path}")

def monitor_audio_file(audio_path, output_path, check_interval=10):
    """
    Continuously monitor the audio file for new recordings and transcribe them.
    
    Args:
        audio_path (str): Path to the audio file to monitor.
        output_path (str): Path to save the transcriptions.
        check_interval (int): Time in seconds between checks.
    """
    last_modified_time = 0
    while True:
        if os.path.exists(audio_path):
            current_modified_time = os.path.getmtime(audio_path)
            if current_modified_time != last_modified_time:
                try:
                    print(f"Transcribing {audio_path}...")
                    transcription = transcribe_audio(audio_path)
                    save_transcription(transcription, output_path)
                    last_modified_time = current_modified_time
                except Exception as e:
                    print(f"Error during transcription: {e}")
        else:
            print(f"Waiting for {audio_path} to be available...")
        time.sleep(check_interval)

if __name__ == "__main__":
    monitor_audio_file(AUDIO_INPUT, TRANSCRIPTION_OUTPUT)
