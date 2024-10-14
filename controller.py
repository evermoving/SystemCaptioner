import customtkinter as ctk
import subprocess
import sys
import os
import threading
import queue  # New import for queue
import time   # New import for sleep

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

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
        self.geometry("300x150")
        self.resizable(False, False)

        self.intelligent_mode = ctk.BooleanVar()
        self.app_running = False
        self.process = None

        # Queue to receive status updates from subprocess
        self.status_queue = queue.Queue()

        self.start_button = ctk.CTkButton(self, text="Start", command=self.toggle_app)
        self.start_button.pack(pady=(20, 10))  # Reduced bottom padding

        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.pack(pady=(0, 10))  # Reduced top padding

        self.intelligent_checkbox = ctk.CTkCheckBox(
            self.checkbox_frame, 
            text="Intelligent mode", 
            variable=self.intelligent_mode
        )
        self.intelligent_checkbox.pack(side="left", padx=(0, 10))

        self.tooltip_button = ctk.CTkButton(
            self.checkbox_frame,
            text="?",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="grey",
            command=None
        )
        self.tooltip_button.pack(side="left")
        ToolTip(self.tooltip_button, "Displays subtitle box only when speech is detected. The app must be stopped for this option to save.")

        self.status_label = ctk.CTkLabel(self, text="Status: Idle")
        self.status_label.pack(side="bottom", pady=(0, 10))  # Changed to pack at the bottom with padding

    def toggle_app(self):
        if not self.app_running:
            self.start_app()
        else:
            self.stop_app()

    def start_app(self):
        self.start_button.configure(text="Stop")
        self.status_label.configure(text="Status: Starting the app")
        intelligent = self.intelligent_mode.get()
        python_executable = sys.executable
        main_path = os.path.join(os.path.dirname(__file__), "main.py")
        args = [python_executable, "-u", main_path]  # Added "-u" for unbuffered output
        if intelligent:
            args.append("--intelligent")

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