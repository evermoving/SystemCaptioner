import customtkinter as ctk
from tkinter import scrolledtext
import threading
import queue
import sys

class ConsoleWindow(ctk.CTkToplevel):
    def __init__(self, console_queue, master=None, icon_path=None):
        super().__init__(master)
        self.title("Console Output")
        self.geometry("600x400")
        
        # Set the icon for the console window
        if icon_path:
            self.iconbitmap(icon_path)

        self.console_queue = console_queue

        # ScrolledText widget for displaying console output
        self.text_area = scrolledtext.ScrolledText(
            self,
            wrap=ctk.WORD,
            bg='#2e2e2e',
            fg='white',
            font=("Courier New", 12),
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(expand=True, fill='both')
        self.text_area.configure(state='disabled')

        # Start the update loop
        self.after(100, self.update_console)

    def update_console(self):
        """Check the queue for new console messages and display them."""
        try:
            while True:
                message = self.console_queue.get_nowait()
                self.display_message(message)
        except queue.Empty:
            pass
        self.after(100, self.update_console)

    def display_message(self, message):
        """Insert the message into the text area."""
        self.text_area.configure(state='normal')
        self.text_area.insert(ctk.END, message + "\n")
        self.text_area.configure(state='disabled')
        self.text_area.yview(ctk.END)

class QueueWriter:
    """A writer object that redirects writes to a queue."""
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def write(self, message):
        if message.strip() != "":
            self.log_queue.put(message)

    def flush(self):
        pass  # No action needed for flush in this implementation

