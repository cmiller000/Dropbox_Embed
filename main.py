import importlib
import subprocess
import sys

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ['aiofiles', 'dropbox', 'asyncio']

for package in required_packages:
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"{package} not found. Installing...")
        install_package(package)

import tkinter as tk
import asyncio
import sys
import logging
from tkinter import messagebox
from gui import DropboxApp
from config import logger

async def run_app(root: tk.Tk, app: DropboxApp) -> None:
    try:
        while True:
            root.update()
            await asyncio.sleep(0.01)  # Smaller delay for more responsive UI
    except tk.TclError as e:
        if "application has been destroyed" not in str(e):
            logger.error(f"Unexpected TclError: {e}", exc_info=True)
            raise

async def main() -> None:
    root = tk.Tk()
    root.title("Dropbox Media Links Generator")
    
    debug_mode = "--debug" in sys.argv
    
    app = DropboxApp(root, debug_mode=debug_mode)
    await run_app(root, app)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Unhandled exception in main loop: {str(e)}", exc_info=True)
        messagebox.showerror("Critical Error", f"A critical error occurred: {str(e)}\n\nThe application will now close.")
    finally:
        sys.exit(0)