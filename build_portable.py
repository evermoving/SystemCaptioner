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
    hallucinations_file = os.path.join(current_dir, 'filter_hallucinations.txt')

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

    print("Build completed successfully!")

    # Post-build steps
    try:
        dist_system_captioner = os.path.join(dist_path, 'SystemCaptioner')
        dist_controller = os.path.join(dist_path, 'Controller')
        controller_internal = os.path.join(dist_system_captioner, 'Controller', '_internal')

        # Move Controller folder inside SystemCaptioner
        if os.path.exists(dist_controller):
            target_controller = os.path.join(dist_system_captioner, 'Controller')
            if os.path.exists(target_controller):
                shutil.rmtree(target_controller)
            shutil.move(dist_controller, target_controller)
            print("Controller folder moved successfully")

        # Copy NVIDIA dependencies to Controller/_internal
        nvidia_src = os.path.join(dist_system_captioner, 'nvidia_dependencies')
        if os.path.exists(nvidia_src):
            nvidia_dest = os.path.join(controller_internal, 'nvidia_dependencies')
            if os.path.exists(nvidia_dest):
                shutil.rmtree(nvidia_dest)
            shutil.copytree(nvidia_src, nvidia_dest)
            print("NVIDIA dependencies copied to Controller/_internal successfully")

        # Copy icon.ico from _internal to root
        icon_src = os.path.join(dist_system_captioner, '_internal', 'icon.ico')
        icon_dest = os.path.join(dist_system_captioner, 'icon.ico')
        if os.path.exists(icon_src):
            shutil.copy2(icon_src, icon_dest)
            print("icon.ico copied to root successfully")

        # Copy filter_hallucinations.txt to root folder of System Captioner
        if os.path.exists(hallucinations_file):
            hallucinations_dest = os.path.join(dist_system_captioner, 'filter_hallucinations.txt')
            shutil.copy2(hallucinations_file, hallucinations_dest)
            print("filter_hallucinations.txt copied to root successfully")

        print("Post-build steps completed successfully!")

    except Exception as e:
        print(f"Error during post-build steps: {e}")

if __name__ == "__main__":
    build_portable()
