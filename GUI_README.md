# QR Reader GUI - Indoor Navigation System

This module provides a graphical user interface for the QR code reader with live camera feed display.

## Features

- **Live Camera Feed**: Real-time display of webcam feed
- **QR Code Detection**: Automatic detection and decoding of QR codes
- **Location Data Display**: Shows parsed location information from detected QR codes
- **Recent Detections**: Keeps track of the last 10 detected QR codes
- **Camera Controls**: Start/stop camera and toggle scanning
- **Visual Overlay**: Green bounding boxes and text overlays on detected QR codes

## Files

- `qr_reader_ui.py` - Main GUI application
- `demo_gui.py` - Simple demo to test PyQt5 installation
- `qr_reader.py` - Core QR reading functionality (enhanced for GUI)

## Requirements

- Python 3.6+
- PyQt5 (already in requirements.txt)
- OpenCV (opencv-python)
- pyzbar (for QR code detection)

## Usage

### 1. Test PyQt5 Installation

First, test if PyQt5 is working correctly:

```bash
python demo_gui.py
```

This will open a simple demo window. If you can see it, PyQt5 is working correctly.

### 2. Run the Full GUI

```bash
python qr_reader_ui.py
```

### 3. GUI Controls

- **Start Camera**: Initializes and starts the webcam
- **Stop Camera**: Stops the camera and releases resources
- **Start Scanning**: Begins QR code detection (only works when camera is running)
- **Stop Scanning**: Pauses QR code detection

### 4. Camera Feed Display

The left panel shows:
- Live camera feed (640x480 minimum)
- Camera status indicator
- QR code detection overlays

### 5. Information Panel

The right panel displays:
- **Camera Controls**: Start/stop buttons
- **QR Code Information**: Details of the most recently detected QR code
- **Recent Detections**: List of the last 10 detected locations

## QR Code Format Support

The system supports multiple QR code data formats:

### JSON Format (Recommended)
```json
{
  "location_id": "ROOM_101",
  "floor_level": "1",
  "coordinates": "10,20",
  "description": "Main Office"
}
```

### CSV Format
```
ROOM_102,2,15,25,Conference Room
```

### Simple Text
```
EXIT_A
```

## Integration with Main System

The GUI integrates seamlessly with your existing indoor navigation system:

- Uses the same `QRCodeReader` class
- Returns `LocationData` objects
- Follows the same configuration system
- Compatible with `main.py` imports

## Troubleshooting

### Camera Not Starting
- Check if webcam is available
- Ensure no other application is using the camera
- Try different camera index in config.json

### PyQt5 Import Errors
- Install PyQt5: `pip install PyQt5`
- Check Python version compatibility

### QR Codes Not Detecting
- Ensure good lighting
- Hold QR code steady and close to camera
- Check if QR code is properly formatted

## Performance Notes

- Camera runs at ~30 FPS for smooth display
- QR detection is limited by the detection interval (default: 1 second)
- GUI runs in separate thread to prevent freezing

## Customization

You can customize the GUI by modifying:
- Camera resolution in config.json
- Detection intervals
- UI colors and styling
- Overlay appearance

## Example Usage in Code

```python
from qr_reader_ui import QRReaderGUI
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = QRReaderGUI()
window.show()
sys.exit(app.exec_())
```

## Next Steps

1. Test the GUI with your webcam
2. Create sample QR codes with location data
3. Integrate with your navigation system
4. Customize the interface as needed
