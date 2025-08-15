"""
Test script for QR Code Generator
Demonstrates various QR code generation features
"""

import os
import sys
from qr_generator import ColoredQRGenerator

def test_basic_generation():
    """Test basic QR code generation."""
    print("=== Testing Basic QR Code Generation ===")
    
    generator = ColoredQRGenerator()
    
    # Test data
    test_location = {
        "location_id": "TEST_ROOM_001",
        "floor_level": "1",
        "coordinates": "25,30",
        "description": "Test Room for QR Generation"
    }
    
    try:
        # Generate QR code with default settings
        qr_image = generator.generate_location_qr(test_location)
        qr_image.save("test_basic_qr.png")
        print("✓ Basic QR code generated successfully")
        
        # Test different color schemes
        for color in ['red', 'green', 'blue', 'mixed']:
            qr_image = generator.generate_location_qr(test_location, color_scheme=color)
            qr_image.save(f"test_{color}_qr.png")
            print(f"✓ {color.capitalize()} QR code generated successfully")
            
    except Exception as e:
        print(f"✗ Error in basic generation: {str(e)}")

def test_color_coding():
    """Test automatic color coding based on floor level."""
    print("\n=== Testing Color Coding by Floor Level ===")
    
    generator = ColoredQRGenerator()
    
    # Test locations with different floor levels
    test_locations = [
        {"location_id": "GROUND_LOBBY", "floor_level": "0", "coordinates": "0,0", "description": "Ground Floor Lobby"},
        {"location_id": "FIRST_OFFICE", "floor_level": "1", "coordinates": "10,10", "description": "First Floor Office"},
        {"location_id": "SECOND_MEETING", "floor_level": "2", "coordinates": "20,20", "description": "Second Floor Meeting Room"},
        {"location_id": "BASEMENT_STORAGE", "floor_level": "-1", "coordinates": "-10,-10", "description": "Basement Storage"}
    ]
    
    try:
        for location in test_locations:
            qr_image = generator.generate_color_coded_qr(location)
            filename = f"floor_{location['floor_level']}_{location['location_id']}_qr.png"
            qr_image.save(filename)
            print(f"✓ Generated color-coded QR for {location['location_id']} (Floor {location['floor_level']})")
            
    except Exception as e:
        print(f"✗ Error in color coding: {str(e)}")

def test_batch_generation():
    """Test batch QR code generation."""
    print("\n=== Testing Batch QR Code Generation ===")
    
    generator = ColoredQRGenerator()
    
    # Create test locations
    test_locations = generator.create_sample_locations()
    
    try:
        # Generate batch with blue color scheme
        generated_files = generator.generate_batch_qr_codes(
            locations=test_locations,
            output_dir="test_qr_output",
            color_scheme="blue",
            size=300
        )
        
        print(f"✓ Batch generation completed: {len(generated_files)} files created")
        for file_path in generated_files:
            print(f"  - {file_path}")
            
    except Exception as e:
        print(f"✗ Error in batch generation: {str(e)}")

def test_custom_data_formats():
    """Test QR codes with different data formats."""
    print("\n=== Testing Different Data Formats ===")
    
    generator = ColoredQRGenerator()
    
    # Test different data formats
    test_cases = [
        {
            "name": "JSON Format",
            "data": {
                "location_id": "ROOM_201",
                "floor_level": "2",
                "coordinates": "30,40",
                "description": "Conference Room A"
            }
        },
        {
            "name": "Simple Text",
            "data": "EXIT_B"
        },
        {
            "name": "Coordinates Only",
            "data": {
                "location_id": "POINT_X",
                "coordinates": "50,60"
            }
        }
    ]
    
    try:
        for i, test_case in enumerate(test_cases):
            qr_image = generator.generate_location_qr(
                location_data=test_case["data"],
                color_scheme="mixed",
                size=350
            )
            filename = f"format_test_{i+1}_{test_case['name'].replace(' ', '_')}_qr.png"
            qr_image.save(filename)
            print(f"✓ Generated QR for {test_case['name']}")
            
    except Exception as e:
        print(f"✗ Error in format testing: {str(e)}")

def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n=== Testing Error Handling ===")
    
    generator = ColoredQRGenerator()
    
    # Test invalid color scheme
    try:
        test_location = {"location_id": "ERROR_TEST", "floor_level": "1"}
        qr_image = generator.generate_location_qr(test_location, color_scheme="invalid_color")
        print("✓ Invalid color scheme handled gracefully")
    except Exception as e:
        print(f"✗ Unexpected error with invalid color: {str(e)}")
    
    # Test empty data
    try:
        qr_image = generator.generate_location_qr({})
        print("✓ Empty data handled gracefully")
    except Exception as e:
        print(f"✗ Unexpected error with empty data: {str(e)}")

def cleanup_test_files():
    """Clean up test files."""
    print("\n=== Cleaning Up Test Files ===")
    
    # Remove test QR code files
    test_files = [
        "test_basic_qr.png",
        "test_red_qr.png",
        "test_green_qr.png",
        "test_blue_qr.png",
        "test_mixed_qr.png"
    ]
    
    # Add floor-specific files
    for floor in ["0", "1", "2", "-1"]:
        test_files.extend([f for f in os.listdir('.') if f.startswith(f"floor_{floor}_")])
    
    # Add format test files
    test_files.extend([f for f in os.listdir('.') if f.startswith("format_test_")])
    
    # Add batch output directory
    if os.path.exists("test_qr_output"):
        import shutil
        shutil.rmtree("test_qr_output")
        print("✓ Removed test output directory")
    
    # Remove individual test files
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ Removed {file}")

def main():
    """Run all tests."""
    print("QR Code Generator Test Suite")
    print("=" * 40)
    
    try:
        # Run tests
        test_basic_generation()
        test_color_coding()
        test_batch_generation()
        test_custom_data_formats()
        test_error_handling()
        
        print("\n" + "=" * 40)
        print("All tests completed!")
        
        # Ask user if they want to keep test files
        response = input("\nDo you want to keep the test QR code files? (y/n): ").lower().strip()
        if response != 'y':
            cleanup_test_files()
        else:
            print("Test files kept for inspection")
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error during testing: {str(e)}")
        cleanup_test_files()

if __name__ == "__main__":
    main()
