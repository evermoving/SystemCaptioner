import threading
import recorder
import transcriber

def start_recording():
    """Start the audio recording process."""
    recorder.record_audio()

def start_transcription():
    """Start the audio transcription process."""
    transcriber.monitor_audio_file(
        transcriber.AUDIO_INPUT_DIR,
        transcriber.TRANSCRIPTION_OUTPUT,
        check_interval=1
    )

if __name__ == "__main__":
    # Create threads for recording and transcription
    recording_thread = threading.Thread(target=start_recording)
    transcription_thread = threading.Thread(target=start_transcription)

    # Start the threads
    recording_thread.start()
    transcription_thread.start()

    # Wait for both threads to complete
    recording_thread.join()
    transcription_thread.join()
