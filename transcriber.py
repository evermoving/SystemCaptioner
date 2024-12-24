import time
import os
import re
import configparser
from faster_whisper import WhisperModel
import queue  # New import
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
    print(f"Model {MODEL_SIZE} loaded.", flush=True)
    return model

def transcribe_audio(model, audio_path, translation_enabled, source_language):
    """
    Transcribe the given audio file using the preloaded Faster Whisper model.
    """
    print(f"Transcribing {audio_path} with source language {source_language}...", flush=True)
    
    try:
        with sf.SoundFile(audio_path) as sound_file:
            if sound_file.frames == 0:
                print(f"Warning: Empty audio file: {audio_path}", flush=True)
                return ""
    except Exception as e:
        print(f"Error reading audio file {audio_path}: {e}", flush=True)
        return ""

    try:
        # print(f"Translation mode: {'enabled' if translation_enabled else 'disabled'}", flush=True)
        # print(f"Source language: {source_language}", flush=True)

        segments, _ = model.transcribe(
            audio_path,
            language=source_language,
            task="translate" if translation_enabled else "transcribe",
            beam_size=1,
            vad_filter=True,
            word_timestamps=True,
            # initial_prompt=""
            # suppress_tokens=[-1, 50363, 50364]
        )
        
        transcription = " ".join(segment.text for segment in segments)
        print("Whisper processing completed.", flush=True)
        return transcription.strip()
    except Exception as e:
        print(f"Error during processing: {e}", flush=True)
        return ""

def save_transcription(transcription, output_path, filter_hallucinations, store_output):
    """
    Save the transcription text to a file and send it to the GUI.
    
    Args:
        transcription (str): The transcribed text.
        output_path (str): Path to the output transcription file.
        filter_hallucinations (bool): Whether to filter hallucinations.
        store_output (bool): Whether to store the output in a file.
    """
    if filter_hallucinations:
        transcription = filter_hallucination_content(transcription)
    
    if store_output:
        with open(output_path, "a", encoding='utf-8') as f:
            f.write(transcription + "\n")
        print(f"Output saved to {output_path}", flush=True)
    
    # Send transcription to GUI queue
    transcription_queue.put(transcription)

def monitor_audio_file(input_dir, output_path, check_interval=0.5, device="cuda", args=None):
    """
    Continuously monitor the directory for new audio files and transcribe them.
    
    Args:
        input_dir (str): Directory to monitor for audio files.
        output_path (str): Path to save the transcriptions.
        check_interval (int): Time in seconds between checks.
        device (str): Device to use for transcription ('cuda' or 'cpu').
        args (argparse.Namespace): Parsed command-line arguments for translation toggle and source language.
    """
    processed_files = set()
    model = initialize_model(device)
    print(f"Using {args.workers} workers thread...", flush=True)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)  # Allows parallel processing

    print(f"Starting transcribe_and_save with translation_enabled: {args.translation_enabled} | source_language: {args.source_language} | filter_hallucinations: {args.filter_hallucinations} | store_output: {args.store_output}...", flush=True)

    while True:
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            if file_path not in processed_files:
                executor.submit(transcribe_and_save, model, file_path, output_path, args.translation_enabled, args.source_language, args.filter_hallucinations, args.store_output)
                processed_files.add(file_path)
        time.sleep(check_interval)


def filter_hallucination_content(input_string):
    """
    Filters out blacklisted words or sentences from an input string based on a blacklist file.

    Args:
        input_string (str): The input string to be filtered.

    Returns:
        str: The filtered string with blacklisted words/sentences removed and cleaned.
    """
    try:
        # Read the blacklist from the file
        with open('hallucinations.txt', 'r', encoding='utf-8') as file:
            blacklisted_lines = sorted(
                [line.strip().lower() for line in file if line.strip()],
                key=len,
                reverse=True  # Sort by length in descending order
            )

        filtered_string = input_string

        # Check for and remove blacklisted words/sentences recursively
        while True:
            initial_string = filtered_string
            for blacklisted in blacklisted_lines:
                pattern = re.compile(re.escape(blacklisted), re.IGNORECASE)
                filtered_string = pattern.sub('', filtered_string)

            # If no changes were made, exit the loop
            if initial_string == filtered_string:
                break

        # Remove awkward spaces (e.g., extra spaces between words)
        filtered_string = re.sub(r'\s+', ' ', filtered_string).strip()
        print(f"String \'{input_string}\' filtered as hallucination text detected", flush=True)

        return filtered_string

    except Exception as e:
        print(f"Returning unfiltered string. Error encountered: {e}", flush=True)
        return input_string


def transcribe_and_save(model, file_path, output_path, translation_enabled, source_language, filter_hallucinations, store_output):
    try:
        print(f"Transcribing/translating {file_path}...", flush=True)
        transcription = transcribe_audio(model, file_path, translation_enabled, source_language)
        if transcription:
            save_transcription(transcription, output_path, filter_hallucinations, store_output)
    except Exception as e:
        print(f"Can't transcribe/translate audio chunk {file_path}: {e}", flush=True)

if __name__ == "__main__":
    monitor_audio_file(AUDIO_INPUT_DIR, TRANSCRIPTION_OUTPUT)
