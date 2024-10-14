import customtkinter as ctk
import subprocess
import sys
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sytem Subtitler")
        self.geometry("300x150")
        self.resizable(False, False)

        self.intelligent_mode = ctk.BooleanVar()

        self.start_button = ctk.CTkButton(self, text="Start", command=self.start_app)
        self.start_button.pack(pady=20)

        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.pack(pady=10)

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
            command=self.show_tooltip
        )
        self.tooltip_button.pack(side="left")

    def show_tooltip(self):
        tooltip = ctk.CTkToolTip(self.tooltip_button, "Displays subtitle box only when speech is detected.")

    def start_app(self):
        intelligent = self.intelligent_mode.get()
        python_executable = sys.executable
        main_path = os.path.join(os.path.dirname(__file__), "main.py")
        if intelligent:
            subprocess.Popen([python_executable, main_path, "--intelligent"])
        else:
            subprocess.Popen([python_executable, main_path])

if __name__ == "__main__":
    app = App()
    app.mainloop()

