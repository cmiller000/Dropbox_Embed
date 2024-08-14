import dropbox 
import time
import json
import os
from typing import Optional, List, Dict, Union, Tuple
from dropbox import Dropbox
from dropbox.files import FileMetadata, FolderMetadata, ListFolderResult
from dropbox.exceptions import ApiError, RateLimitError, AuthError
from dropbox.sharing import CreateSharedLinkWithSettingsError, SharedLinkSettings, RequestedVisibility
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from config import CACHE_DIR, setup_logging
import asyncio
from tkinter import simpledialog
import aiofiles
import re

logger = setup_logging()

# Define our own TokenExpiredError
class TokenExpiredError(Exception):
    pass

class InvalidTokenError(Exception):
    pass

class DropboxService:
    MIN_CALL_INTERVAL = 0.1  # 100 ms between API calls, adjust as needed

    def __init__(self, access_token=None):
        self._dbx = None
        self._access_token = access_token
        self.last_api_call = 0  # Initialize last_api_call
        if access_token:
            self._ensure_connection()

    def set_access_token(self, access_token):
        self._access_token = access_token
        self._ensure_connection()

    def _ensure_connection(self):
        if not self._access_token:
            raise ValueError("Access token not set")
        if not self._dbx:
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
                backoff_factor=1
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
            session = requests.Session()
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            self._dbx = Dropbox(
                self._access_token,
                session=session
            )

    def _rate_limit(self):
        current_time = time.time()
        if current_time - self.last_api_call < self.MIN_CALL_INTERVAL:
            time.sleep(self.MIN_CALL_INTERVAL - (current_time - self.last_api_call))
        self.last_api_call = current_time

    def is_token_valid(self):
        try:
            self._ensure_connection()
            self._dbx.users_get_current_account()
            return True
        except AuthError:
            return False
        except Exception as e:
            logger.error(f"Error checking token validity: {str(e)}")
            return False

    def list_files(self, path: str) -> ListFolderResult:
        if not self._dbx:
            raise ValueError("Dropbox client not initialized. Set access token first.")
        self._rate_limit()
        try:
            logger.debug(f"Listing files in Dropbox folder: {path}")
            result = self._dbx.files_list_folder(path)
            logger.debug(f"Found {len(result.entries)} entries in {path}")
            return result
        except AuthError:
            logger.error("Authentication error when listing files")
            raise InvalidTokenError("The access token is invalid or has been revoked")
        except ApiError as e:
            logger.error(f"Dropbox API error when listing files in {path}: {str(e)}")
            raise

    async def batch_get_share_links(self, paths: List[str]) -> Dict[str, Optional[str]]:
        results = {}
        async def get_link(path):
            link = await self.get_cached_share_link(path)
            results[path] = link

        tasks = [asyncio.create_task(get_link(path)) for path in paths]
        await asyncio.gather(*tasks)
        return results

    async def get_cached_share_link(self, path: str) -> Optional[str]:
        cache_file = os.path.join(CACHE_DIR, path.replace('/', '_') + '.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if time.time() - cached_data['timestamp'] < 3600:  # Cache valid for 1 hour
                    return cached_data['url']
        
        url = await self.get_share_link(path)
        if url:
            with open(cache_file, 'w') as f:
                json.dump({'url': url, 'timestamp': time.time()}, f)
        return url

    async def get_share_link(self, path: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(0)  # Allow other coroutines to run
                self._rate_limit()
                # First, try to list existing shared links
                existing_links = self._dbx.sharing_list_shared_links(path=path).links
                if existing_links:
                    url = existing_links[0].url
                    # Transform the URL to the raw format and add raw=1
                    raw_url = re.sub(r'www\.dropbox\.com', 'dl.dropboxusercontent.com', url)
                    raw_url = raw_url.replace('?dl=0', '?raw=1')
                    return raw_url
                
                # If no existing link, create a new one
                settings = SharedLinkSettings(requested_visibility=RequestedVisibility.public)
                shared_link_metadata = self._dbx.sharing_create_shared_link_with_settings(path, settings)
                url = shared_link_metadata.url
                # Transform the URL to the raw format and add raw=1
                raw_url = re.sub(r'www\.dropbox\.com', 'dl.dropboxusercontent.com', url)
                raw_url = raw_url.replace('?dl=0', '?raw=1')
                return raw_url
            except ApiError as e:
                if isinstance(e.error, CreateSharedLinkWithSettingsError) and e.error.is_shared_link_already_exists():
                    # If the error indicates that a shared link already exists, try to get it
                    try:
                        existing_links = self._dbx.sharing_list_shared_links(path=path).links
                        if existing_links:
                            url = existing_links[0].url
                            # Transform the URL to the raw format and add raw=1
                            raw_url = re.sub(r'www\.dropbox\.com', 'dl.dropboxusercontent.com', url)
                            raw_url = raw_url.replace('?dl=0', '?raw=1')
                            return raw_url
                    except Exception as list_error:
                        logger.error(f"Error retrieving existing shared link for {path}: {str(list_error)}")
                
                if attempt < max_retries - 1:
                    logger.warning(f"Error getting/creating share link, retrying... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    logger.error(f"Error getting/creating share link for {path}: {str(e)}")
                    return None
            except RateLimitError:
                logger.warning("Rate limit reached. Waiting before retrying...")
                time.sleep(60)
            except Exception as e:
                logger.error(f"Unexpected error getting/creating share link for {path}: {str(e)}")
                return None
        return None

    async def create_shared_link(self, path: str) -> str:
        if not self._dbx:
            raise ValueError("Dropbox client not initialized. Set access token first.")
        self._rate_limit()
        try:
            # First, try to get existing shared links
            existing_links = self._dbx.sharing_list_shared_links(path=path).links
            if existing_links:
                url = existing_links[0].url
            else:
                # If no existing link, create a new one
                settings = SharedLinkSettings(requested_visibility=RequestedVisibility.public)
                shared_link_metadata = self._dbx.sharing_create_shared_link_with_settings(path, settings)
                url = shared_link_metadata.url
            
            # Transform the URL to the raw format and add raw=1
            raw_url = re.sub(r'www\.dropbox\.com', 'dl.dropboxusercontent.com', url)
            raw_url = raw_url.replace('?dl=0', '?raw=1')
            
            return raw_url
        except AuthError:
            logger.error("Authentication error when creating shared link")
            raise InvalidTokenError("The access token is invalid or has been revoked")
        except ApiError as e:
            logger.error(f"Dropbox API error when creating shared link for {path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when creating shared link for {path}: {str(e)}")
            raise

    async def process_files_batch(self, files, output_file, output_format, batch_size=10):
        total_files = len(files)
        for i in range(0, total_files, batch_size):
            batch = files[i:i+batch_size]
            tasks = [self.process_single_file(file, output_format) for file in batch]
            results = await asyncio.gather(*tasks)
            
            async with aiofiles.open(output_file, mode='a') as f:
                for result in results:
                    if result:
                        await f.write(result + '\n')
            
            yield i + len(batch), total_files

    async def process_single_file(self, file, output_format):
        try:
            share_link = await self.create_shared_link(file.path_lower)
            dl_link = share_link.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
            
            if output_format == 'txt':
                return f"{file.name}: {dl_link}"
            elif output_format == 'html':
                return f'<a href="{dl_link}">{file.name}</a>'
            elif output_format == 'markdown':
                return f'[{file.name}]({dl_link})'
        except Exception as e:
            logger.error(f"Error processing file {file.name}: {str(e)}")
            return None

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return set(json.load(f))
        return set()

    async def save_progress(self, processed_files):
        async with aiofiles.open(self.progress_file, 'w') as f:
            await f.write(json.dumps(list(processed_files)))

    async def process_files(self, files, output_file, output_format):
        processed_files = self.load_progress()
        total_files = len(files)

        async with aiofiles.open(output_file, mode='a') as f:
            for i, file in enumerate(files):
                if file.path_lower in processed_files:
                    yield i + 1, total_files
                    continue

                try:
                    result = await self.process_single_file(file, output_format)
                    if result:
                        await f.write(result + '\n')
                        processed_files.add(file.path_lower)
                        await self.save_progress(processed_files)
                except Exception as e:
                    logger.error(f"Error processing file {file.name}: {str(e)}")

                yield i + 1, total_files