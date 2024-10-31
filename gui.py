import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import time

class SubtitleGUI:
    def __init__(self, update_queue, intelligent_mode=False):
        self.update_queue = update_queue
        self.intelligent_mode = intelligent_mode
        self.last_activity_time = time.time()
        self.should_show = False

        self.root = tk.Tk()
        
        # Remove window decorations (frameless window)
        self.root.overrideredirect(True)
        
        # Set window size and position
        window_width = 800
        window_height = 120
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = screen_height - window_height - 50  # 50 pixels above the bottom
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Make window semi-transparent
        self.root.attributes("-alpha", 0.9)  # Range: 0.0 (fully transparent) to 1.0 (fully opaque)
        
        # Set window to be always on top
        self.root.attributes("-topmost", True)
        
        # Set background color to dark grey
        self.root.configure(bg='#2e2e2e')  # Dark grey color
        
        # ScrolledText widget for displaying subtitles
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg='#2e2e2e',  # Match the window background
            fg='white',
            font=("Helvetica", 24),
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(expand=True, fill='both')
        self.text_area.configure(state='disabled')
        
        # Bind mouse events for dragging the window
        self.text_area.bind("<ButtonPress-1>", self.start_move)
        self.text_area.bind("<ButtonRelease-1>", self.stop_move)
        self.text_area.bind("<B1-Motion>", self.do_move)
        
        # Variables to keep track of dragging
        self.offset_x = 0
        self.offset_y = 0

        if self.intelligent_mode:
            self.root.withdraw()  # Hide window initially

        # Start the update loop in the main thread
        self.root.after(100, self.update_subtitles)

    def start_move(self, event):
        """Record the offset when the user starts dragging the window."""
        self.offset_x = event.x
        self.offset_y = event.y

    def stop_move(self, event):
        """Reset the offset when the user stops dragging the window."""
        self.offset_x = 0
        self.offset_y = 0

    def do_move(self, event):
        """Move the window based on mouse movement."""
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def update_subtitles(self):
        """Check the queue for new transcriptions and display them."""
        try:
            while True:
                transcription = self.update_queue.get_nowait()
                self.display_transcription(transcription)
                if self.intelligent_mode:
                    self.last_activity_time = time.time()
                    if not self.should_show:
                        self.root.deiconify()
                        self.should_show = True
        except queue.Empty:
            pass

        if self.intelligent_mode:
            if self.should_show and (time.time() - self.last_activity_time > 4):
                self.root.withdraw()
                self.should_show = False

        self.root.after(100, self.update_subtitles)  # Check every 100 ms

    def display_transcription(self, transcription):
        """Insert the transcription into the text area."""
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, transcription + "\n")
        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)

    def run(self):
        """Run the Tkinter main loop."""
        self.root.mainloop()
