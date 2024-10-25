# System Captioner

Generates and shows real-time captions by listening to your Windows PC's audio. Makes digital content more accessible for those who are deaf or hard of hearing, aids language learning, and more. 


https://github.com/user-attachments/assets/7315ab7c-fe30-4c37-91aa-60bb32979338


## How it works

1. Captures system audio in real-time through Windows audio loopback using PyAudioWPatch
3. Locally transcribes the recordings using faster-whisper
4. Displays the transcriptions as captions in a overlay window that remains always on top


Language auto-detection, user-friendly GUI, draggable captions box, and intelligent mode that shows captions only when speech is detected.

By default, the app runs on and requires nVidia CUDA (cudnn + cublas). You can also choose to run it on CPU. 

## Get started (Windows)

0. Install Python (currently compatible versions: Python 3.{7,8,9,10,11,12}.) 

1. Clone the repository (or download it as .zip from this page) and navigate into the folder:
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
6. Launch main.py while in virtual environment:
```bash
python main.py
```
7. Select your audio device from the dropdown menu. If it's already selected on first launch, select it again to ensure the sample rate is detected and written to config.ini. 

In case of issues, check the in-built console for any error messages.  
