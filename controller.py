import customtkinter as ctk
import subprocess
import sys
import os
import threading
import queue  # New import for queue
import time   # New import for sleep
import configparser  # New import for config handling

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Constants
CONFIG_FILE = "config.ini"

class ToolTip:
    """
    It creates a tooltip for a given widget as the mouse goes on it.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, wraplength=150, bg_color="#2e2e2e", text_color="white")
        label.pack()

    def hide_tooltip(self, event=None):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("System Subtitler")
        self.geometry("400x250")  # Increased width and height to accommodate dropdown
        self.resizable(False, False)

        self.intelligent_mode = ctk.BooleanVar()
        self.gpu_enabled = ctk.BooleanVar()  # New BooleanVar for GPU checkbox
        self.model_selection = ctk.StringVar()  # New StringVar for model selection
        self.app_running = False
        self.process = None

        # Queue to receive status updates from subprocess
        self.status_queue = queue.Queue()

        # Load configuration
        self.config = configparser.ConfigParser()
        self.load_config()

        # Initialize the Intelligent mode, CUDA, and model based on config
        self.intelligent_mode.set(self.config.getboolean('Settings', 'mode'))
        self.gpu_enabled.set(self.config.getboolean('Settings', 'cuda'))  # Initialize GPU checkbox
        self.model_selection.set(self.config.get('Settings', 'model'))  # Initialize model selection

        self.start_button = ctk.CTkButton(self, text="Start", command=self.toggle_app)
        self.start_button.pack(pady=(20, 10))  # Reduced bottom padding

        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.pack(pady=(0, 10))  # Reduced top padding

        # Intelligent Mode Checkbox and Tooltip
        self.intelligent_frame = ctk.CTkFrame(self.checkbox_frame)
        self.intelligent_frame.pack(pady=(0, 5))

        self.intelligent_checkbox = ctk.CTkCheckBox(
            self.intelligent_frame, 
            text="Intelligent mode", 
            variable=self.intelligent_mode,
            command=self.save_config  # Save config on change
        )
        self.intelligent_checkbox.pack(side="left", padx=(0, 5))

        self.intelligent_tooltip_button = ctk.CTkButton(
            self.intelligent_frame,
            text="?",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="grey",
            command=None
        )
        self.intelligent_tooltip_button.pack(side="left")
        ToolTip(
            self.intelligent_tooltip_button, 
            "In intelligent mode, subtitle window is shown only when speech is detected."
        )

        # Run on GPU Checkbox (moved to a new line)
        self.gpu_frame = ctk.CTkFrame(self)
        self.gpu_frame.pack(pady=(0, 10))

        self.gpu_checkbox = ctk.CTkCheckBox(
            self.gpu_frame,
            text="Run on GPU",
            variable=self.gpu_enabled,
            command=self.save_config  # Save config on change
        )
        self.gpu_checkbox.pack(side="left", padx=(0, 5))

        # Tooltip for GPU Checkbox
        self.gpu_tooltip_button = ctk.CTkButton(
            self.gpu_frame,
            text="?",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="grey",
            command=None
        )
        self.gpu_tooltip_button.pack(side="left")
        ToolTip(
            self.gpu_tooltip_button, 
            "Disabling this will run the app on CPU and result in much slower transcription."
        )

        # Model Selection Dropdown
        self.model_frame = ctk.CTkFrame(self)
        self.model_frame.pack(pady=(0, 10))

        self.model_label = ctk.CTkLabel(self.model_frame, text="Select Model:")
        self.model_label.pack(side="left", padx=(0, 5))

        self.model_dropdown = ctk.CTkOptionMenu(
            self.model_frame,
            values=["tiny", "base", "small", "medium", "large"],
            variable=self.model_selection,
            command=self.save_config  # Save config on change
        )
        self.model_dropdown.pack(side="left")

        # Tooltip for Model Dropdown
        self.model_tooltip_button = ctk.CTkButton(
            self.model_frame,
            text="?",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="grey",
            command=None
        )
        self.model_tooltip_button.pack(side="left")
        ToolTip(
            self.model_tooltip_button, 
            "Select the model to use for transcription. Larger models are more accurate but require more VRAM."
        )

        self.status_label = ctk.CTkLabel(self, text="Status: Idle")
        self.status_label.pack(side="bottom", pady=(0, 10))  # Changed to pack at the bottom with padding

    def load_config(self):
        """Load the configuration from config.ini or create default if not exists."""
        if not os.path.exists(CONFIG_FILE):
            self.create_default_config()
        self.config.read(CONFIG_FILE)

    def create_default_config(self):
        """Create a default config.ini file with basic settings."""
        self.config['Settings'] = {
            'mode': 'False',    # Default mode is basic (False)
            'cuda': 'True',     # Default CUDA is enabled (True)
            'model': 'small'    # Default model is small
        }
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

    def save_config(self, *args):
        """Save the current settings to config.ini."""
        self.config['Settings']['mode'] = str(self.intelligent_mode.get())
        self.config['Settings']['cuda'] = str(self.gpu_enabled.get())  # Save GPU setting
        self.config['Settings']['model'] = self.model_selection.get()  # Save model selection
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

    def toggle_app(self):
        if not self.app_running:
            self.start_app()
        else:
            self.stop_app()

    def start_app(self):
        # Path configurations
        base_dir = os.path.dirname(os.path.abspath(__file__))
        recordings_path = os.path.join(base_dir, "recordings")
        transcriptions_path = os.path.join(base_dir, "transcriptions.txt")

        # Delete existing recordings
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

        # Empty transcriptions.txt
        try:
            with open(transcriptions_path, 'w') as f:
                pass  # Truncate the file to empty it
            print("transcriptions.txt has been emptied.", flush=True)
        except Exception as e:
            print(f"Error emptying transcriptions.txt: {e}", flush=True)

        # Proceed to start the subprocess
        self.start_button.configure(text="Stop")
        self.status_label.configure(text="Status: Loading model...")
        intelligent = self.intelligent_mode.get()
        cuda = self.gpu_enabled.get()  # Use GPU setting from checkbox
        model = self.model_selection.get()  # Get selected model
        python_executable = sys.executable
        main_path = os.path.join(base_dir, "main.py")
        args = [python_executable, "-u", main_path]  # Added "-u" for unbuffered output
        if intelligent:
            args.append("--intelligent")
        if cuda:
            args.append("--cuda")
        args.extend([f"--model", model])  # Add model argument

        # Start the subprocess with stdout and stderr piped
        self.process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.app_running = True
        self.status_label.configure(text="Status: Loading model...")

        # Start a thread to read the subprocess output
        threading.Thread(target=self.read_process_output, daemon=True).start()

        # Start polling the queue for status updates
        self.after(100, self.poll_status_queue)

    def stop_app(self):
        if self.process:
            self.process.terminate()
            self.process = None
        self.start_button.configure(text="Start")
        self.status_label.configure(text="Status: Idle")
        self.app_running = False

    def read_process_output(self):
        """
        Reads the stdout and stderr of the subprocess and puts relevant
        messages into the status_queue.
        """
        if self.process.stdout:
            for line in self.process.stdout:
                line = line.strip()
                print(f"transcriber.py: {line}")  # Optional: Prefix for clarity
                if "Loading model" in line:
                    self.status_queue.put("Status: Loading model...")
                elif "Model loaded" in line:
                    if self.intelligent_mode.get():
                        self.status_queue.put("Status: Listening for speech (Intelligent mode)")
                    else:
                        self.status_queue.put("Status: Listening for speech (Basic mode)")
        if self.process.stderr:
            for line in self.process.stderr:
                line = line.strip()
                print(f"transcriber.py ERROR: {line}")
                self.status_queue.put(f"Error: {line}")

    def poll_status_queue(self):
        """
        Polls the status_queue and updates the status_label accordingly.
        """
        while not self.status_queue.empty():
            try:
                status = self.status_queue.get_nowait()
                self.status_label.configure(text=status)
            except queue.Empty:
                pass
        if self.app_running:
            self.after(100, self.poll_status_queue)

if __name__ == "__main__":
    app = App()
    app.mainloop()