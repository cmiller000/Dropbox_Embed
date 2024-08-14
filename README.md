
# Dropbox Media Links Generator

## Overview

The **Dropbox Media Links Generator** is a Python-based tool designed to streamline the process of generating shareable media links from your Dropbox files. Whether you’re a content creator, educator, or just looking to share media quickly and efficiently, this tool provides a user-friendly interface and robust functionality to meet your needs.

## Features

- **Seamless Dropbox Integration**: connect your Dropbox account using an access token.
- **Selective File Link Generation**: Focus on specific file types (audio, video, images, documents) for link generation.
- **Non-blocking Asynchronous Operations**: Handle large media libraries with ease.
- **Intuitive Folder Navigation**: Browse your Dropbox folders within the application.
- **Real-time Progress Updates**: Stay informed with on-screen progress tracking.
- **Comprehensive Logging**: Easily monitor and debug with detailed logs.

## Installation

### Prerequisites

- Python 3.7 or higher
- A Dropbox account with API access
- `pip` package manager

### Setup

1. **Clone the Repository**:

    ```
    git clone https://github.com/cmiller000/Dropbox_Embed.git
    cd Dropbox_Embed
    ```

2. **Install Required Packages**:

    The application automatically checks for required packages and installs them if necessary.
   

4. **Set Up Environment Variables**:

    Create a `.env` file in the root directory and add your Dropbox access token:

    ```
    DROPBOX_ACCESS_TOKEN=your_access_token_here
    ```

    Alternatively, you will be prompted to enter your access token upon starting the application.
   
![Python --14-08 2024 _001684](https://github.com/user-attachments/assets/d45d0d11-b7db-4419-b8c8-f0d4872faf6b)

   

## Usage

### Running the Application

Start the application using Python:

```
python main.py
```

### Using the GUI

![Python --14-08 2024 _001682](https://github.com/user-attachments/assets/7246f22a-d0e5-495a-8246-245cb17831da)


1. **Enter Dropbox Token**: Upon launching, you'll be prompted to enter your Dropbox access token if not already set. The token entry dialog will appear as shown below:

   ![Dropbox Token Entry](Python --14-08 2024 _001684.png)

2. **Browse Folders**: Use the folder browser to navigate through your Dropbox directories. Click on the "Browse Dropbox" button to select the desired folder path. 

   ![Dropbox Media Links Generator](Python --14-08 2024 _001682.png)

3. **Select Output File**: Choose the location and name for the output file by clicking the "Browse" button next to the "Output File" field.
4. **Select File Types**: Choose the types of files you want to generate links for by selecting the checkboxes for "Audio" and/or "Video."
5. **Generate Links**: Click on the "Generate Links" button to start the process. The application will process the selected files and generate shareable links in the format of your choice.
6. **Progress Monitoring**: You can monitor the progress of link generation through the progress bar.
7. **Stop Processing**: If you wish to halt the operation, you can click the "Stop Processing" button.
8. **Reset Token**: If you need to change or reset your Dropbox token, click the "Reset Token" button.

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

We welcome contributions to improve the Dropbox Media Links Generator! If you'd like to contribute, please fork the repository, make your changes, and submit a pull request. Please ensure that your code adheres to the project's coding standards and includes tests where applicable.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
