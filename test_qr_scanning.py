#!/usr/bin/env python3
"""
Test script for QR code scanning functionality
"""

import sys
import time
from qr_reader import QRCodeReader, LocationData
from qr_detection import QRCodeDetector

def test_qr_reader():
    """Test the QRCodeReader class"""
    print("Testing QRCodeReader...")
    
    reader = QRCodeReader()
    
    # Test camera start
    print("Starting camera...")
    if reader.start_camera():
        print("✓ Camera started successfully")
        
        # Test QR reading for a few seconds
        print("Scanning for QR codes (5 seconds)...")
        start_time = time.time()
        
        while time.time() - start_time < 5:
            location_data = reader.read_qr_code()
            if location_data:
                print(f"✓ QR Code detected: {location_data}")
                break
            time.sleep(0.1)
        else:
            print("No QR codes detected in 5 seconds")
        
        reader.stop_camera()
        print("✓ Camera stopped")
    else:
        print("✗ Failed to start camera")

def test_qr_detection():
    """Test the QRCodeDetector class"""
    print("\nTesting QRCodeDetector...")
    
    detector = QRCodeDetector()
    
    if detector.cap and detector.cap.isOpened():
        print("✓ Camera initialized successfully")
        
        # Test detection for a few seconds
        print("Scanning for color-coded QR codes (5 seconds)...")
        start_time = time.time()
        
        while time.time() - start_time < 5:
            if detector.is_qr_detected():
                detected_qrs = detector.get_detected_qrs()
                print(f"✓ QR codes detected: {len(detected_qrs)}")
                for color, roi, bbox in detected_qrs:
                    print(f"  - Color: {color}, BBox: {bbox}")
                break
            time.sleep(0.1)
        else:
            print("No QR codes detected in 5 seconds")
        
        detector.stop_detection()
        print("✓ Detection stopped")
    else:
        print("✗ Failed to initialize camera")

def test_location_data():
    """Test LocationData parsing"""
    print("\nTesting LocationData parsing...")
    
    # Test JSON format
    json_data = '{"location_id": "TEST001", "floor_level": 1, "coordinates": [10, 20], "description": "Test Location"}'
    location = LocationData(json_data)
    print(f"✓ JSON parsing: {location}")
    
    # Test CSV format
    csv_data = "TEST002,2,15,25,Another Test"
    location = LocationData(csv_data)
    print(f"✓ CSV parsing: {location}")
    
    # Test simple format
    simple_data = "TEST003"
    location = LocationData(simple_data)
    print(f"✓ Simple parsing: {location}")

if __name__ == "__main__":
    print("QR Code Scanning Test Suite")
    print("=" * 40)
    
    try:
        test_location_data()
        test_qr_reader()
        test_qr_detection()
        
        print("\n" + "=" * 40)
        print("Test completed!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
