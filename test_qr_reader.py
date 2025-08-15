#!/usr/bin/env python3
"""
Test script for the QR Reader module.
This script demonstrates how to use the QRCodeReader and LocationData classes.
"""

from qr_reader import QRCodeReader, LocationData
import time

def test_location_data():
    """Test the LocationData class with different input formats."""
    print("Testing LocationData class...")
    
    # Test with JSON format
    json_data = '{"location_id": "ROOM_101", "floor_level": "1", "coordinates": "10,20", "description": "Main Office"}'
    location1 = LocationData(json_data)
    print(f"JSON input: {location1}")
    print(f"  Valid: {location1.is_valid()}")
    print(f"  Dict: {location1.to_dict()}")
    
    # Test with comma-separated format
    csv_data = "ROOM_102,2,15,25,Conference Room"
    location2 = LocationData(csv_data)
    print(f"\nCSV input: {location2}")
    print(f"  Valid: {location2.is_valid()}")
    print(f"  Dict: {location2.to_dict()}")
    
    # Test with simple text
    simple_data = "EXIT_A"
    location3 = LocationData(simple_data)
    print(f"\nSimple input: {location3}")
    print(f"  Valid: {location3.is_valid()}")
    print(f"  Dict: {location3.to_dict()}")
    
    print("\n" + "="*50 + "\n")

def test_qr_reader():
    """Test the QRCodeReader class."""
    print("Testing QRCodeReader class...")
    
    qr_reader = QRCodeReader()
    
    print("1. Testing camera initialization...")
    if qr_reader.start_camera():
        print("   ✓ Camera started successfully")
        
        print("2. Testing single QR code read...")
        print("   Point your camera at a QR code...")
        
        # Try to read a QR code for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            location_data = qr_reader.read_qr_code()
            if location_data:
                print(f"   ✓ QR Code detected: {location_data}")
                break
            time.sleep(0.5)
        else:
            print("   ⚠ No QR code detected in 10 seconds")
        
        print("3. Stopping camera...")
        qr_reader.stop_camera()
        print("   ✓ Camera stopped")
    else:
        print("   ✗ Failed to start camera")
        print("   This might be due to:")
        print("   - No webcam available")
        print("   - Webcam in use by another application")
        print("   - Permission issues")
    
    print("\n" + "="*50 + "\n")

def main():
    """Main test function."""
    print("QR Reader Test Suite")
    print("="*50)
    
    # Test LocationData class
    test_location_data()
    
    # Test QRCodeReader class
    test_qr_reader()
    
    print("Test completed!")
    print("\nTo test with live camera feed, run:")
    print("python qr_reader.py")

if __name__ == "__main__":
    main()
