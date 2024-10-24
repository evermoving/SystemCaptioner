# ![icon](icon.ico) System Captioner

Generates and shows real-time captions by listening to your Windows PC's audio. Highly experimental. 

## How it works

1. Identifies your Windows default playback device/speaker
2. Temporarily records what you hear through it in chunks using pyaudiowpatch
3. Locally transcribes the recordings using faster-whisper
4. Displays the transcriptions as captions on a always-on-top window

Comes with a user-friendly GUI, draggable captions box, and intelligent mode that shows captions only when speech is detected.

By default, the app runs on and requires nVidia CUDA (cudnn + cublas). You can tell the app to run on CPU, but it might result in slower performance.

## Get started

1. Download nvidia_dependencies zip from the releases section and extract it into folder where main.py is, i.e. `/SystemCaptioner/nvidia_dependencies/`
2. Run:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch main.py

> Initially, Whisper might take a while to load. Check console to monitor progress.