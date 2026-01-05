import os
import subprocess
from typing import Optional

class HermeticBrowser:
    """
    Manages the vendored Chrome instance (Puppeteer pattern).
    """
    def __init__(self, chrome_path: Optional[str] = None):
        # Default to a local 'chrome-win64' folder if not provided
        self.chrome_path = chrome_path or os.path.join(os.getcwd(), "chrome-win64", "chrome.exe")
        
    def launch(self, headless: bool = True):
        """
        Launch the browser process.
        """
        if not os.path.exists(self.chrome_path):
            raise FileNotFoundError(f"Hermetic Chrome not found at {self.chrome_path}")
            
        args = [
            self.chrome_path,
            "--remote-debugging-port=9222",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        if headless:
            args.append("--headless")

        self.process = subprocess.Popen(args)
        return self.process

    def stop(self):
        if self.process:
            self.process.terminate()
