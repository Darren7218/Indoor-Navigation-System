# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## High-level Code Architecture

This is an indoor navigation system for the FICT Building, using QR codes for localization. The system is written in Python and uses OpenCV for computer vision, PyQt5 for the GUI, and NetworkX for route planning. Other key libraries include `pyttsx3` for text-to-speech and `qrcode` for QR code generation.

### Core Modules and Data Flow

1.  **`main.py`**: The entry point of the application. It initializes the system, parses command-line arguments, and starts the appropriate mode (GUI or FICT-specific CLI).

2.  **`config.py`**: A centralized configuration hub that stores all settings for the application, including color thresholds for QR detection, audio feedback parameters, UI settings, and theme definitions.

3.  **`user_interface.py`**: This module manages the PyQt5-based GUI. It features a `CameraThread` for non-blocking camera operations and a `NavigationInterface` that orchestrates user interactions. It communicates with the other modules to display camera feeds, handle user input, and present navigation instructions.

4.  **`fic_navigation_integration.py`**: The core of the navigation logic. The `FICTNavigationSystem` class loads the building's location data, constructs a navigation graph for each floor using NetworkX, and calculates the optimal route using the A* pathfinding algorithm.

5.  **`qr_detection.py` & `qr_reader.py`**: These modules work together to handle QR code detection and decoding. `qr_detection.py` uses OpenCV to identify color-coded QR codes in the camera feed, and `qr_reader.py` decodes them to extract location data.

6.  **`audio_feedback.py`**: Manages the text-to-speech functionality, providing audio cues and instructions to the user.

### Data Flow

- **QR Detection**: The `CameraThread` in `user_interface.py` captures frames and uses `qr_detection.py` to find potential QR codes.
- **Location Identification**: Once a QR code is detected, `qr_reader.py` decodes it, and the location data is passed to `fic_navigation_integration.py` to set the user's current location.
- **Route Calculation**: When the user selects a destination in the UI, `user_interface.py` calls `fic_navigation_integration.py` to calculate the route.
- **Navigation Guidance**: The calculated route is then displayed in the UI, and the turn-by-turn instructions are spoken to the user via `audio_feedback.py`.

## Project Structure
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

## Common Commands

### Installation

To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd IndoorNavProj
pip install -r requirements.txt
```


### Running the Application

The system can be run in two different modes:

- **GUI Mode (Default)**: `python main.py` or `python main.py --gui`
- **FICT Navigation Mode**: `python main.py --fict`


## Configuration
Key settings can be adjusted in `config.py`.

### Theme Settings
```python
UI_SETTINGS = {
    'theme': 'dark',  # 'light' or 'dark'
    'high_contrast': True
}
```

### Audio Settings
```python
AUDIO_SETTINGS = {
    'voice_rate': 150,        # Words per minute
    'voice_volume': 0.9,      # Volume (0.0 to 1.0)
    'beep_frequency': 1000,   # Hz
    'beep_duration': 0.1      # Seconds
}
```

### Detection Settings (optional)
Enable stronger proposals to help the OpenCV decoder in tough conditions.
```python
# YOLO proposals (requires ultralytics + torch)
YOLO_SETTINGS = {
    'enabled': False,
    'weights_path': 'models/qr_yolo.pt',
}

# QRDet specialized detector (pip install qrdet)
QRDET_SETTINGS = {
    'enabled': True,
    'model_size': 's',
}
```

## Troubleshooting

- **Audio Not Working**: Verify audio device connection and system settings. (when app open, it worked. It failed after tapping the calculate route button)
- **Route Calculation Fails**: Verify building data is loaded correctly and that the navigation graph is connected.


## Further Improvement after troubleshooting done
- **Create Andriod App**: make an Andriod compatible app for user
