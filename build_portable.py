import os
import shutil
import PyInstaller.__main__
import faster_whisper

def build_portable():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    dist_path = os.path.join(current_dir, 'dist')
    nvidia_deps_path = os.path.join(current_dir, 'nvidia_dependencies')
    icon_path = os.path.join(current_dir, 'icon.ico')
    
    # Get faster_whisper assets path
    faster_whisper_path = os.path.dirname(faster_whisper.__file__)
    assets_path = os.path.join(faster_whisper_path, 'assets')
    
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
        '--add-data=transcriber.py;.',
        '--add-data=recorder.py;.',
        '--add-data=console.py;.',
        f'--add-data={assets_path};faster_whisper/assets',  # Add faster_whisper assets
        # Add all necessary hidden imports
        '--hidden-import=queue',
        '--hidden-import=configparser',
        '--hidden-import=customtkinter',
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
        '--hidden-import=faster_whisper',  # Add faster_whisper
        '--collect-all=whisper',
        '--collect-all=torch',
        '--collect-all=faster_whisper',  # Collect all faster_whisper components
    ])
    
    # Copy NVIDIA dependencies if they exist
    if os.path.exists(nvidia_deps_path):
        target_nvidia_path = os.path.join(dist_path, 'SystemCaptioner', '_internal', 'nvidia_dependencies')
        shutil.copytree(nvidia_deps_path, target_nvidia_path)
        print("NVIDIA dependencies copied successfully")
    
    print("Build completed successfully!")

if __name__ == "__main__":
    build_portable()
