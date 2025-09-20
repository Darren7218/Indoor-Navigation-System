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
        self.last_qr_data = None
        self.last_detection_time = 0

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

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
                    'detection_interval': 1.0,
                    'confidence_threshold': 0.8
                }
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return {}
    
