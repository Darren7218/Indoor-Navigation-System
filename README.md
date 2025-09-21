# Indoor Navigation System for FICT Building

This project is an indoor navigation system designed for the FICT Building, utilizing QR codes for precise localization. The system is built with Python and features a graphical user interface (GUI) created with PyQt5. It uses OpenCV for computer vision tasks, including QR code detection, and NetworkX for efficient route planning.

## Features

-   **QR Code-Based Localization**: Uses color-coded QR codes to determine the user's current location within the building.
-   **Graphical User Interface (GUI)**: An accessible and user-friendly interface built with PyQt5.
-   **Real-Time Camera Feed**: Displays a live feed from the camera to detect QR codes.
-   **Route Planning**: Calculates the optimal route to a selected destination using the A* pathfinding algorithm.
-   **Turn-by-Turn Navigation**: Provides turn-by-turn instructions to guide the user.
-   **Text-to-Speech Feedback**: Offers audio cues and instructions for navigation.
-   **Customizable Themes**: Supports both light and dark modes, with a high-contrast option for accessibility.

## Installation

To get started with the project, clone the repository and install the necessary dependencies.

```bash
git clone <repository-url>
cd IndoorNavProj
pip install -r requirements.txt
```

## Generate QR Code
```bash
python generate_fic_building_qr
```


## Usage

The application can be run in two modes:

-   **GUI Mode (Default)**:
    ```bash
    python main.py
    ```
    Alternatively:
    ```bash
    python main.py --gui
    ```

-   **FICT Navigation Mode (CLI)**:
    ```bash
    python main.py --fict
    ```

## Configuration

You can customize the application's settings by modifying the `config.py` file.

### Theme Settings

Adjust the visual theme of the UI:

```python
UI_SETTINGS = {
    'theme': 'dark',  # Available options: 'light' or 'dark'
    'high_contrast': True
}
```

### Audio Settings

Configure the text-to-speech feedback:

```python
AUDIO_SETTINGS = {
    'voice_rate': 150,        # Words per minute
    'voice_volume': 0.9,      # Volume (from 0.0 to 1.0)
    'beep_frequency': 1000,   # Frequency in Hz
    'beep_duration': 0.1      # Duration in seconds
}
```

### Detection Settings

For improved QR code detection in challenging conditions, you can enable advanced detection models.

-   **YOLO Proposals** (requires `ultralytics` and `torch`):
    ```python
    YOLO_SETTINGS = {
        'enabled': False,
        'weights_path': 'models/qr_yolo.pt',
    }
    ```

-   **QRDet Detector** (requires `qrdet`):
    ```python
    QRDET_SETTINGS = {
        'enabled': True,
        'model_size': 's',
    }
    ```

## Project Structure

The project is organized into the following modules:

```
IndoorNavProj/
├── main.py                           # Main system entry point
├── config.py                         # Configuration and settings
├── user_interface.py                 # Accessible UI module
├── fic_navigation_integration.py     # FICT Building navigation logic
├── qr_detection.py                   # QR code detection module
├── qr_reader.py                      # QR code reading module
├── audio_feedback.py                 # Text-to-speech module
├── requirements.txt                  # Python dependencies
├── data/                             # Data files, including QR codes
├── logs/                             # System logs
└── cache/                            # Temporary files
```

## Troubleshooting

-   **Audio Not Working**: If the audio feedback fails after clicking the "Calculate Route" button, check your system's audio device connections and settings.
-   **Route Calculation Fails**: Ensure that the building data is loaded correctly and that the navigation graph is properly connected.

## Future Improvements

-   **Android Application**: Develop an Android-compatible version of the application for mobile use.

