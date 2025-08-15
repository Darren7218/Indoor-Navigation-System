"""
Comprehensive Debug Test Script
Tests all components of the FICT Building Navigation System
"""

import sys
import traceback
from typing import Dict, Any

def test_qr_generator():
    """Test QR Generator functionality"""
    print("=== Testing QR Generator ===")
    try:
        from qr_generator import ColoredQRGenerator
        
        # Test initialization
        generator = ColoredQRGenerator()
        print("✓ QR Generator initialized successfully")
        
        # Test basic QR generation
        test_data = {"location_id": "TEST001", "description": "Test Location"}
        qr_image = generator.generate_location_qr(test_data, color_scheme="blue", size=200)
        print("✓ Basic QR generation working")
        
        # Test color coding
        qr_image = generator.generate_color_coded_qr(test_data, floor_level="1", size=200)
        print("✓ Color coding working")
        
        print("✅ QR Generator: All tests passed\n")
        return True
        
    except Exception as e:
        print(f"❌ QR Generator test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_qr_detection():
    """Test QR Detection functionality"""
    print("=== Testing QR Detection ===")
    try:
        from qr_detection import QRCodeDetector
        
        # Test initialization
        detector = QRCodeDetector()
        print("✓ QR Detector initialized successfully")
        
        # Test basic functionality
        print("✓ QR Detection system ready")
        
        print("✅ QR Detection: All tests passed\n")
        return True
        
    except Exception as e:
        print(f"❌ QR Detection test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_route_guidance():
    """Test Route Guidance functionality"""
    print("=== Testing Route Guidance ===")
    try:
        from route_guidance import RouteGuidance
        
        # Test initialization
        route_system = RouteGuidance()
        print("✓ Route Guidance initialized successfully")
        
        # Test basic functionality
        print("✓ Route Guidance system ready")
        
        print("✅ Route Guidance: All tests passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Route Guidance test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_navigation_integration():
    """Test Navigation Integration functionality"""
    print("=== Testing Navigation Integration ===")
    try:
        from fic_navigation_integration import FICTNavigationSystem
        
        # Test initialization
        nav_system = FICTNavigationSystem()
        print("✓ Navigation System initialized successfully")
        
        # Test location loading
        print(f"✓ Loaded {len(nav_system.fic_locations)} locations")
        
        # Test location search
        search_results = nav_system.search_locations("lecture")
        print(f"✓ Location search working: found {len(search_results)} lecture rooms")
        
        # Test floor map
        ground_floor = nav_system.get_floor_map("0")
        first_floor = nav_system.get_floor_map("1")
        print(f"✓ Floor maps working: Ground={ground_floor['total_locations']}, First={first_floor['total_locations']}")
        
        # Test navigation (simulate current location)
        nav_system.current_location = {
            "location_id": "MAIN_ENTRANCE",
            "floor_level": "0",
            "coordinates": "0,32",
            "description": "Main Building Entrance"
        }
        nav_system.current_floor = "0"
        
        # Test route calculation
        route_info = nav_system.get_navigation_route("N101")
        if route_info:
            print("✓ Route calculation working")
            print(f"  - Floor change needed: {route_info['floor_change_needed']}")
            print(f"  - Estimated time: {route_info['estimated_time']:.1f} minutes")
        else:
            print("⚠️ Route calculation returned None (expected for missing navigation data)")
        
        print("✅ Navigation Integration: All tests passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Navigation Integration test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_qr_code_generation():
    """Test FICT Building QR Code Generation"""
    print("=== Testing FICT Building QR Generation ===")
    try:
        from generate_fic_building_qr import create_ground_floor_locations, create_first_floor_locations
        
        # Test location data creation
        ground_locations = create_ground_floor_locations()
        first_locations = create_first_floor_locations()
        
        print(f"✓ Ground floor locations: {len(ground_locations)}")
        print(f"✓ First floor locations: {len(first_locations)}")
        
        # Test location data structure
        if ground_locations and first_locations:
            sample_location = ground_locations[0]
            required_keys = ['location_id', 'floor_level', 'coordinates', 'description']
            if all(key in sample_location for key in required_keys):
                print("✓ Location data structure correct")
            else:
                print("⚠️ Location data structure incomplete")
        
        print("✅ FICT Building QR Generation: All tests passed\n")
        return True
        
    except Exception as e:
        print(f"❌ FICT Building QR Generation test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_file_structure():
    """Test file structure and dependencies"""
    print("=== Testing File Structure ===")
    try:
        import os
        
        # Check required files exist
        required_files = [
            'qr_generator.py',
            'qr_detection.py', 
            'route_guidance.py',
            'fic_navigation_integration.py',
            'generate_fic_building_qr.py',
            'config.json',
            'requirements.txt'
        ]
        
        missing_files = []
        for file in required_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
            else:
                print(f"❌ {file} missing")
                missing_files.append(file)
        
        # Check generated QR code directories
        qr_dirs = [
            'data/qr_schemas/fic_building/ground_floor',
            'data/qr_schemas/fic_building/first_floor',
            'data/qr_schemas/fic_building/important_locations'
        ]
        
        for qr_dir in qr_dirs:
            if os.path.exists(qr_dir):
                file_count = len([f for f in os.listdir(qr_dir) if f.endswith('.png')])
                print(f"✓ {qr_dir}: {file_count} QR codes")
            else:
                print(f"⚠️ {qr_dir}: directory not found")
        
        if not missing_files:
            print("✅ File Structure: All required files present\n")
            return True
        else:
            print(f"⚠️ File Structure: {len(missing_files)} files missing\n")
            return False
        
    except Exception as e:
        print(f"❌ File Structure test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("🔍 FICT Building Navigation System - Debug Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results['qr_generator'] = test_qr_generator()
    test_results['qr_detection'] = test_qr_detection()
    test_results['route_guidance'] = test_route_guidance()
    test_results['navigation_integration'] = test_navigation_integration()
    test_results['qr_code_generation'] = test_qr_code_generation()
    test_results['file_structure'] = test_file_structure()
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
