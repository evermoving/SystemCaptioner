import customtkinter as ctk
import configparser
from recorder import get_audio_devices

class SetupWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Initial Setup")
        self.geometry("400x200")
        self.resizable(False, False)

        # Create label
        self.label = ctk.CTkLabel(
            self,
            text="First launch detected. Select your audio device:",
            wraplength=350
        )
        self.label.pack(pady=(20, 10))

        # Get audio devices
        self.devices = get_audio_devices()
        self.device_names = [device['name'] for device in self.devices]
        self.device_selection = ctk.StringVar()

        if self.device_names:
            self.device_selection.set(self.device_names[0])

        # Create dropdown
        self.device_dropdown = ctk.CTkOptionMenu(
            self,
            values=self.device_names,
            variable=self.device_selection
        )
        self.device_dropdown.pack(pady=10)

        # Create submit button
        self.submit_button = ctk.CTkButton(
            self,
            text="Submit",
            command=self.on_submit
        )
        self.submit_button.pack(pady=10)

        # Add this line at the start of __init__
        self.after_ids = []

    def on_submit(self):
        # Get all pending after callbacks
        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id)
        
        # Cancel any pending animations
        for after_id in self.after_ids:  # You'll need to track these
            self.after_cancel(after_id)
        
        # Save configuration
        """Create initial config.ini file with selected audio device."""
        config = configparser.ConfigParser()
        
        # Find the selected device info
        selected_device = self.device_selection.get()
        device_info = next((device for device in self.devices if device['name'] == selected_device), None)
        
        config['Settings'] = {
            'mode': 'False',
            'cuda': 'True',
            'model': 'small',
            'audio_device': selected_device,
            'sample_rate': str(device_info['defaultSampleRate']) if device_info else '44100'
        }

        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        # Properly destroy the window
        self.quit()
        self.destroy()

def run_setup():
    setup_window = SetupWindow()
    setup_window.mainloop()

if __name__ == "__main__":
    run_setup()
