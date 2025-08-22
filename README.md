# FICT Building Navigation System

A specialized indoor navigation system designed for the FICT Building, featuring QR code detection, route guidance, and an accessible user interface optimized for visually impaired users.

## 🎯 Features

### QR Code Detection & Generation
- **Color-coded QR codes**: Blue for Ground Floor, Red for First Floor
- **Real-time webcam capture** with continuous frame processing
- **HSV color segmentation** for robust detection under varying lighting conditions
- **Automated QR generation** for all 149 FICT Building locations
- **Optional robust detectors**: YOLOv8 proposals and QRDet-based specialized QR detection

### Navigation System
- **149 FICT Building locations** across 2 floors
- **A* pathfinding algorithm** with accessibility considerations
- **Turn-by-turn instructions** with distance and time estimates
- **Floor change detection** and routing
- **Location search** by name, description, or type

### User Interface
- **Light/Dark theme switching** with high contrast mode
- **Accessible design** optimized for visually impaired users
- **Audio feedback system** with text-to-speech
- **Real-time camera feed** with detection overlays
- **Menu-driven navigation** with keyboard shortcuts

## 🛠️ Technical Specifications

### Core Libraries
- **OpenCV 4.7+**: Computer vision and QR detection
- **PyQt5**: Advanced UI with accessibility features
- **NetworkX**: Graph algorithms and pathfinding
- **pyttsx3**: Text-to-speech (offline compatible)
- **qrcode**: QR code generation
- **ultralytics**: YOLOv8 object detection (optional for QR proposals)
- **qrdet**: Robust QR detector (YOLOv8-based) for difficult cases (optional)

### Hardware Requirements
- **Computer**: Laptop or PC with 720p/1080p webcam
- **Audio**: Internal or external speakers
- **Storage**: 100MB for QR codes and maps

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- Webcam (built-in or external)
- Speakers or headphones

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd IndoorNavProj
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Generate FICT Building QR Codes
```bash
python generate_fic_building_qr.py
```

### Step 4: Verify Installation
```bash
python main.py --help
```

## 🚀 Usage

### Starting the System

#### Graphical User Interface (Default)
```bash
python main.py
# or
python main.py --gui
```

#### FICT Navigation Mode
```bash
python main.py --fict
```

#### Command Line Testing
```bash
python main.py --cli
```

### System Operation

1. **Start the System**
   - Launch the application
   - System initializes with audio feedback

2. **Theme Selection**
   - Use View → Theme menu to switch between Light and Dark themes
   - Toggle High Contrast mode for accessibility

3. **Camera Setup**
   - Click "Start Camera" or press 'C'
   - System begins scanning for color-coded QR codes

4. **QR Code Detection**
   - Point camera at FICT Building QR codes
   - Blue QR codes = Ground Floor locations
   - Red QR codes = First Floor locations
   - System automatically detects and enters reading mode

5. **Location Identification**
   - QR code is decoded to determine current location
   - Location is announced via text-to-speech
   - Current position displayed on interface

6. **Route Planning**
   - Select destination from dropdown menu
   - Click "Calculate Route" or press 'R'
   - System calculates optimal path using A* algorithm

7. **Navigation**
   - Turn-by-turn instructions are provided
   - Audio cues guide user through route
   - Progress tracking shows completion status

### Keyboard Shortcuts
- **Spacebar**: Toggle audio feedback
- **C**: Start/Stop camera
- **R**: Recalculate route
- **Escape**: Close application

### Audio Controls
- **Volume Slider**: Adjust audio volume (0-100%)
- **Speech Rate**: Control TTS speed (50-300 words/min)
- **Audio Toggle**: Enable/disable all audio feedback

## 🗺️ FICT Building Layout

### Ground Floor (Blue QR Codes Frame)
- **77 locations** including:
  - Main entrance and exits
  - Lecture halls and classrooms
  - Administrative offices
  - Common areas and facilities

### First Floor (Red QR Codes Frame)
- **72 locations** including:
  - Faculty offices
  - Research laboratories
  - Conference rooms
  - Student facilities

### Important Locations
- **4 special QR codes** for key areas:
  - Main entrance
  - Emergency exits
  - Information desk
  - Accessibility features

## 🔧 Configuration

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
    'img_size': 640,
    'conf_threshold': 0.25,
    'iou_threshold': 0.45,
    'max_det': 50,
}

# QRDet specialized detector (pip install qrdet)
QRDET_SETTINGS = {
    'enabled': True,
    'model_size': 's',
    'conf_th': 0.5,
    'nms_iou': 0.3,
}
```

## 🧪 Testing

### System Testing
```bash
python test_system.py
```

### QR Code Generation Testing
```bash
python test_qr_generator.py
```

### Navigation Testing
```bash
python debug_test.py
```

## 📁 Project Structure
```
IndoorNavProj/
├── main.py                           # Main system entry point
├── config.py                         # Configuration and settings
├── qr_detection.py                   # QR code detection module
├── qr_reader.py                      # QR code reading module
├── route_guidance.py                 # Route calculation module
├── user_interface.py                 # Accessible UI module
├── fic_navigation_integration.py     # FICT Building navigation
├── generate_fic_building_qr.py       # QR code generation
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── data/qr_schemas/fic_building/     # Generated QR codes
│   ├── ground_floor/                 # 77 Blue QR codes
│   ├── first_floor/                  # 72 Red QR codes
│   └── important_locations/          # 4 Large QR codes
├── logs/                             # System logs
└── cache/                            # Temporary files
```

## 🔍 Troubleshooting

### Common Issues

#### Camera Not Working
- Ensure webcam is connected and not in use by other applications
- Check camera permissions in your operating system
- Try different camera index (0, 1, 2) in `qr_detection.py`

#### Audio Not Working
- Verify speakers/headphones are connected
- Check system audio settings
- Install required audio codecs for your OS

#### QR Code Detection Issues
- Ensure adequate lighting
- Use the HSV calibration tool for your environment
- Check QR code quality and size

#### Route Calculation Fails
- Verify FICT Building data is properly loaded
- Check that start and destination nodes exist
- Ensure graph connectivity

### Performance Optimization
- Reduce camera resolution for better performance
- Adjust frame processing rate
- Use SSD storage for faster file access
- Close unnecessary background applications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FICT Building administration for location data
- OpenCV community for computer vision capabilities
- PyQt developers for accessible UI framework
- NetworkX team for graph algorithms
- Accessibility advocates for design guidance
- QRDet by Eric Cañas for robust YOLOv8-based QR detection. See project: [qrdet](https://github.com/Eric-Canas/qrdet)

## 📞 Support

For technical support or questions:
- Check the troubleshooting section
- Review system logs in the `logs/` directory
- Open an issue on the project repository

---

**Note**: This system is specifically designed for the FICT Building. Always test thoroughly in your specific environment before deploying in production settings.

