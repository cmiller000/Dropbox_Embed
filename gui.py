import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import asyncio
from typing import Optional, List, Tuple
import os
import dropbox  # Ensure dropbox module is imported
from dropbox.exceptions import ApiError  # Added ApiError import
from dropbox.files import FolderMetadata  # Added FolderMetadata import
from dropbox.sharing import CreateSharedLinkWithSettingsError  # Added CreateSharedLinkWithSettingsError import
from dropbox_service import DropboxService, TokenExpiredError, InvalidTokenError
from file_processor import FileProcessor
from config import WINDOW_TITLE, WINDOW_SIZE, OUTPUT_FORMATS, DROPBOX_ACCESS_TOKEN, setup_logging, load_json_config, save_json_config, ALL_FILE_EXTENSIONS, PREFERENCES_FILE
from datetime import datetime  # Import datetime for timestamp
import json  # Import json for saving/loading preferences
import time  # Add this import
from app_controller import AppController
from pathlib import Path

# Initialize logger
logger = setup_logging()

class TokenDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        logger.debug("TokenDialog initialized")
        super().__init__(parent, title)

    def body(self, master):
        logger.debug("TokenDialog body method called")
        ttk.Label(master, text="Enter your Dropbox token:").grid(row=0, column=0, pady=5)
        self.token_entry = ttk.Entry(master, width=50)
        self.token_entry.grid(row=1, column=0, pady=5)
        return self.token_entry

    def apply(self):
        logger.debug("TokenDialog apply method called")
        self.result = self.token_entry.get()
        logger.debug(f"Token entered: {self.result}")

class DropboxFolderBrowser(tk.Toplevel):
    def __init__(self, parent, title, dropbox_service):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")  # Set a larger window size
        self.dropbox_service = dropbox_service
        self.result = None

        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.heading('#0', text='Dropbox Folder Browser', anchor=tk.W)
        self.tree.bind('<<TreeviewOpen>>', self.on_open)

        self.root_node = self.tree.insert('', 'end', text='/', open=True)
        self.load_folder('', self.root_node)

        ttk.Button(self, text="Select", command=self.select).pack()

    def load_folder(self, path, parent_node):
        try:
            entries = self.dropbox_service.list_files(path).entries
            entries = sorted(entries, key=lambda entry: entry.name.lower())
            for entry in entries:
                if isinstance(entry, FolderMetadata):
                    node = self.tree.insert(parent_node, 'end', text=entry.name, open=False)
                    self.tree.insert(node, 'end')  # Add a dummy child to make it expandable
        except (InvalidTokenError, TokenExpiredError):
            messagebox.showerror("Error", "Invalid or expired token. Please re-authenticate.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load folder: {e}")

    def on_open(self, event):
        item = self.tree.focus()
        if self.tree.parent(item):  # Not root
            path = self.get_path(item)
            self.tree.delete(*self.tree.get_children(item))
            self.load_folder(path, item)

    def get_path(self, item):
        path_parts = []
        while item:
            path_parts.append(self.tree.item(item, 'text'))
            item = self.tree.parent(item)
        path = '/'.join(reversed(path_parts))
        return path if path != '/' else ''

    def select(self):
        item = self.tree.focus()
        self.result = self.get_path(item)
        self.destroy()

def get_output_path(custom_path=None):
    # Get the script's directory
    script_dir = Path(__file__).parent.absolute()
    
    # Create the outputs folder if it doesn't exist
    output_dir = script_dir / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"dropbox_{timestamp}.txt"
    
    # If a custom path is provided, use it; otherwise, use the default
    if custom_path:
        return Path(custom_path)
    else:
        return output_dir / filename

