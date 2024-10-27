import os
import shutil
import PyInstaller.__main__

def build_portable():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    dist_path = os.path.join(current_dir, 'dist')
    nvidia_deps_path = os.path.join(current_dir, 'nvidia_dependencies')
    icon_path = os.path.join(current_dir, 'icon.ico')
    
    # Clean previous builds
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    
    # PyInstaller configuration
    PyInstaller.__main__.run([
        'main.py',
        '--name=SystemCaptioner',
        '--onedir',
        f'--icon={icon_path}',
        '--noconsole',
        # Add all necessary data files
        '--add-data=icon.ico;.',
        '--add-data=config.ini;.',
        '--add-data=controller.py;.',
        '--add-data=transcriber.py;.',  # Add transcriber module
        '--add-data=recorder.py;.',      # Add recorder module
        '--add-data=console.py;.',       # Add console module
        # Add all necessary hidden imports
        '--hidden-import=queue',
        '--hidden-import=configparser',
        '--hidden-import=customtkinter',
        '--hidden-import=torch',
        '--hidden-import=whisper',
        '--hidden-import=numpy',
        '--hidden-import=pyaudio',
        '--hidden-import=threading',
        '--hidden-import=transcriber',    # Add transcriber module
        '--hidden-import=recorder',       # Add recorder module
        '--hidden-import=console',        # Add console module
        '--hidden-import=sounddevice',    # Add sounddevice if you're using it
        '--hidden-import=wave',           # Add wave if you're using it
        '--hidden-import=scipy',          # Add scipy if you're using it
        '--collect-all=whisper',          # Ensure all whisper components are included
        '--collect-all=torch',            # Ensure all torch components are included
    ])
    
    # Copy NVIDIA dependencies if they exist
    if os.path.exists(nvidia_deps_path):
        target_nvidia_path = os.path.join(dist_path, 'SystemCaptioner', '_internal', 'nvidia_dependencies')
        shutil.copytree(nvidia_deps_path, target_nvidia_path)
        print("NVIDIA dependencies copied successfully")
    
    print("Build completed successfully!")

if __name__ == "__main__":
    build_portable()
