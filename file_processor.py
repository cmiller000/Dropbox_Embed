import importlib
import subprocess
import sys
from collections import defaultdict
import json
import os
import asyncio
import aiofiles
from typing import List, Dict, Any, AsyncGenerator, Optional, Union, Tuple
from dropbox.files import FileMetadata, FolderMetadata
from config import (
    AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, IMAGE_EXTENSIONS, DOCUMENT_EXTENSIONS,
    BATCH_SIZE, logger, ALL_FILE_EXTENSIONS
)
import re
from dropbox_service import DropboxService

def install_aiofiles():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiofiles"])

try:
    importlib.import_module('aiofiles')
except ImportError:
    print("aiofiles not found. Installing...")
    install_aiofiles()

import aiofiles  # Make sure this line is here and not commented out
import asyncio
import os
import csv
import dropbox
from typing import List, Dict, Any, AsyncGenerator, Optional, Union, Tuple
from dropbox.files import FileMetadata, FolderMetadata
from config import (
    AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, IMAGE_EXTENSIONS, DOCUMENT_EXTENSIONS,
    BATCH_SIZE, logger, ALL_FILE_EXTENSIONS
)
import re
from dropbox_service import DropboxService

class FileProcessor:
    def __init__(self, dropbox_service):
        self.dropbox_service = dropbox_service
        self.progress_file = 'processing_progress.json'

    async def collect_files(self, folder_path: str, file_types: List[str]) -> Optional[Dict[str, List[Union[str, FileMetadata]]]]:
        try:
            logger.debug(f"Starting file collection from folder: {folder_path}")
            logger.debug(f"File types to collect: {file_types}")
            all_files = {}
            extensions = self._get_extensions(file_types)
            logger.debug(f"Extensions to look for: {extensions}")
            await self._collect_files_recursive(folder_path, extensions, all_files)
            logger.debug(f"File collection complete. Total folders: {len(all_files)}")
            for folder, files in all_files.items():
                logger.debug(f"Folder: {folder}, Files: {len(files)}")
            return all_files
        except Exception as e:
            logger.error(f"Error collecting files: {str(e)}")
            return None

    async def _collect_files_recursive(self, folder_path: str, extensions: List[str], all_files: Dict[str, List[Union[str, FileMetadata]]]):
        try:
            logger.debug(f"Listing files in folder: {folder_path}")
            result = self.dropbox_service.list_files(folder_path)
            logger.debug(f"Files/folders found in {folder_path}: {len(result.entries)}")
            for entry in result.entries:
                if isinstance(entry, FileMetadata):
                    logger.debug(f"File found: {entry.name}")
                    if any(entry.name.lower().endswith(ext.lower()) for ext in extensions):
                        logger.debug(f"File matches extension: {entry.name}")
                        if folder_path not in all_files:
                            all_files[folder_path] = []
                        all_files[folder_path].append(entry)
                elif isinstance(entry, FolderMetadata):
                    logger.debug(f"Subfolder found: {entry.name}")
                    await self._collect_files_recursive(entry.path_lower, extensions, all_files)
        except Exception as e:
            logger.error(f"Error collecting files from {folder_path}: {str(e)}")

    def _get_extensions(self, file_types: List[str]) -> List[str]:
        extensions = []
        if 'Audio' in file_types:
            extensions.extend(AUDIO_EXTENSIONS)
        if 'Video' in file_types:
            extensions.extend(VIDEO_EXTENSIONS)
        logger.debug(f"File types: {file_types}, Extensions to collect: {extensions}")
        return extensions

    async def process_files(self, files: Dict[str, List[Union[str, FileMetadata]]], output_file: str, output_format: str) -> AsyncGenerator[Tuple[int, int], None]:
        total_files = sum(len(folder_files) for folder_files in files.values())
        processed_count = 0

        with open(output_file, 'w', encoding='utf-8') as f:
            for folder_path, folder_files in files.items():
                if folder_files:
                    # Simplify the folder path to show only the last three levels
                    path_parts = folder_path.split('/')
                    simplified_folder_path = '/'.join(path_parts[-3:])
                    f.write(f"\n{simplified_folder_path}:\n")
                    f.write("=" * len(simplified_folder_path) + "\n\n")

                for file in folder_files:
                    result = await self.process_single_file(file, output_format)
                    if result:
                        f.write(result + "\n")
                    processed_count += 1
                    yield processed_count, total_files

    async def process_single_file(self, file: Union[str, FileMetadata], output_format: str) -> Optional[str]:
        try:
            file_path = file.path_lower if isinstance(file, FileMetadata) else file
            file_name = os.path.basename(file_path)
            
            # Simplify the path to show only the last three levels
            path_parts = file_path.split('/')
            simplified_path = '/'.join(path_parts[-3:])
            
            raw_link = await self.dropbox_service.create_shared_link(file_path)
            
            if output_format == 'html':
                return f'<p>Path: {simplified_path}<br><a href="{raw_link}">{file_name}</a></p>'
            elif output_format == 'markdown':
                return f'Path: {simplified_path}\n[{file_name}]({raw_link})\n'
            else:  # Plain text
                return f'Path: {simplified_path}\n{raw_link}\n'
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return None

    def load_progress(self) -> set:
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return set(json.load(f))
        return set()

    async def save_progress(self, processed_files: set):
        async with aiofiles.open(self.progress_file, 'w') as f:
            await f.write(json.dumps(list(processed_files)))

    # ... other methods ...