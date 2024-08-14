import asyncio
from typing import List, Optional, AsyncGenerator, Tuple
from dropbox.exceptions import AuthError
from dropbox_service import DropboxService, TokenExpiredError, InvalidTokenError
from file_processor import FileProcessor
from config import logger, ALL_FILE_EXTENSIONS, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS

class AppController:
    def __init__(self):
        self.dropbox_service = DropboxService()
        self.file_processor = None
        logger.debug("AppController initialized")

    def set_access_token(self, access_token: str):
        logger.debug("Setting access token")
        self.dropbox_service.set_access_token(access_token)
        if self.dropbox_service.is_token_valid():
            self.file_processor = FileProcessor(self.dropbox_service)
            logger.debug(f"FileProcessor initialized: {self.file_processor}")
        else:
            raise InvalidTokenError("The provided access token is invalid")

    async def generate_links(self, folder_path, output_file, output_format, file_types):
        if not self.file_processor:
            raise ValueError("Access token not set or invalid. Call set_access_token() first.")
        
        logger.info(f"Generating links for folder: {folder_path}")
        logger.info(f"File types: {file_types}")
        files = await self.file_processor.collect_files(folder_path, file_types)
        if not files:
            logger.warning("No files collected")
            yield 0, 0
            return

        total_files = sum(len(folder_files) for folder_files in files.values())
        logger.info(f"Total files collected: {total_files}")
        if total_files == 0:
            logger.warning("No files to process")
            yield 0, 0
            return

        logger.info(f"Collected {total_files} files from {len(files)} folders. Starting processing...")
        async for processed_count, total_files in self.file_processor.process_files(files, output_file, output_format):
            yield processed_count, total_files

    def is_token_valid(self):
        return self.dropbox_service and self.dropbox_service.is_token_valid()

    def refresh_token(self, new_token: str) -> None:
        if self.dropbox_service:
            self.dropbox_service.set_access_token(new_token)
            logger.info("Access token refreshed")
        else:
            logger.error("Dropbox service not initialized")
            self.dropbox_service = DropboxService()
            self.file_processor = FileProcessor(self.dropbox_service)

    def stop_processing(self) -> None:
        if self.file_processor:
            self.file_processor.stop_processing = True
            logger.info("Processing stopped by user")

    def clear_data(self) -> None:
        if self.file_processor:
            self.file_processor.clear_data()
            logger.info("Data cleared")