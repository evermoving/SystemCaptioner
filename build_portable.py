import os
import shutil
import PyInstaller.__main__
import faster_whisper

def build_portable():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    dist_path = os.path.join(current_dir, 'dist')
    build_path = os.path.join(current_dir, 'build')
    nvidia_deps_path = os.path.join(current_dir, 'nvidia_dependencies')
    icon_path = os.path.join(current_dir, 'icon.ico')
    
    # Get faster_whisper assets path
    faster_whisper_path = os.path.dirname(faster_whisper.__file__)
    assets_path = os.path.join(faster_whisper_path, 'assets')
    
    # Clean previous builds
    for path in [dist_path, build_path]:
        if os.path.exists(path):
            shutil.rmtree(path)
    
    # PyInstaller configuration for main.py
    PyInstaller.__main__.run([
        'main.py',
        '--name=SystemCaptioner',
        '--onedir',
        f'--icon={icon_path}',
        '--noconsole',
        '--clean',
        # Add all necessary data files
        '--add-data=icon.ico;.',
        '--add-data=config.ini;.',
        '--add-data=transcriber.py;.',
        '--add-data=recorder.py;.',
        '--add-data=console.py;.',
        f'--add-data={assets_path};faster_whisper/assets',
        # Add all necessary hidden imports
        '--hidden-import=queue',
        '--hidden-import=configparser',
        '--hidden-import=customtkinter',
        '--hidden-import=setupGUI',
        '--hidden-import=torch',
        '--hidden-import=whisper',
        '--hidden-import=numpy',
        '--hidden-import=pyaudio',
        '--hidden-import=threading',
        '--hidden-import=transcriber',
        '--hidden-import=recorder',
        '--hidden-import=console',
        '--hidden-import=sounddevice',
        '--hidden-import=wave',
        '--hidden-import=scipy',
        '--hidden-import=faster_whisper',
        '--hidden-import=ctypes',
        '--hidden-import=win32gui',
        '--collect-all=whisper',
        '--collect-all=torch',
        '--collect-all=faster_whisper',
        '--collect-all=customtkinter',
    ])
    
    # PyInstaller configuration for controller.py
    PyInstaller.__main__.run([
        'controller.py',
        '--name=Controller',
        '--onedir',
        f'--icon={icon_path}',
        '--noconsole',
        '--clean',
        # Add necessary data files if any
        '--add-data=config.ini;.',
        f'--add-data={assets_path};faster_whisper/assets',
        # Add hidden imports
        '--hidden-import=queue',
        '--hidden-import=configparser',
        '--hidden-import=setupGUI',
        '--hidden-import=torch',
        '--hidden-import=whisper',
        '--hidden-import=numpy',
        '--hidden-import=pyaudio',
        '--hidden-import=threading',
        '--hidden-import=transcriber',
        '--hidden-import=recorder',
        '--hidden-import=sounddevice',
        '--hidden-import=wave',
        '--hidden-import=scipy',
        '--hidden-import=faster_whisper',
        '--hidden-import=ctypes',
        '--hidden-import=win32gui',
        '--collect-all=whisper',
        '--collect-all=torch',
        '--collect-all=faster_whisper',
    ])
    
    # Copy NVIDIA dependencies if they exist
    if os.path.exists(nvidia_deps_path):
        target_nvidia_path = os.path.join(dist_path, 'SystemCaptioner', 'nvidia_dependencies')
        if os.path.exists(target_nvidia_path):
            shutil.rmtree(target_nvidia_path)
        shutil.copytree(nvidia_deps_path, target_nvidia_path)
        print("NVIDIA dependencies copied successfully")
    
    # Create an empty transcriptions.txt file
    with open(os.path.join(dist_path, 'SystemCaptioner', 'transcriptions.txt'), 'w') as f:
        pass
    
    # Create a default config.ini if it doesn't exist
    config_path = os.path.join(dist_path, 'SystemCaptioner', 'config.ini')
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write("""[Settings]
mode = False
cuda = True
model = small
audio_device = 
sample_rate = 44100
""")
    
    print("Build completed successfully!")

if __name__ == "__main__":
    build_portable()
