import whisper
import time
import os

# Constants
AUDIO_INPUT = "debug.wav"
TRANSCRIPTION_OUTPUT = "transcriptions.txt"
MODEL_SIZE = "small"  # Changed to "small"

def transcribe_audio(audio_path, model_size=MODEL_SIZE):
    """
    Transcribe the given audio file using Whisper model.
    
    Args:
        audio_path (str): Path to the audio file to transcribe.
        model_size (str): Size of the Whisper model to use.
        
    Returns:
        str: Transcribed text.
    """
    print(f"Loading model: {model_size}")
    model = whisper.load_model(model_size)
    print("Model loaded. Starting transcription...")
    result = model.transcribe(audio_path)
    print("Transcription completed.")
    return result["text"].strip()

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
