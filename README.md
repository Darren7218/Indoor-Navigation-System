# Indoor Navigation System

A comprehensive indoor navigation system designed specifically for visually impaired users, featuring QR code detection, route guidance, and an accessible user interface.

## 🎯 Features

### 3.3.1 QR Code Detection
- **Real-time webcam capture** with continuous frame processing
- **Color-coded QR detection** for red, green, and blue QR codes
- **HSV color segmentation** for robust detection under varying lighting conditions
- **Size threshold detection** to enter reading mode automatically
- **Fast HSV calibration** for consistent detection across different environments
- **Voice cues and beep sounds** for centering assistance

### 3.3.2 QR Code Reading
- **Dual decoding system**:
  - Primary: OpenCV's QRCodeDetector
  - Fallback: Pyzbar library for improved robustness
- **Predefined schema support** containing:
  - Node ID
  - Coordinates (x, y)
  - Floor level
  - Available exits
- **Text-to-speech location announcements**
- **Automatic route guidance initiation**

### 3.3.3 Route Guidance
- **Weighted graph representation** of floor maps
- **A* pathfinding algorithm** with straight-line distance heuristic
- **Dijkstra's algorithm fallback** when A* fails
- **Accessibility scoring** for route optimization
- **Turn-by-turn instructions** with distances and checkpoints
- **Strategic QR code scanning** for location confirmation
- **Route recalculation** capabilities

### 3.3.4 User Interface
- **Accessible design** optimized for visually impaired users
- **High-contrast interface** with large, clear text
- **Audio feedback system** with text-to-speech
- **Tactile feedback** through beep sounds
- **Keyboard shortcuts** for easy navigation
- **Real-time camera feed** with detection overlays
- **Progress tracking** and status monitoring

## 🛠️ Technical Specifications

### Programming Language
- **Primary**: Python 3.11+ (for rapid prototyping and extensive library support)
- **Alternative**: C++17 (for high-performance components if needed)

### Core Libraries
- **OpenCV 4.7+**: Computer vision, color segmentation, QR detection
- **Pyzbar**: QR code decoding fallback
- **PyQt5/Qt6**: Advanced UI features and accessibility
- **NetworkX**: Graph algorithms and pathfinding
- **NumPy**: Numerical processing
- **pyttsx3**: Text-to-speech (offline compatible)

### Hardware Requirements
- **Computer**: Laptop or PC with 720p/1080p webcam
- **Audio**: Internal or external speakers
- **Optional**: Phone-based sensors (compass for mobile implementations)

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

### Step 3: Verify Installation
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

#### Command Line Testing Mode
```bash
python main.py --cli
```

### System Operation

1. **Start the System**
   - Launch the application
   - System initializes with audio feedback

2. **Camera Setup**
   - Click "Start Camera" or press 'C'
   - System begins scanning for color-coded QR codes

3. **QR Code Detection**
   - Point camera at red, green, or blue QR codes
   - System automatically detects and enters reading mode
   - Voice feedback confirms detection

4. **Location Identification**
   - QR code is decoded to determine current location
   - Location is announced via text-to-speech
   - Current position displayed on interface

5. **Route Planning**
   - Select destination from dropdown menu
   - Click "Calculate Route" or press 'R'
   - System calculates optimal path using A* algorithm

6. **Navigation**
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
- **Test Audio**: Verify audio system functionality

## 🗺️ Floor Map Configuration

The system uses a weighted graph representation where:
- **Nodes**: Doors, intersections, landmarks, exits
- **Edges**: Corridors with distance and accessibility weights
- **Weights**: Distance + accessibility penalties

### Sample Floor Layout
```
A1 (Entrance) ----10m---- B1 (Intersection) ----10m---- C1 (Intersection)
    |                           |                           |
    |                           |                           |
   10m                         10m                         10m
    |                           |                           |
    v                           v                           v
A2 (Intersection) ----10m---- B2 (Intersection) ----10m---- C2 (Intersection)
    |                           |                           |
    |                           |                           |
   10m                         10m                         10m
    |                           |                           |
    v                           v                           v
A3 (Landmark) ----10m---- B3 (Landmark) ----10m---- C3 (Exit)
```

## 🔧 Configuration

### Color Detection Thresholds
Adjust HSV values in `config.py` for different lighting conditions:
```python
COLOR_THRESHOLDS = {
    'red': {
        'lower1': [0, 100, 100],
        'upper1': [10, 255, 255],
        'lower2': [160, 100, 100],
        'upper2': [180, 255, 255]
    },
    # ... green and blue thresholds
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

### Navigation Parameters
```python
NAVIGATION = {
    'recalculation_threshold': 5.0,    # Meters
    'checkpoint_distance': 10.0,       # Meters
    'turn_announcement_distance': 3.0  # Meters
}
```

## 🧪 Testing

### Command Line Testing
```bash
python main.py --cli
```
This mode tests:
- QR detection system
- Route calculation algorithms
- Audio feedback systems
- System integration

### Individual Module Testing
```bash
# Test QR detection
python qr_detection.py

# Test QR reading
python qr_reader.py

# Test route guidance
python route_guidance.py

# Test user interface
python user_interface.py
```

## 📁 Project Structure
```
IndoorNavProj/
├── main.py                 # Main system entry point
├── config.py               # Configuration and settings
├── qr_detection.py         # QR code detection module
├── qr_reader.py            # QR code reading module
├── route_guidance.py       # Route calculation module
├── user_interface.py       # Accessible UI module
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Floor maps and schemas
├── logs/                  # System logs
└── cache/                 # Audio and temporary files
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
- Verify floor map data is properly formatted
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

- OpenCV community for computer vision capabilities
- PyQt developers for accessible UI framework
- NetworkX team for graph algorithms
- Accessibility advocates for design guidance

## 📞 Support

For technical support or questions:
- Check the troubleshooting section
- Review system logs in the `logs/` directory
- Open an issue on the project repository

---

**Note**: This system is designed for educational and research purposes. Always test thoroughly in your specific environment before deploying in production settings.
