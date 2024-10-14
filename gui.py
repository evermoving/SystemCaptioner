import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import time

class SubtitleGUI:
    def __init__(self, update_queue):
        self.update_queue = update_queue
        self.root = tk.Tk()
        self.root.title("Subtitles")
        self.root.geometry("800x200+100+600")  # Adjust size and position as needed
        self.root.attributes("-topmost", True)
        self.root.configure(bg='black')

        # ScrolledText widget for displaying subtitles
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, bg='black', fg='white', font=("Helvetica", 16))
        self.text_area.pack(expand=True, fill='both')
        self.text_area.configure(state='disabled')

        # Start the update loop in a separate thread
        self.root.after(100, self.update_subtitles)

    def update_subtitles(self):
        try:
            while True:
                transcription = self.update_queue.get_nowait()
                self.display_transcription(transcription)
        except queue.Empty:
            pass
        self.root.after(1000, self.update_subtitles)  # Update every second

    def display_transcription(self, transcription):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, transcription + "\n")
        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)
        # Optional: Clear previous lines after a delay
        # You can implement a rolling mechanism as needed

    def run(self):
        self.root.mainloop()

