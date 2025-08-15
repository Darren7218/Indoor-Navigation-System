"""
QR Code Reading Module
Dual decoding with OpenCV's QRCodeDetector and Pyzbar fallback
Decodes location data following predefined schema
"""

import cv2
import numpy as np
from pyzbar import pyzbar
import time
import logging
from typing import Optional, Tuple, Dict, Any
import json
import os

class LocationData:
    """
    Data structure for location information extracted from QR codes.
    """
    
    def __init__(self, qr_data: str, confidence: float = 1.0):
        """
        Initialize location data from QR code.
        
        Args:
            qr_data (str): Raw QR code data
            confidence (float): Confidence level of the detection (0.0 to 1.0)
        """
        self.raw_data = qr_data
        self.confidence = confidence
        self.timestamp = time.time()
        
        # Parse location data
        self.location_id = None
        self.floor_level = None
        self.coordinates = None
        self.description = None
        
        self._parse_location_data()
    
    def _parse_location_data(self):
        """Parse the QR code data to extract location information."""
        try:
            # Try to parse as JSON first
            if self.raw_data.startswith('{') and self.raw_data.endswith('}'):
                data = json.loads(self.raw_data)
                self.location_id = data.get('location_id')
                self.floor_level = data.get('floor_level')
                self.coordinates = data.get('coordinates')
                self.description = data.get('description')
            else:
                # Try to parse as comma-separated values
                parts = self.raw_data.split(',')
                if len(parts) >= 3:
                    self.location_id = parts[0].strip()
                    self.floor_level = parts[1].strip()
                    self.coordinates = parts[2].strip()
                    if len(parts) > 3:
                        self.description = parts[3].strip()
                else:
                    # Fallback: treat as simple location ID
                    self.location_id = self.raw_data.strip()
                    
        except Exception as e:
            # If parsing fails, use raw data as location ID
            self.location_id = self.raw_data.strip()
    
    def is_valid(self) -> bool:
        """Check if the location data is valid."""
        return self.location_id is not None and len(self.location_id) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert location data to dictionary."""
        return {
            'location_id': self.location_id,
            'floor_level': self.floor_level,
            'coordinates': self.coordinates,
            'description': self.description,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'raw_data': self.raw_data
        }
    
    def __str__(self) -> str:
        """String representation of location data."""
        if self.is_valid():
            return f"Location: {self.location_id} (Floor: {self.floor_level or 'Unknown'})"
        return f"Invalid Location Data: {self.raw_data}"

class QRCodeReader:
    """
    A class to handle QR code reading from webcam feed.
    Integrates with the indoor navigation system to read location QR codes.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the QR code reader.
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.camera = None
        self.is_running = False
        self.last_qr_data = None
        self.last_detection_time = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Camera settings
        self.camera_index = self.config.get('camera_index', 0)
        self.frame_width = self.config.get('frame_width', 640)
        self.frame_height = self.config.get('frame_height', 480)
        self.fps = self.config.get('fps', 30)
        
        # QR detection settings
        self.detection_interval = self.config.get('detection_interval', 1.0)  # seconds
        self.confidence_threshold = self.config.get('confidence_threshold', 0.8)
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                return {
                    'camera_index': 0,
                    'frame_width': 640,
                    'frame_height': 480,
                    'fps': 30,
                    'detection_interval': 1.0,
                    'confidence_threshold': 0.8
                }
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return {}
    
    def start_camera(self) -> bool:
        """
        Start the webcam capture.
        
        Returns:
            bool: True if camera started successfully, False otherwise
        """
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self.logger.error(f"Could not open camera at index {self.camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.is_running = True
            self.logger.info(f"Camera started successfully at {self.frame_width}x{self.frame_height}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            return False
    
    def stop_camera(self):
        """Stop the webcam capture."""
        if self.camera:
            self.camera.release()
        self.is_running = False
        self.logger.info("Camera stopped")
    
    def read_qr_code(self) -> Optional[LocationData]:
        """
        Read a single frame and detect QR codes.
        
        Returns:
            Optional[LocationData]: Location data if QR code detected, None otherwise
        """
        if not self.camera or not self.is_running:
            return None
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                return None
            
            # Convert to grayscale for better QR detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect QR codes
            qr_codes = pyzbar.decode(gray)
            
            if qr_codes:
                for qr in qr_codes:
                    qr_data = qr.data.decode('utf-8')
                    
                    # Check if enough time has passed since last detection
                    if (time.time() - self.last_detection_time) >= self.detection_interval:
                        # Create LocationData object
                        location_data = LocationData(qr_data)
                        # Store original QR detection data for overlay drawing
                        location_data._qr_rect = qr.rect
                        location_data._qr_polygon = qr.polygon
                        self.last_qr_data = location_data
                        self.last_detection_time = time.time()
                        self.logger.info(f"QR Code detected: {location_data}")
                        return location_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading QR code: {e}")
            return None
    
    def continuous_scan(self, callback=None, max_duration: Optional[float] = None):
        """
        Continuously scan for QR codes.
        
        Args:
            callback: Function to call when QR code is detected (receives LocationData)
            max_duration: Maximum duration to scan (None for infinite)
        """
        if not self.start_camera():
            return
        
        start_time = time.time()
        
        try:
            while self.is_running:
                # Check if max duration exceeded
                if max_duration and (time.time() - start_time) > max_duration:
                    break
                
                location_data = self.read_qr_code()
                
                if location_data and callback:
                    callback(location_data)
                
                # Add small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
                # Check for 'q' key to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("Scanning interrupted by user")
        finally:
            self.stop_camera()
            cv2.destroyAllWindows()
    
    def get_camera_feed(self):
        """Get the current camera frame for display purposes."""
        if not self.camera or not self.is_running:
            return None
        
        ret, frame = self.camera.read()
        if ret:
            return frame
        return None
    
    def draw_qr_overlay(self, frame, qr_data: LocationData):
        """
        Draw QR code detection overlay on frame.
        
        Args:
            frame: OpenCV frame
            qr_data: LocationData object
        """
        if not qr_data:
            return frame
        
        # Draw bounding box if available
        if hasattr(qr_data, '_qr_rect') and qr_data._qr_rect:
            x, y, w, h = qr_data._qr_rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw polygon if available
            if hasattr(qr_data, '_qr_polygon') and qr_data._qr_polygon:
                points = np.array(qr_data._qr_polygon, np.int32)
                points = points.reshape((-1, 1, 2))
                cv2.polylines(frame, [points], True, (255, 0, 0), 2)
        
        # Draw text overlay
        text = f"Location: {qr_data.location_id}"
        if qr_data.floor_level:
            text += f" (Floor: {qr_data.floor_level})"
        
        # Position text at top-left corner
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw a border around the frame to indicate detection
        height, width = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (width-1, height-1), (0, 255, 0), 3)
        
        return frame
    
    def test_camera(self):
        """Test camera functionality and display feed."""
        if not self.start_camera():
            print("Failed to start camera")
            return
        
        print("Camera test started. Press 'q' to quit.")
        
        try:
            while True:
                frame = self.get_camera_feed()
                if frame is None:
                    continue
                
                # Try to detect QR codes
                location_data = self.read_qr_code()
                
                # Draw overlay if QR code detected
                if location_data:
                    frame = self.draw_qr_overlay(frame, location_data)
                
                # Display frame
                cv2.imshow('QR Code Scanner Test', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_camera()
            cv2.destroyAllWindows()


def main():
    """Main function for testing the QR reader."""
    qr_reader = QRCodeReader()
    
    print("QR Code Reader Test")
    print("1. Test camera feed")
    print("2. Continuous scan")
    print("3. Single scan")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == '1':
        qr_reader.test_camera()
    elif choice == '2':
        def on_qr_detected(location_data):
            print(f"Location detected: {location_data}")
        qr_reader.continuous_scan(callback=on_qr_detected)
    elif choice == '3':
        if qr_reader.start_camera():
            print("Scanning for QR code... Press 'q' to quit")
            while True:
                location_data = qr_reader.read_qr_code()
                if location_data:
                    print(f"Location detected: {location_data}")
                    break
                
                frame = qr_reader.get_camera_feed()
                if frame is not None:
                    cv2.imshow('QR Scanner', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            qr_reader.stop_camera()
            cv2.destroyAllWindows()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