class DropboxApp:
    def __init__(self, master: tk.Tk, debug_mode: bool = False):
        self.master = master
        self.master.title(WINDOW_TITLE)
        self.master.geometry("800x200")  # Set default window size
        self.master.minsize(200, 200)  # Set minimum size
        self.debug_mode = debug_mode

        self.dropbox_token = ""
        self.app_controller = AppController()
        self.selected_folder = tk.StringVar()
        self.output_format = tk.StringVar(value="txt")
        self.file_type = tk.StringVar(value="both")
        self.output_file = tk.StringVar()
        self.set_default_output_file()
        self.file_types = ['Audio', 'Video']  # Default to both Audio and Video
        self.audio_var = tk.BooleanVar(value=True)
        self.video_var = tk.BooleanVar(value=True)
        self.progress_var = tk.DoubleVar()  # Add this line
        self.status_var = tk.StringVar()
        self.processing = False

        self.create_widgets()
        self.load_preferences()
        self.initialize_services()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Dropbox Folder Path:").grid(row=0, column=0, sticky="w")
        ttk.Entry(main_frame, textvariable=self.selected_folder, width=50).grid(row=0, column=1, sticky="we")
        ttk.Button(main_frame, text="Browse Dropbox", command=self.browse_folder).grid(row=0, column=2, padx=5)

        ttk.Label(main_frame, text="Output File:").grid(row=1, column=0, sticky="w")
        ttk.Entry(main_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, sticky="we")
        ttk.Button(main_frame, text="Browse", command=self.browse_output_file).grid(row=1, column=2, padx=5)

        ttk.Label(main_frame, text="File Types:").grid(row=4, column=0, sticky="w")
        file_types_frame = ttk.Frame(main_frame)
        file_types_frame.grid(row=4, column=1, columnspan=2, sticky="w")
        ttk.Checkbutton(file_types_frame, text="Audio", variable=self.audio_var, command=self.update_file_types).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(file_types_frame, text="Video", variable=self.video_var, command=self.update_file_types).pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky="we", pady=10)

        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=3, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10, sticky="we")

        self.generate_button = ttk.Button(button_frame, text="Generate Links", command=self.start_generate_links)
        self.generate_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="Stop Processing", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.reset_token_button = ttk.Button(button_frame, text="Reset Token", command=self.reset_token)
        self.reset_token_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        main_frame.columnconfigure(1, weight=1)

    def initialize_services(self):
        if self.dropbox_token:
            try:
                self.app_controller.set_access_token(self.dropbox_token)
                self.status_var.set("Access token set")
            except (TokenExpiredError, InvalidTokenError):
                self.status_var.set("Invalid or expired token. Please reset and enter a new token.")
        else:
            self.status_var.set("No access token set. Please enter a token.")

    def load_preferences(self):
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE, 'r') as f:
                    preferences = json.load(f)
                    self.selected_folder.set(preferences.get("selected_folder", ""))
                    self.output_format.set(preferences.get("output_format", "txt"))
                    self.output_file.set(preferences.get("output_file", ""))
                    self.dropbox_token = preferences.get("dropbox_token", "")
            except json.JSONDecodeError:
                logger.error("Error loading preferences. Using default values.")
        else:
            logger.info("Preferences file not found. Using default values.")

    def save_preferences(self):
        preferences = {
            "selected_folder": self.selected_folder.get(),
            "output_format": self.output_format.get(),
            "output_file": self.output_file.get(),
            "dropbox_token": self.dropbox_token
        }
        with open(PREFERENCES_FILE, 'w') as f:
            json.dump(preferences, f)

    def reset_token(self):
        logger.debug("Reset token button clicked")
        self.dropbox_token = ""
        self.app_controller = AppController()
        self.status_var.set("Token reset. Please enter a new token.")
        self.save_preferences()
        logger.debug("Calling set_token method")
        self.set_token()

    def set_token(self):
        logger.debug("set_token method called")
        dialog = TokenDialog(self.master, "Dropbox Token")
        logger.debug(f"TokenDialog result: {dialog.result}")
        if dialog.result:
            self.dropbox_token = dialog.result
            self.status_var.set("Token set")
            self.initialize_services()
            self.save_preferences()  # Save preferences when the token is set
        else:
            logger.debug("No token entered in dialog")

    def browse_folder(self):
        try:
            folder_browser = DropboxFolderBrowser(self.master, "Select Dropbox Folder", self.app_controller.dropbox_service)
            self.master.wait_window(folder_browser)
            if folder_browser.result:
                self.selected_folder.set(folder_browser.result)
                self.set_default_output_file()
                self.save_preferences()
        except (InvalidTokenError, TokenExpiredError) as e:
            if self.handle_token_error(str(e)):
                self.browse_folder()  # Retry with new token

    async def generate_links(self, output_path):
        if not self.dropbox_token:
            if not self.handle_token_error("No access token set. Please enter a token."):
                return

        self.app_controller.set_access_token(self.dropbox_token)
        logger.info(f"Selected folder: {self.selected_folder.get()}")
        logger.info(f"File types: {self.file_types}")

        try:
            start_time = time.time()
            self.progress_var.set(0)
            self.progress_bar["value"] = 0

            async for processed_count, total_files in self.app_controller.generate_links(
                self.selected_folder.get(),
                output_path,
                self.output_format.get(),
                self.file_types
            ):
                if not self.processing:
                    break
                elapsed_time = time.time() - start_time
                if total_files > 0:
                    progress = (processed_count / total_files) * 100
                    self.progress_var.set(progress)
                    self.progress_bar["value"] = progress
                    progress_message = f"Processed {processed_count} of {total_files} files (Elapsed time: {elapsed_time:.2f}s)"
                else:
                    progress_message = f"No files to process (Elapsed time: {elapsed_time:.2f}s)"
                self.status_var.set(progress_message)
                logger.debug(progress_message)
                
                self.master.update_idletasks()
                await asyncio.sleep(0)

            if self.processing:
                total_time = time.time() - start_time
                if total_files > 0:
                    self.status_var.set(f"Processed {total_files} files successfully in {total_time:.2f} seconds.")
                else:
                    self.status_var.set(f"No files were processed. Completed in {total_time:.2f} seconds.")
            else:
                self.status_var.set("Processing stopped by user.")
        except (TokenExpiredError, InvalidTokenError) as e:
            logger.error(f"Token error: {str(e)}")
            if self.handle_token_error(str(e)):
                await self.generate_links(output_path)
        except Exception as e:
            logger.error(f"Error generating links: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate links: {str(e)}")
        finally:
            self.processing = False
            self.generate_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.reset_token_button.config(state=tk.NORMAL)

    def browse_output_file(self):
        initial_dir = Path(self.output_file.get()).parent
        filename = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="Select Output File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filename:
            self.output_file.set(filename)

    def set_default_output_file(self):
        self.output_file.set(str(get_output_path()))

    def update_file_types(self):
        self.file_types = []
        if self.audio_var.get():
            self.file_types.append('Audio')
        if self.video_var.get():
            self.file_types.append('Video')
        logger.debug(f"Updated file types: {self.file_types}")

    def start_generate_links(self):
        self.processing = True
        self.generate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.reset_token_button.config(state=tk.DISABLED)
        output_path = self.output_file.get()
        if not output_path:
            output_path = str(get_output_path())
            self.output_file.set(output_path)
        
        asyncio.create_task(self.generate_links(output_path))

    def stop_processing(self):
        self.processing = False
        self.generate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.reset_token_button.config(state=tk.NORMAL)
        self.status_var.set("Processing stopped by user.")

    def handle_token_error(self, error_message):
        self.status_var.set(error_message)
        new_token = self.prompt_for_new_token()
        if new_token:
            self.dropbox_token = new_token
            self.app_controller.set_access_token(new_token)
            return True
        else:
            self.status_var.set("Failed to refresh token. Some features may be unavailable.")
            return False

    def prompt_for_new_token(self):
        return simpledialog.askstring("Dropbox Access Token", "Please enter your Dropbox access token:", parent=self.master)

    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        while True:
            self.master.update()
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = DropboxApp(root)
    app.run()