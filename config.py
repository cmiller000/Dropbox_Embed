import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any
import configparser
from dotenv import load_dotenv
import json
import time

# Define INI_CONFIG_FILE at the top
INI_CONFIG_FILE = 'config.ini'

# Load environment variables from .env file
load_dotenv()

# Dropbox configuration
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')

# File extensions
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']
DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.ppt', '.pptx', '.xls', '.xlsx', '.csv']
ALL_FILE_EXTENSIONS = AUDIO_EXTENSIONS + VIDEO_EXTENSIONS + IMAGE_EXTENSIONS + DOCUMENT_EXTENSIONS

# API rate limiting
MIN_CALL_INTERVAL = 0.1  # 100ms between API calls

# File processing
BATCH_SIZE = 10

# Paths
CACHE_DIR = 'dropbox_cache'
PREFERENCES_FILE = os.path.join(os.path.dirname(__file__), 'preferences.json') # Updated this line
LOG_FILE = 'app.log'

# GUI settings
WINDOW_TITLE = "Dropbox Media Links Generator"
WINDOW_SIZE = "1000x800"

# Output formats
OUTPUT_FORMATS = ["txt", "csv", "md"]

# Define the outputs directory
OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

# Create the outputs directory if it doesn't exist
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

def load_json_config() -> Dict[str, Any]:
    """Load configuration from the JSON preferences file."""
    if os.path.exists(PREFERENCES_FILE):
        with open(PREFERENCES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_json_config(config: Dict[str, Any]) -> None:
    """Save configuration to the JSON preferences file."""
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(config, f)

def load_ini_config() -> configparser.ConfigParser:
    """Load configuration from the INI file."""
    config = configparser.ConfigParser()
    config.read(INI_CONFIG_FILE)
    if 'Preferences' not in config:
        config['Preferences'] = {
            'selected_folders': '',
            'output_file': 'dropbox_links.txt',
            'file_extensions': ','.join(ALL_FILE_EXTENSIONS)
        }
        save_ini_config(config)
    return config

def save_ini_config(config: configparser.ConfigParser) -> None:
    """Save configuration to the INI file."""
    with open(INI_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Load configuration
json_config = load_json_config()
ini_config = load_ini_config()

# Set up logging
logger = setup_logging()

# Load configuration
json_config = load_json_config()
ini_config = load_ini_config()