
# Dropbox Media Links Generator

## Overview

The Dropbox Media Links Generator is a Python-based application that allows users to generate shareable media links from files stored in Dropbox. The application provides a graphical user interface (GUI) for easy interaction, supports various media types, and leverages asynchronous operations to ensure a responsive user experience.

## Features

- **Dropbox Integration**: Connect to your Dropbox account securely using an access token.
- **File Type Filtering**: Select specific types of files (audio and video) to generate links for.
- **Asynchronous Processing**: Uses async operations to handle large numbers of files without blocking the UI.
- **Folder Browser**: Navigate through your Dropbox folders via the built-in folder browser.
- **Progress Tracking**: Monitor the progress of link generation in real-time.
- **Logging**: Detailed logging of application activities for easy debugging and monitoring.

## Installation

### Prerequisites

- Python 3.7 or higher
- Dropbox account with API access
- `pip` package manager

### Setup

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/your-repo/dropbox-media-links-generator.git
    cd dropbox-media-links-generator
    ```

2. **Install Required Packages**:

    The application automatically checks for required packages and installs them if necessary. However, you can manually install them using:

    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**:

    Create a `.env` file in the root directory and add your Dropbox access token:

    ```bash
    DROPBOX_ACCESS_TOKEN=your_access_token_here
    ```

    Alternatively, you will be prompted to enter your access token upon starting the application.

## Usage

### Running the Application

Start the application using Python:

```bash
python main.py
```

### Using the GUI

1. **Enter Dropbox Token**: Upon launching, you'll be prompted to enter your Dropbox access token if not already set.
2. **Browse Folders**: Use the folder browser to navigate through your Dropbox directories.
3. **Select File Types**: Choose which types of files you want to generate links for (e.g., audio, video, images, documents).
4. **Generate Links**: Click on the "Generate Links" button to start the process. The application will process the selected files and generate shareable links in the format of your choice.
5. **Save Output**: The generated links will be saved in the `outputs` directory in the format you specified.

### Logging

Logs are saved in `app.log` in the root directory, with a maximum size of 5 MB per log file. The application maintains up to three log files.

## Configuration

The application settings can be customized via the `config.py` file:

- **File Extensions**: Modify `AUDIO_EXTENSIONS`, `VIDEO_EXTENSIONS`, `IMAGE_EXTENSIONS`, and `DOCUMENT_EXTENSIONS` to include or exclude specific file types.
- **API Rate Limiting**: Adjust `MIN_CALL_INTERVAL` to control the minimum interval between API calls.
- **Batch Size**: Change `BATCH_SIZE` to control the number of files processed in each batch.
- **GUI Settings**: Modify `WINDOW_TITLE` and `WINDOW_SIZE` to customize the appearance of the GUI.

## Error Handling

The application includes error handling for common issues such as:

- Invalid Dropbox access tokens
- API rate limiting errors
- Network connectivity issues

Critical errors are logged and displayed to the user via a message box.

## Contributing

Contributions are welcome! If you'd like to contribute, please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

