"""
Test Script for Indoor Navigation System
Tests system components without requiring camera hardware
"""

import sys
import time
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing module imports...")
    
    try:
        from config import COLOR_THRESHOLDS, QR_DETECTION, AUDIO_SETTINGS
        print("✓ Configuration module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    try:
        from qr_reader import QRCodeReader, LocationData
        print("✓ QR Reader module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import QR reader: {e}")
        return False
    
    try:
        from route_guidance import RouteGuidance, NavigationRoute
        print("✓ Route Guidance module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import route guidance: {e}")
        return False
    
    try:
        # Test PyQt5 import
        from PyQt5.QtWidgets import QApplication
        print("✓ PyQt5 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt5: {e}")
        print("  Note: PyQt5 is required for the GUI interface")
        return False
    
    return True

def test_configuration():
    """Test configuration system"""
    print("\nTesting configuration system...")
    
    try:
        from config import create_directories, save_config, load_config
        
        # Test directory creation
        create_directories()
        print("✓ Directories created successfully")
        
        # Test configuration save/load
        save_config()
        print("✓ Configuration saved successfully")
        
        loaded_config = load_config()
        if loaded_config:
            print("✓ Configuration loaded successfully")
        else:
            print("✓ Using default configuration")
            
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_qr_reader():
    """Test QR code reading functionality"""
    print("\nTesting QR code reader...")
    
    try:
        from qr_reader import QRCodeReader
        
        reader = QRCodeReader()
        print("✓ QR Reader initialized successfully")
        
        # Test data parsing
        test_data = {
            "node_id": "A1",
            "coordinates": "10.5,20.3",
            "floor_level": 1,
            "exits": {
                "north": "A2",
                "east": "B1",
                "south": "A0"
            }
        }
        
        import json
        test_json = json.dumps(test_data)
        
        # Test parsing (this would normally come from QR detection)
        location = reader._parse_qr_data(test_json)
        
        if location:
            print("✓ QR data parsing successful")
            print(f"  Location: {location.node_id}")
            print(f"  Coordinates: {location.coordinates}")
            print(f"  Floor: {location.floor_level}")
            print(f"  Exits: {list(location.exits.keys())}")
        else:
            print("✗ QR data parsing failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ QR Reader test failed: {e}")
        return False

def test_route_guidance():
    """Test route guidance system"""
    print("\nTesting route guidance system...")
    
    try:
        from route_guidance import RouteGuidance
        from qr_reader import LocationData
        
        guidance = RouteGuidance()
        print("✓ Route Guidance initialized successfully")
        
        # Create test location
        test_location = LocationData(
            node_id="A1",
            coordinates=(0, 0),
            floor_level=1,
            exits={"north": "A2", "east": "B1"},
            timestamp=time.time(),
            confidence=0.9
        )
        
        # Calculate test route
        route = guidance.calculate_route(test_location, "C3")
        
        if route:
            print("✓ Route calculation successful")
            print(f"  Destination: {route.destination}")
            print(f"  Total distance: {route.total_distance:.1f} meters")
            print(f"  Estimated time: {route.estimated_time:.0f} seconds")
            print(f"  Number of segments: {len(route.segments)}")
            
            # Show route summary
            route_summary = guidance.get_route_summary(route)
            print("\nRoute Summary:")
            print("-" * 40)
            print(route_summary)
            print("-" * 40)
            
        else:
            print("✗ Route calculation failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Route Guidance test failed: {e}")
        return False

def test_audio_system():
    """Test audio feedback system"""
    print("\nTesting audio feedback system...")
    
    try:
        from user_interface import AudioFeedback
        
        audio = AudioFeedback()
        
        if audio.is_initialized:
            print("✓ Audio feedback system initialized successfully")
            
            # Test speech (optional - may be loud)
            test_speech = input("Test speech output? (y/n): ").lower().strip()
            if test_speech == 'y':
                audio.speak("Audio feedback test successful")
                print("✓ Speech test completed")
            else:
                print("✓ Speech test skipped")
                
        else:
            print("⚠ Audio feedback system not available")
            print("  This is normal if TTS engine is not installed")
            
        return True
        
    except Exception as e:
        print(f"✗ Audio system test failed: {e}")
        return False

def test_gui_creation():
    """Test GUI creation (without showing window)"""
    print("\nTesting GUI creation...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from user_interface import NavigationInterface
        
        # Create Qt application (required for GUI components)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create navigation interface
        gui = NavigationInterface()
        print("✓ GUI interface created successfully")
        
        # Clean up
        gui.close()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI creation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("INDOOR NAVIGATION SYSTEM - COMPONENT TESTING")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("QR Code Reader", test_qr_reader),
        ("Route Guidance", test_route_guidance),
        ("Audio Feedback", test_audio_system),
        ("GUI Creation", test_gui_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"✗ {test_name} test failed")
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nTo start the system:")
        print("  python main.py          # Start GUI")
        print("  python main.py --cli    # Run command-line tests")
    else:
        print("⚠ Some tests failed. Please check the errors above.")
        print("  The system may not work correctly.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
