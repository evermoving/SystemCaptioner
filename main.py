import customtkinter as ctk
import subprocess
import sys
import os
import threading
import queue  # New import for queue
import time   # New import for sleep
import configparser  # New import for config handling

from console import ConsoleWindow, QueueWriter  # Importing ConsoleWindow and QueueWriter from console.py

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
        self.title("System Captioner")
        self.geometry("400x250")
        self.resizable(False, False)

        self.intelligent_mode = ctk.BooleanVar()
        self.gpu_enabled = ctk.BooleanVar()
        self.model_selection = ctk.StringVar()
        self.app_running = False
        self.process = None

        self.console_queue = queue.Queue()

        sys.stdout = QueueWriter(self.console_queue)
        sys.stderr = QueueWriter(self.console_queue)

        self.console_window = None

        self.config = configparser.ConfigParser()
        self.load_config()

        self.intelligent_mode.set(self.config.getboolean('Settings', 'mode'))
        self.gpu_enabled.set(self.config.getboolean('Settings', 'cuda'))
        self.model_selection.set(self.config.get('Settings', 'model'))

        self.start_button = ctk.CTkButton(self, text="Start", command=self.toggle_app, fg_color="green", hover_color="dark green")
        self.start_button.pack(pady=(25, 10))

        self.console_button = ctk.CTkButton(self, text="Console", command=self.open_console, fg_color="blue", hover_color="dark blue")
        self.console_button.pack(pady=(0, 25))

        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.pack(pady=(0, 10))

        self.inner_checkbox_frame = ctk.CTkFrame(self.checkbox_frame)
        self.inner_checkbox_frame.pack()

        self.intelligent_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame, 
            text="Intelligent mode", 
            variable=self.intelligent_mode,
            command=self.save_config
        )
        self.intelligent_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.intelligent_tooltip_button = ctk.CTkButton(
            self.inner_checkbox_frame,
            text="?",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="grey",
            command=None
        )
        self.intelligent_tooltip_button.grid(row=0, column=1)
        ToolTip(
            self.intelligent_tooltip_button, 
            "In intelligent mode, subtitle window is shown only when speech is detected."
        )

        self.gpu_checkbox = ctk.CTkCheckBox(
            self.inner_checkbox_frame,
            text="Run on GPU",
            variable=self.gpu_enabled,
            command=self.save_config
        )
        self.gpu_checkbox.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))

        self.gpu_tooltip_button = ctk.CTkButton(
            self.inner_checkbox_frame,
            text="?",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="grey",
            command=None
        )
        self.gpu_tooltip_button.grid(row=1, column=1, pady=(5, 0))
        ToolTip(
            self.gpu_tooltip_button, 
            "Disabling this will run the app on CPU and result in much slower transcription."
        )

        self.model_frame = ctk.CTkFrame(self)
        self.model_frame.pack(pady=(0, 10))

        self.model_label = ctk.CTkLabel(self.model_frame, text="Model:")
        self.model_label.pack(side="left", padx=(0, 5))

        self.model_dropdown = ctk.CTkOptionMenu(
            self.model_frame,
            values=["tiny", "base", "small", "medium", "large"],
            variable=self.model_selection,
            command=self.save_config  # Save config on change
        )
        self.model_dropdown.pack(side="left")

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
            self.start_button.configure(text="Stop", fg_color="red", hover_color="dark red")
        else:
            self.stop_app()
            self.start_button.configure(text="Start", fg_color="green", hover_color="dark green")

    def start_app(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        recordings_path = os.path.join(base_dir, "recordings")
        transcriptions_path = os.path.join(base_dir, "transcriptions.txt")

        if os.path.exists(recordings_path):
            try:
                for filename in os.listdir(recordings_path):
                    file_path = os.path.join(recordings_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print("Existing recordings have been deleted.", flush=True)
                self.enqueue_console_message("Existing recordings have been deleted.")
            except Exception as e:
                print(f"Error deleting recordings: {e}", flush=True)
                self.enqueue_console_message(f"Error deleting recordings: {e}")
        else:
            print("Recordings directory does not exist. Creating one.", flush=True)
            self.enqueue_console_message("Recordings directory does not exist. Creating one.")
            os.makedirs(recordings_path)

        try:
            with open(transcriptions_path, 'w') as f:
                pass  # Truncate the file to empty it
            print("transcriptions.txt has been emptied.", flush=True)
            self.enqueue_console_message("transcriptions.txt has been emptied.")
        except Exception as e:
            print(f"Error emptying transcriptions.txt: {e}", flush=True)
            self.enqueue_console_message(f"Error emptying transcriptions.txt: {e}")

        self.start_button.configure(text="Stop", fg_color="red", hover_color="dark red")
        intelligent = self.intelligent_mode.get()
        cuda = self.gpu_enabled.get()
        model = self.model_selection.get()
        python_executable = sys.executable
        controller_path = os.path.join(base_dir, "controller.py")
        args = [python_executable, "-u", controller_path]
        if intelligent:
            args.append("--intelligent")
        if cuda:
            args.append("--cuda")
        args.extend([f"--model", model])

        self.process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.app_running = True

        threading.Thread(target=self.read_process_output, daemon=True).start()
        threading.Thread(target=self.watch_console_queue, daemon=True).start()

    def stop_app(self):
        if self.process:
            self.process.terminate()
            self.process = None
        self.start_button.configure(text="Start", fg_color="green", hover_color="dark green")
        self.app_running = False

    def read_process_output(self):
        if self.process.stdout:
            for line in self.process.stdout:
                line = line.strip()
                print(f"controller.py: {line}")
        if self.process.stderr:
            for line in self.process.stderr:
                line = line.strip()
                print(f"controller.py ERROR: {line}")

    def enqueue_console_message(self, message):
        """Helper method to enqueue messages to the console queue."""
        self.console_queue.put(message)

    def open_console(self):
        """Open the console window."""
        if not self.console_window or not self.console_window.winfo_exists():
            self.console_window = ConsoleWindow(self.console_queue, self)
        else:
            self.console_window.focus()

    def watch_console_queue(self):
        """Continuously watch for console messages (if any additional handling is needed)."""
        while self.app_running:
            time.sleep(1)  # Adjust the sleep duration as needed

    def run(self):
        """Run the main application loop."""
        self.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()
