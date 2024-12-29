import customtkinter as ctk
import subprocess
import sys
import os
import threading
import queue
import time
import configparser
import webbrowser
from console import ConsoleWindow, QueueWriter
from setupGUI import run_setup

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Constants
CONFIG_FILE = "config.ini"
TOOLTIP_WRAP_LENGTH = 150
TOOLTIP_BG_COLOR = "#2e2e2e"
TOOLTIP_TEXT_COLOR = "white"
DEFAULT_SOURCE_LANGUAGE = "en"
DEFAULT_TRANSCRIPTION_TIMEOUT = "5"
DEFAULT_WORKERS = "4"
FEEDBACK_LINK = "https://github.com/evermoving/SystemCaptioner/issues"
LANGUAGE_CODES_LINK = "https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes"
CONTROLLER_DIR = "Controller" if getattr(sys, 'frozen', False) else "."
CONTROLLER_EXECUTABLE = 'Controller.exe' if getattr(sys, 'frozen', False) else 'controller.py'


class ToolTip:
    """
    Creates a tooltip for a given widget as the mouse goes on it.
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self._show_tooltip)
        self.widget.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(
            tw,
            text=self.text,
            wraplength=TOOLTIP_WRAP_LENGTH,
            bg_color=TOOLTIP_BG_COLOR,
            text_color=TOOLTIP_TEXT_COLOR,
        )
        label.pack()

    def _hide_tooltip(self, event=None):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()


def get_base_path():
    """Get the base path for the application in both dev and standalone environments."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("System Captioner v1.39 - Translation Update")
        self.geometry("650x585")
        self.resizable(True, True)

        # Load the application icon
        icon_path = os.path.join(get_base_path(), "icon.ico")
        self.iconbitmap(icon_path)

        # Initialize variables for app state and settings
        self.intelligent_mode = ctk.BooleanVar()
        self.gpu_enabled = ctk.BooleanVar()
        self.model_selection = ctk.StringVar()
        self.app_running = False
        self.process = None
        self.translation_enabled = ctk.BooleanVar()
        self.source_language = ctk.StringVar(value=DEFAULT_SOURCE_LANGUAGE)
        self.transcription_timeout = ctk.StringVar(value=DEFAULT_TRANSCRIPTION_TIMEOUT)
        self.workers = ctk.StringVar(value=DEFAULT_WORKERS)
        self.filter_hallucinations = ctk.BooleanVar()
        self.store_output = ctk.BooleanVar()
        self.console_queue = queue.Queue()
        self.console_window = ConsoleWindow(self.console_queue, self)
        self.console_window.withdraw()  # Start hidden
        self.config = configparser.ConfigParser()
        self._load_config()

        # Set initial values from config
        self.intelligent_mode.set(self.config.getboolean('Settings', 'mode'))
        self.gpu_enabled.set(self.config.getboolean('Settings', 'cuda'))
        self.model_selection.set(self.config.get('Settings', 'model'))

        # Redirect stdout and stderr
        sys.stdout = QueueWriter(self.console_queue)
        sys.stderr = QueueWriter(self.console_queue)

        # Initialize main UI elements
        self._init_ui()

        # Setup timeout monitoring
        self.TRANSCRIPTION_TIMEOUT = 5  # seconds
        self.last_transcription_start = 0
        self.current_transcription_file = None
        self.timeout_thread = None
        self.stop_timeout = threading.Event()

        # Add this line after super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _init_ui(self):
        """Initializes the main UI elements."""
        # Start/Stop button
        self.start_button = ctk.CTkButton(
            self, text="Start", command=self.toggle_app, fg_color="green", hover_color="dark green"
        )
        self.start_button.pack(pady=(25, 10))

        # Console button
        self.console_button = ctk.CTkButton(
            self, text="Console", command=self.open_console, fg_color="blue", hover_color="dark blue"
        )
        self.console_button.pack(pady=(0, 25))

        # Checkbox frame
        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.pack(pady=(0, 10))

        # Inner checkbox frame for organization
        self.inner_checkbox_frame = ctk.CTkFrame(self.checkbox_frame)
        self.inner_checkbox_frame.pack()

        # Intelligent mode checkbox
        self.intelligent_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame,
            text="Intelligent Mode",
            variable=self.intelligent_mode,
            command=self._save_config,
        )
        self.intelligent_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Intelligent mode tooltip button
        self._create_tooltip_button(
            self.inner_checkbox_frame,
            row=0,
            column=1,
            tooltip_text="In intelligent mode, subtitle window is shown only when speech is detected."
        )

        # GPU checkbox
        self.gpu_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame,
            text="Run on GPU",
            variable=self.gpu_enabled,
            command=self._save_config,
        )
        self.gpu_checkbox.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))

        # GPU tooltip button
        self._create_tooltip_button(
            self.inner_checkbox_frame,
            row=1,
            column=1,
            tooltip_text="Disabling this will run the app on CPU and result in much slower transcription."
        )

        # Translation checkbox
        self.translation_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame,
            text="Enable Translation",
            variable=self.translation_enabled,
            command=self._save_config,
        )
        self.translation_checkbox.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(5, 0))

        # Translation tooltip button
        self._create_tooltip_button(
            self.inner_checkbox_frame,
            row=2,
            column=1,
            tooltip_text="Enable this to translate the transcription to English."
        )

        # Filter hallucinations checkbox
        self.filter_hallucinations_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame,
            text="Filter Hallucinations",
            variable=self.filter_hallucinations,
            command=self._save_config,
        )
        self.filter_hallucinations_checkbox.grid(row=3, column=0, sticky="w", padx=(0, 10), pady=(5, 0))

        # Filter hallucinations tooltip button
        self._create_tooltip_button(
            self.inner_checkbox_frame,
            row=3,
            column=1,
            tooltip_text="Enable this to filter hallucinations using hallucinations.txt file.",
            command=lambda: self._open_file("hallucinations.txt"),
        )

        # Store output checkbox
        self.store_output_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame,
            text="Store Output",
            variable=self.store_output,
            command=self._save_config,
        )
        self.store_output_checkbox.grid(row=4, column=0, sticky="w", padx=(0, 10), pady=(5, 0))

        # Store output tooltip button
        self._create_tooltip_button(
            self.inner_checkbox_frame,
            row=4,
            column=1,
            tooltip_text="Enable this to store the transcription output in transcriptions.txt."
        )

        # Model selection frame
        self.model_frame = ctk.CTkFrame(self)
        self.model_frame.pack(pady=(0, 10))

        # Model label
        self.model_label = ctk.CTkLabel(self.model_frame, text="Model:")
        self.model_label.pack(side="left", padx=(0, 5))

        # Model dropdown
        self.model_dropdown = ctk.CTkOptionMenu(
            self.model_frame,
            values=[
                'tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium',
                'large-v1', 'large-v2', 'large-v3', 'large', 'distil-large-v2', 'distil-medium.en',
                'distil-small.en', 'distil-large-v3', 'large-v3-turbo', 'turbo'
            ],
            variable=self.model_selection,
            command=self._save_config,
        )
        self.model_dropdown.pack(side="left")

        # Model tooltip button
        self._create_tooltip_button(
            self.model_frame,
            tooltip_text="Select the model to use for transcription. Larger models are more accurate but require more VRAM. .en are English only models"
        )

        # Audio device frame
        self.device_frame = ctk.CTkFrame(self)
        self.device_frame.pack(pady=(0, 10))

        # Audio device label
        self.device_label = ctk.CTkLabel(self.device_frame, text="Audio Device:")
        self.device_label.pack(side="left", padx=(0, 5))

        # Audio devices dropdown
        self.devices = self._get_audio_devices()
        self.device_names = [device['name'] for device in self.devices]
        self.device_selection = ctk.StringVar()
        # Load saved device from config
        saved_device = self.config.get('Settings', 'audio_device', fallback='')
        if saved_device in self.device_names:
            self.device_selection.set(saved_device)
        elif self.device_names:
            self.device_selection.set(self.device_names[0])

        self.device_dropdown = ctk.CTkOptionMenu(
            self.device_frame,
            values=self.device_names,
            variable=self.device_selection,
            command=self._on_device_change,
        )
        self.device_dropdown.pack(side="left")

        # Feedback label
        self.feedback_label = ctk.CTkLabel(
            self,
            text="If the app didn't work or you had any issues, let us know!",
            text_color="light blue",
            cursor="hand2",
            font=("", -13, "underline"),
        )
        self.feedback_label.pack(side="bottom", pady=(0, 10))
        self.feedback_label.bind("<Button-1>", lambda e: self._open_url(FEEDBACK_LINK))

        # Timeout frame
        self.timeout_frame = ctk.CTkFrame(self)
        self.timeout_frame.pack(pady=(0, 10))

        # Timeout label
        self.timeout_label = ctk.CTkLabel(self.timeout_frame, text="Transcription Timeout (seconds):")
        self.timeout_label.pack(side="left", padx=(0, 5))

        # Timeout entry
        self.timeout_entry = ctk.CTkEntry(self.timeout_frame, textvariable=self.transcription_timeout)
        self.timeout_entry.pack(side="left")

        # Workers frame
        self.workers_frame = ctk.CTkFrame(self)
        self.workers_frame.pack(pady=(0, 10))

        # Workers label
        self.workers_label = ctk.CTkLabel(self.workers_frame, text="Workers:")
        self.workers_label.pack(side="left", padx=(0, 5))

        # Workers entry
        self.workers_entry = ctk.CTkEntry(self.workers_frame, textvariable=self.workers)
        self.workers_entry.pack(side="left")

        # Workers tooltip
        self._create_tooltip_button(
            self.workers_frame,
            tooltip_text="Number of worker threads for parallel processing."
        )

        # Language frame
        self.language_frame = ctk.CTkFrame(self)
        self.language_frame.pack(pady=(0, 10))

        # Language label
        self.language_label = ctk.CTkLabel(self.language_frame, text="Source Language:")
        self.language_label.pack(side="left", padx=(0, 5))

        # Language entry
        self.language_entry = ctk.CTkEntry(self.language_frame, textvariable=self.source_language)
        self.language_entry.pack(side="left")

        # Language tooltip
        self._create_tooltip_button(
            self.language_frame,
            tooltip_text="Specify the language used by the source audio using ISO-639-1 format (e.g., 'en' for English, 'zh' for Chinese).",
            command=lambda: self._open_url(LANGUAGE_CODES_LINK)
        )

    def _create_tooltip_button(self, parent, row=None, column=None, tooltip_text="", command=None):
        """Creates a tooltip button with the specified tooltip text."""
        button = ctk.CTkButton(
            parent,
            text="?",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="grey",
            command=command,
        )
        if row is not None and column is not None:
            button.grid(row=row, column=column, pady=(5, 0))
        else:
            button.pack(side="left")
        ToolTip(button, tooltip_text)

    def _load_config(self):
        """Loads configuration from config.ini or creates defaults if missing."""
        if not os.path.exists(CONFIG_FILE):
            run_setup()  # Run setup for initial device selection
        self.config.read(CONFIG_FILE)
        self.translation_enabled.set(self.config.getboolean('Settings', 'translation_enabled', fallback=False))
        self.source_language.set(self.config.get('Settings', 'source_language', fallback=DEFAULT_SOURCE_LANGUAGE))
        self.transcription_timeout.set(
            self.config.get('Settings', 'transcription_timeout', fallback=DEFAULT_TRANSCRIPTION_TIMEOUT))
        self.workers.set(self.config.get('Settings', 'workers', fallback=DEFAULT_WORKERS))
        self.filter_hallucinations.set(self.config.getboolean('Settings', 'filter_hallucinations', fallback=True))
        self.store_output.set(self.config.getboolean('Settings', 'store_output', fallback=True))

    def _save_config(self, *args):
        """Saves current settings to config.ini."""
        settings = self.config['Settings']
        settings['mode'] = str(self.intelligent_mode.get())
        settings['cuda'] = str(self.gpu_enabled.get())
        settings['model'] = self.model_selection.get()
        settings['audio_device'] = self.device_selection.get()
        settings['transcription_timeout'] = self.transcription_timeout.get()
        settings['workers'] = self.workers.get()
        settings['translation_enabled'] = str(self.translation_enabled.get())
        settings['source_language'] = self.source_language.get()
        settings['filter_hallucinations'] = str(self.filter_hallucinations.get())
        settings['store_output'] = str(self.store_output.get())
        # Save the sample rate of the selected device
        selected_device = self.device_selection.get()
        device_info = next((device for device in self.devices if device['name'] == selected_device), None)
        if device_info:
            settings['sample_rate'] = str(device_info['defaultSampleRate'])
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

    def toggle_app(self):
        """Toggles the application's start/stop state."""
        if not self.app_running:
            self._start_app()
            self.start_button.configure(text="Stop", fg_color="red", hover_color="dark red")
        else:
            self._stop_app()
            self.start_button.configure(text="Start", fg_color="green", hover_color="dark green")

    def _start_app(self):
        """Starts the captioning application."""
        # Reset timeout tracking variables
        self.last_transcription_start = 0
        self.current_transcription_file = None

        base_dir = get_base_path()
        recordings_path = os.path.join(base_dir, "recordings")
        transcriptions_path = os.path.join(base_dir, "transcriptions.txt")

        # Ensure recordings directory exists and clear existing files
        if os.path.exists(recordings_path):
            try:
                for filename in os.listdir(recordings_path):
                    file_path = os.path.join(recordings_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print("Existing recordings have been deleted.", flush=True)
            except Exception as e:
                print(f"Error deleting recordings: {e}", flush=True)
        else:
            print("Recordings directory does not exist. Creating one.", flush=True)
            os.makedirs(recordings_path)

        # Clear the transcriptions file if it's not already empty
        try:
            if os.path.exists(transcriptions_path) and os.path.getsize(transcriptions_path) > 0:
                with open(transcriptions_path, 'w') as f:
                    pass  # Truncate the file
                print("transcriptions.txt has been emptied.", flush=True)
            elif os.path.exists(transcriptions_path) and os.path.getsize(transcriptions_path) == 0:
                print("transcriptions.txt is already empty.", flush=True)
            else:
                print("transcriptions.txt does not exist.", flush=True)

        except Exception as e:
            print(f"Error handling transcriptions.txt: {e}", flush=True)

        # Update the start button
        self.start_button.configure(text="Stop", fg_color="red", hover_color="dark red")

        # Construct the controller executable path
        controller_executable = os.path.join(base_dir, CONTROLLER_DIR, CONTROLLER_EXECUTABLE)

        # Build the command arguments
        args = [controller_executable]
        if self.intelligent_mode.get():
            args.append("--intelligent")
        if self.gpu_enabled.get():
            args.append("--cuda")
        args.extend(["--model", self.model_selection.get()])

        # Get selected audio device index
        selected_device = self.device_selection.get()
        device_index = next((device['index'] for device in self.devices if device['name'] == selected_device), None)
        if device_index is not None:
            args.extend(["--device-index", str(device_index)])

        # Add translation and filter settings
        if self.translation_enabled.get():
            args.append("--translation-enabled")

        if self.filter_hallucinations.get():
            args.append("--filter-hallucinations")

        if self.store_output.get():
            args.append("--store-output")

        args.extend(["--source-language", self.source_language.get()])
        args.extend(["--transcription-timeout", self.transcription_timeout.get()])
        args.extend(["--workers", self.workers.get()])

        # Launch the subprocess
        self.process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.app_running = True

        # Start monitoring threads
        self.stop_timeout.clear()
        self.timeout_thread = threading.Thread(target=self._monitor_timeout, daemon=True)
        self.timeout_thread.start()

        threading.Thread(target=self._read_process_output, daemon=True).start()
        threading.Thread(target=self._watch_console_queue, daemon=True).start()

        self.TRANSCRIPTION_TIMEOUT = int(self.transcription_timeout.get())
        workers = int(self.workers.get())
        translation_enabled = self.translation_enabled.get()
        filter_hallucinations = self.filter_hallucinations.get()
        store_output = self.store_output.get()
        source_language = self.source_language.get()

        args.extend(["--transcription-timeout", str(self.TRANSCRIPTION_TIMEOUT)])
        args.extend(["--workers", str(workers)])
        if translation_enabled:
            args.append("--translation-enabled")

        if filter_hallucinations:
            args.append("--filter-hallucinations")

        if store_output:
            args.append("--store-output")

        args.extend(["--source-language", source_language])

    def _stop_app(self):
        """Stops the captioning application."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)  # Give a short time for graceful termination
            except subprocess.TimeoutExpired:
                self.process.kill()  # Force kill if process doesn't terminate gracefully
            self.process = None
        self.start_button.configure(text="Start", fg_color="green", hover_color="dark green")
        self.app_running = False
        self.stop_timeout.set()
        if self.timeout_thread and threading.current_thread() != self.timeout_thread:
            self.timeout_thread.join()
            self.timeout_thread = None

    def _monitor_timeout(self):
        """Monitors the transcription timeout and restarts the app if necessary."""
        while self.app_running and not self.stop_timeout.is_set():
            if self.last_transcription_start > 0:
                elapsed_time = time.time() - self.last_transcription_start
                if elapsed_time > self.TRANSCRIPTION_TIMEOUT:
                    error_msg = f"Transcription timeout for {self.current_transcription_file} after {self.TRANSCRIPTION_TIMEOUT} seconds"
                    self._enqueue_console_message(f"controller.py ERROR: {error_msg}")
                    self._stop_app()
                    time.sleep(1)
                    self._start_app()
                    break
            time.sleep(1)

    def _read_process_output(self):
        """Reads and processes output from the subprocess."""
        if self.process.stdout:
            for line in iter(self.process.stdout.readline, ''):
                if not line:
                    break
                line = line.strip()
                # Check for transcription start
                if "Starting transcription for" in line:
                    self.last_transcription_start = time.time()
                    self.current_transcription_file = line.split("...")[-2].split("recordings\\")[-1]

                # Check for transcription completion or error
                if "Transcription completed" in line or "Error during transcription" in line:
                    self.last_transcription_start = 0  # Reset the timer
                    self.current_transcription_file = None

                # Send messages to the console queue
                if "ERROR" in line:
                    self._enqueue_console_message(f"controller.py ERROR: {line}")
                else:
                    self._enqueue_console_message(f"controller.py: {line}")

    def _enqueue_console_message(self, message):
        """Enqueues a message to the console queue."""
        self.console_queue.put(message)

    def open_console(self):
        """Opens the console window."""
        if not self.console_window or not self.console_window.winfo_exists():
            self.console_window = ConsoleWindow(self.console_queue, self)
        else:
            self.console_window.deiconify()
            self.console_window.focus()

    def _watch_console_queue(self):
        """Monitors the console queue (placeholder for any additional console processing)."""
        while self.app_running:
            time.sleep(1)

    def run(self):
        """Runs the main application loop."""
        self.mainloop()

    def _get_audio_devices(self):
        """Gets a list of available audio devices."""
        from recorder import get_audio_devices
        return get_audio_devices()

    def _on_device_change(self, selected_device_name):
        """Handles changes in the selected audio device."""
        device_info = next((device for device in self.devices if device['name'] == selected_device_name), None)
        if device_info:
            self.config['Settings']['sample_rate'] = str(device_info['defaultSampleRate'])
            self.config['Settings']['audio_device'] = selected_device_name
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)

    def on_closing(self):
        """Handles cleanup when the window is closed."""
        # Stop the application if it's running
        if self.app_running:
            self._stop_app()

        # Ensure process is terminated
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        # Destroy console window
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.destroy()

        # Destroy main window
        self.quit()
        self.destroy()

    def _open_file(self, filename):
        """Opens a file with the default application."""
        os.startfile(filename)

    def _open_url(self, url):
        """Opens a URL in the default web browser."""
        webbrowser.open(url)


if __name__ == "__main__":
    app = App()
    app.run()

