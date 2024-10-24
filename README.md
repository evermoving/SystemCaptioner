# System Captioner

Generates and shows real-time captions by listening to your Windows PC's audio. 

## How it works

1. Allows you to select a playback device from available loopback devices on your Windows system
2. Temporarily records everything you hear through the selected device in chunks using pyaudiowpatch
3. Locally transcribes the recordings using faster-whisper
4. Displays the transcriptions as captions in an always-on-top window

User-friendly GUI, draggable captions box, and intelligent mode that shows captions only when speech is detected.

By default, the app runs on and requires nVidia CUDA (cudnn + cublas). You can tell the app to run on CPU, but it might result in slower performance.

## Get started (Windows)

1. Clone the repository and navigate into the folder:
```bash
git clone https://github.com/evermoving/SystemCaptioner
cd SystemCaptioner
```
2. Create a virtual environment inside the cloned repo: 
```bash
python -m venv venv
```
3. Activate the virtual environment:
```bash
.\venv\Scripts\activate
```
4. Install the dependencies:
```bash
pip install -r requirements.txt
```
5. Download nvidia_dependencies zip from the releases section and extract it into folder where main.py is, i.e. `/SystemCaptioner/nvidia_dependencies/`
6. Launch main.py:
```bash
python main.py
```
7. Select your audio device from the dropdown menu. If it's already selected on first launch, select it again to ensure the sample rate is detected and written to config.ini. 

Initially, Whisper might take a while to load. Check console to monitor progress.