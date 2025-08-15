"""
Generate QR Codes for FICT Building
Based on Ground Floor and First Floor floor plans
"""

from qr_generator import ColoredQRGenerator
import os

def create_ground_floor_locations():
    """Create location data for Ground Floor based on the floor plan."""
    return [
        # Left Section - Offices/Smaller Rooms
        {"location_id": "NG-001", "floor_level": "0", "coordinates": "10,5", "description": "Office"},
        {"location_id": "NG-002", "floor_level": "0", "coordinates": "15,5", "description": "Office"},
        {"location_id": "NG-003", "floor_level": "0", "coordinates": "20,5", "description": "Office"},
        {"location_id": "NG-004", "floor_level": "0", "coordinates": "25,5", "description": "Office"},
        {"location_id": "NG-005", "floor_level": "0", "coordinates": "30,5", "description": "Office"},
        {"location_id": "NG-006", "floor_level": "0", "coordinates": "35,5", "description": "Office"},
        {"location_id": "NG-007", "floor_level": "0", "coordinates": "40,5", "description": "Office"},
        {"location_id": "NG-008", "floor_level": "0", "coordinates": "45,5", "description": "Office"},
        {"location_id": "NG-009", "floor_level": "0", "coordinates": "50,5", "description": "Office"},
        {"location_id": "NG-010", "floor_level": "0", "coordinates": "55,5", "description": "Office"},
        {"location_id": "NG-011", "floor_level": "0", "coordinates": "60,5", "description": "Office"},
        {"location_id": "NG-012", "floor_level": "0", "coordinates": "65,5", "description": "Office"},
        {"location_id": "NG-013", "floor_level": "0", "coordinates": "70,5", "description": "Office"},
        {"location_id": "NG-014", "floor_level": "0", "coordinates": "75,5", "description": "Office"},
        
        # Middle Row of Offices
        {"location_id": "NG-015", "floor_level": "0", "coordinates": "10,15", "description": "Office"},
        {"location_id": "NG-016", "floor_level": "0", "coordinates": "15,15", "description": "Office"},
        {"location_id": "NG-017", "floor_level": "0", "coordinates": "20,15", "description": "Office"},
        {"location_id": "NG-018", "floor_level": "0", "coordinates": "25,15", "description": "Office"},
        {"location_id": "NG-019", "floor_level": "0", "coordinates": "30,15", "description": "Office"},
        {"location_id": "NG-020", "floor_level": "0", "coordinates": "35,15", "description": "Office"},
        {"location_id": "NG-021", "floor_level": "0", "coordinates": "40,15", "description": "Office"},
        {"location_id": "NG-022", "floor_level": "0", "coordinates": "45,15", "description": "Office"},
        
        # Vertical Stack of Offices
        {"location_id": "NG-024", "floor_level": "0", "coordinates": "5,25", "description": "Office"},
        {"location_id": "NG-025", "floor_level": "0", "coordinates": "5,30", "description": "Office"},
        {"location_id": "NG-026", "floor_level": "0", "coordinates": "5,35", "description": "Office"},
        {"location_id": "NG-027", "floor_level": "0", "coordinates": "5,40", "description": "Office"},
        {"location_id": "NG-028", "floor_level": "0", "coordinates": "5,45", "description": "Office"},
        
        # Isolated Offices
        {"location_id": "NG-029", "floor_level": "0", "coordinates": "10,50", "description": "Office"},
        {"location_id": "NG-030", "floor_level": "0", "coordinates": "15,50", "description": "Office"},
        
        # Bottom Row of Offices
        {"location_id": "NG-031", "floor_level": "0", "coordinates": "10,60", "description": "Office"},
        {"location_id": "NG-032", "floor_level": "0", "coordinates": "15,60", "description": "Office"},
        {"location_id": "NG-033", "floor_level": "0", "coordinates": "20,60", "description": "Office"},
        {"location_id": "NG-034", "floor_level": "0", "coordinates": "25,60", "description": "Office"},
        {"location_id": "NG-035", "floor_level": "0", "coordinates": "30,60", "description": "Office"},
        {"location_id": "NG-036", "floor_level": "0", "coordinates": "35,60", "description": "Office"},
        {"location_id": "NG-037", "floor_level": "0", "coordinates": "40,60", "description": "Office"},
        {"location_id": "NG-038", "floor_level": "0", "coordinates": "45,60", "description": "Office"},
        {"location_id": "NG-039", "floor_level": "0", "coordinates": "50,60", "description": "Office"},
        {"location_id": "NG-040", "floor_level": "0", "coordinates": "55,60", "description": "Office"},
        {"location_id": "NG-041", "floor_level": "0", "coordinates": "60,60", "description": "Office"},
        {"location_id": "NG-042", "floor_level": "0", "coordinates": "65,60", "description": "Office"},
        {"location_id": "NG-043", "floor_level": "0", "coordinates": "70,60", "description": "Office"},
        {"location_id": "NG-044", "floor_level": "0", "coordinates": "75,60", "description": "Office"},
        {"location_id": "NG-045", "floor_level": "0", "coordinates": "80,60", "description": "Office"},
        {"location_id": "NG-046", "floor_level": "0", "coordinates": "85,60", "description": "Office"},
        {"location_id": "NG-047", "floor_level": "0", "coordinates": "90,60", "description": "Office"},
        {"location_id": "NG-048", "floor_level": "0", "coordinates": "95,60", "description": "Office"},
        {"location_id": "NG-049", "floor_level": "0", "coordinates": "100,60", "description": "Office"},
        {"location_id": "NG-050", "floor_level": "0", "coordinates": "105,60", "description": "Office"},
        {"location_id": "NG-051", "floor_level": "0", "coordinates": "110,60", "description": "Office"},
        {"location_id": "NG-052", "floor_level": "0", "coordinates": "115,60", "description": "Office"},
        
        # Middle Section - Lecture Rooms
        {"location_id": "N007", "floor_level": "0", "coordinates": "120,10", "description": "Lecture Room 7 - Open-Office Style Classroom"},
        {"location_id": "N006", "floor_level": "0", "coordinates": "130,10", "description": "Lecture Room 6"},
        {"location_id": "N005", "floor_level": "0", "coordinates": "140,10", "description": "Lecture Room 5"},
        {"location_id": "N004", "floor_level": "0", "coordinates": "150,10", "description": "Lecture Room 4"},
        {"location_id": "N003", "floor_level": "0", "coordinates": "160,10", "description": "Lecture Room 3"},
        {"location_id": "N002", "floor_level": "0", "coordinates": "170,10", "description": "Lecture Room 2"},
        {"location_id": "N001", "floor_level": "0", "coordinates": "180,10", "description": "Lecture Room 1"},
        
        # Bottom Section - Laboratories
        {"location_id": "N008", "floor_level": "0", "coordinates": "120,50", "description": "Microsoft Software Engineering Laboratory"},
        {"location_id": "N009", "floor_level": "0", "coordinates": "130,50", "description": "Silverlake Lab"},
        {"location_id": "N010", "floor_level": "0", "coordinates": "140,50", "description": "Cisco Networking Academy Laboratory"},
        {"location_id": "N011", "floor_level": "0", "coordinates": "150,50", "description": "IPSR Lab"},
        {"location_id": "N012", "floor_level": "0", "coordinates": "160,50", "description": "Laboratory"},
        
        # Toilets
        {"location_id": "NGT6", "floor_level": "0", "coordinates": "50,20", "description": "Female Toilet"},
        {"location_id": "NGT7", "floor_level": "0", "coordinates": "55,20", "description": "Male Toilet"},
        {"location_id": "NGT3", "floor_level": "0", "coordinates": "155,35", "description": "Disable Toilet"},
        {"location_id": "NGT5", "floor_level": "0", "coordinates": "125,45", "description": "Female Toilet"},
        {"location_id": "NGT4", "floor_level": "0", "coordinates": "130,45", "description": "Male Toilet"},
        {"location_id": "NGT1", "floor_level": "0", "coordinates": "175,45", "description": "Female Toilet"},
        {"location_id": "NGT2", "floor_level": "0", "coordinates": "180,45", "description": "Male Toilet"},
        
        # Staircases
        {"location_id": "STAIRS_G1", "floor_level": "0", "coordinates": "42,25", "description": "Staircase to First Floor"},
        {"location_id": "STAIRS_G2", "floor_level": "0", "coordinates": "155,25", "description": "Staircase to First Floor"},
        {"location_id": "STAIRS_G3", "floor_level": "0", "coordinates": "175,25", "description": "Staircase to First Floor"},
        
        # Main Entrance
        {"location_id": "MAIN_ENTRANCE", "floor_level": "0", "coordinates": "0,32", "description": "Main Building Entrance"},
        
        # Corridors
        {"location_id": "CORRIDOR_MAIN", "floor_level": "0", "coordinates": "85,32", "description": "Main Corridor"},
        {"location_id": "CORRIDOR_LECTURE", "floor_level": "0", "coordinates": "150,5", "description": "Lecture Room Corridor"},
        {"location_id": "CORRIDOR_LAB", "floor_level": "0", "coordinates": "150,55", "description": "Laboratory Corridor"}
    ]

def create_first_floor_locations():
    """Create location data for First Floor based on the floor plan."""
    return [
        # Left Section - Offices
        {"location_id": "NF-022", "floor_level": "1", "coordinates": "10,5", "description": "Faculty General Office"},
        {"location_id": "NF-023", "floor_level": "1", "coordinates": "10,15", "description": "Meeting Room"},
        
        # Top Corridor Offices
        {"location_id": "NF-022B", "floor_level": "1", "coordinates": "15,5", "description": "Office"},
        {"location_id": "NF-013", "floor_level": "1", "coordinates": "20,5", "description": "Office"},
        {"location_id": "NF-012", "floor_level": "1", "coordinates": "25,5", "description": "Office"},
        {"location_id": "NF-011", "floor_level": "1", "coordinates": "30,5", "description": "Office"},
        {"location_id": "NF-010", "floor_level": "1", "coordinates": "35,5", "description": "Office"},
        {"location_id": "NF-009", "floor_level": "1", "coordinates": "40,5", "description": "Office"},
        {"location_id": "NF-008", "floor_level": "1", "coordinates": "45,5", "description": "Office"},
        {"location_id": "NF-007", "floor_level": "1", "coordinates": "50,5", "description": "Office"},
        {"location_id": "NF-006", "floor_level": "1", "coordinates": "55,5", "description": "Office"},
        {"location_id": "NF-005", "floor_level": "1", "coordinates": "60,5", "description": "Office"},
        {"location_id": "NF-004", "floor_level": "1", "coordinates": "65,5", "description": "Office"},
        {"location_id": "NF-003", "floor_level": "1", "coordinates": "70,5", "description": "Office"},
        {"location_id": "NF-002", "floor_level": "1", "coordinates": "75,5", "description": "Office"},
        
        # Bottom Corridor Offices
        {"location_id": "NF-022C", "floor_level": "1", "coordinates": "15,15", "description": "Office"},
        {"location_id": "NF-021D", "floor_level": "1", "coordinates": "20,15", "description": "Office"},
        {"location_id": "NF-024", "floor_level": "1", "coordinates": "25,15", "description": "Office"},
        {"location_id": "NF-025", "floor_level": "1", "coordinates": "30,15", "description": "Office"},
        {"location_id": "NF-026", "floor_level": "1", "coordinates": "35,15", "description": "Office"},
        {"location_id": "NF-027", "floor_level": "1", "coordinates": "40,15", "description": "Office"},
        {"location_id": "NF-028", "floor_level": "1", "coordinates": "45,15", "description": "Office"},
        {"location_id": "NF-029", "floor_level": "1", "coordinates": "50,15", "description": "Office"},
        {"location_id": "NF-030", "floor_level": "1", "coordinates": "55,15", "description": "Office"},
        {"location_id": "NF-031", "floor_level": "1", "coordinates": "60,15", "description": "Office"},
        {"location_id": "NF-032", "floor_level": "1", "coordinates": "65,15", "description": "Office"},
        {"location_id": "NF-033", "floor_level": "1", "coordinates": "70,15", "description": "Office"},
        {"location_id": "NF-034", "floor_level": "1", "coordinates": "75,15", "description": "Office"},
        
        # Inner Corridor Offices
        {"location_id": "NF-021", "floor_level": "1", "coordinates": "20,25", "description": "Office"},
        {"location_id": "NF-020", "floor_level": "1", "coordinates": "25,25", "description": "Office"},
        {"location_id": "NF-019", "floor_level": "1", "coordinates": "30,25", "description": "Office"},
        {"location_id": "NF-018", "floor_level": "1", "coordinates": "35,25", "description": "Office"},
        {"location_id": "NF-017", "floor_level": "1", "coordinates": "40,25", "description": "Office"},
        {"location_id": "NF-016", "floor_level": "1", "coordinates": "45,25", "description": "Office"},
        {"location_id": "NF-015", "floor_level": "1", "coordinates": "50,25", "description": "Office"},
        {"location_id": "NF-014", "floor_level": "1", "coordinates": "55,25", "description": "Office"},
        
        # Second Inner Corridor Offices
        {"location_id": "NF-042", "floor_level": "1", "coordinates": "20,35", "description": "Office"},
        {"location_id": "NF-041", "floor_level": "1", "coordinates": "25,35", "description": "Office"},
        {"location_id": "NF-040", "floor_level": "1", "coordinates": "30,35", "description": "Office"},
        {"location_id": "NF-039", "floor_level": "1", "coordinates": "35,35", "description": "Office"},
        {"location_id": "NF-038", "floor_level": "1", "coordinates": "40,35", "description": "Office"},
        {"location_id": "NF-037", "floor_level": "1", "coordinates": "45,35", "description": "Office"},
        {"location_id": "NF-036", "floor_level": "1", "coordinates": "50,35", "description": "Office"},
        {"location_id": "NF-035", "floor_level": "1", "coordinates": "55,35", "description": "Office"},
        
        # Central Section - Lecture Rooms
        {"location_id": "N107", "floor_level": "1", "coordinates": "120,10", "description": "Lecture Room 7"},
        {"location_id": "N106", "floor_level": "1", "coordinates": "130,10", "description": "Lecture Room 6"},
        {"location_id": "N105", "floor_level": "1", "coordinates": "140,10", "description": "Lecture Room 5"},
        {"location_id": "N104", "floor_level": "1", "coordinates": "150,10", "description": "Lecture Room 4 - IoT and Big Data Laboratory"},
        
        # Central Section - Laboratories
        {"location_id": "N108", "floor_level": "1", "coordinates": "120,50", "description": "Huawei Networking Laboratory"},
        {"location_id": "N109", "floor_level": "1", "coordinates": "130,50", "description": "Final Year Project Laboratory"},
        
        # Right Section - Lecture Rooms
        {"location_id": "N103", "floor_level": "1", "coordinates": "160,10", "description": "Lecture Room 3"},
        {"location_id": "N102", "floor_level": "1", "coordinates": "170,10", "description": "Lecture Room 2"},
        {"location_id": "N101", "floor_level": "1", "coordinates": "180,10", "description": "Lecture Room 1"},
        
        # Right Section - Laboratories
        {"location_id": "N110", "floor_level": "1", "coordinates": "160,50", "description": "Intel AI Lab"},
        {"location_id": "N111", "floor_level": "1", "coordinates": "170,50", "description": "IPSR Lab"},
        {"location_id": "N112", "floor_level": "1", "coordinates": "180,50", "description": "GDEX Technovate Lab"},
        
        # Toilets
        {"location_id": "NFT6", "floor_level": "1", "coordinates": "50,20", "description": "Female Toilet"},
        {"location_id": "NFT7", "floor_level": "1", "coordinates": "55,20", "description": "Male Toilet"},
        {"location_id": "NFT3", "floor_level": "1", "coordinates": "150,35", "description": "Disable Toilet"},
        {"location_id": "NFT5", "floor_level": "1", "coordinates": "125,45", "description": "Female Toilet"},
        {"location_id": "NFT4", "floor_level": "1", "coordinates": "130,45", "description": "Male Toilet"},
        {"location_id": "NFT1", "floor_level": "1", "coordinates": "175,45", "description": "Female Toilet"},
        {"location_id": "NFT2", "floor_level": "1", "coordinates": "180,45", "description": "Male Toilet"},
        
        # Pantry
        {"location_id": "NFP2", "floor_level": "1", "coordinates": "60,20", "description": "Pantry"},
        
        # Staircases
        {"location_id": "STAIRS_F1", "floor_level": "1", "coordinates": "42,25", "description": "Staircase to Ground Floor"},
        {"location_id": "STAIRS_F2", "floor_level": "1", "coordinates": "150,25", "description": "Staircase to Ground Floor"},
        {"location_id": "STAIRS_F3", "floor_level": "1", "coordinates": "175,25", "description": "Staircase to Ground Floor"},
        
        # Open Spaces
        {"location_id": "OPEN_SPACE_CENTRAL", "floor_level": "1", "coordinates": "150,30", "description": "Central Open Space"},
        {"location_id": "OPEN_SPACE_RIGHT", "floor_level": "1", "coordinates": "170,30", "description": "Right Section Open Space"},
        
        # Corridors
        {"location_id": "CORRIDOR_MAIN_F1", "floor_level": "1", "coordinates": "85,30", "description": "Main Corridor"},
        {"location_id": "CORRIDOR_LECTURE_F1", "floor_level": "1", "coordinates": "150,5", "description": "Lecture Room Corridor"},
        {"location_id": "CORRIDOR_LAB_F1", "floor_level": "1", "coordinates": "150,55", "description": "Laboratory Corridor"}
    ]

def generate_fic_building_qr_codes():
    """Generate QR codes for the entire FICT Building."""
    print("=== FICT Building QR Code Generation ===")
    
    # Initialize generator
    generator = ColoredQRGenerator()
    
    # Create output directory
    output_dir = "data/qr_schemas/fic_building"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate Ground Floor QR codes (Blue color scheme)
    print("\n--- Generating Ground Floor QR Codes (Blue) ---")
    ground_floor_locations = create_ground_floor_locations()
    
    ground_floor_files = generator.generate_batch_qr_codes(
        locations=ground_floor_locations,
        output_dir=f"{output_dir}/ground_floor",
        color_scheme="blue",
        size=350
    )
    
    print(f"✓ Generated {len(ground_floor_files)} Ground Floor QR codes")
    
    # Generate First Floor QR codes (Red color scheme)
    print("\n--- Generating First Floor QR Codes (Red) ---")
    first_floor_locations = create_first_floor_locations()
    
    first_floor_files = generator.generate_batch_qr_codes(
        locations=first_floor_locations,
        output_dir=f"{output_dir}/first_floor",
        color_scheme="red",
        size=350
    )
    
    print(f"✓ Generated {len(first_floor_files)} First Floor QR codes")
    
    # Generate summary
    total_locations = len(ground_floor_locations) + len(first_floor_locations)
    total_files = len(ground_floor_files) + len(first_floor_files)
    
    print(f"\n=== Generation Complete ===")
    print(f"Total locations: {total_locations}")
    print(f"Total QR codes generated: {total_files}")
    print(f"Output directory: {output_dir}")
    
    # Create a summary file
    summary_file = f"{output_dir}/location_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("FICT Building Location Summary\n")
        f.write("=" * 40 + "\n\n")
        
        f.write("GROUND FLOOR (Blue QR Codes):\n")
        f.write("-" * 30 + "\n")
        for location in ground_floor_locations:
            f.write(f"{location['location_id']}: {location['description']} at {location['coordinates']}\n")
        
        f.write(f"\nFIRST FLOOR (Red QR Codes):\n")
        f.write("-" * 30 + "\n")
        for location in first_floor_locations:
            f.write(f"{location['location_id']}: {location['description']} at {location['coordinates']}\n")
        
        f.write(f"\nTotal: {total_locations} locations\n")
        f.write(f"Generated: {total_files} QR codes\n")
    
    print(f"✓ Location summary saved to: {summary_file}")
    
    return {
        'ground_floor': ground_floor_files,
        'first_floor': first_floor_files,
        'total': total_files,
        'output_dir': output_dir
    }

def generate_specific_location_qr():
    """Generate QR codes for specific important locations."""
    print("\n=== Generating Specific Location QR Codes ===")
    
    generator = ColoredQRGenerator()
    
    # Important locations that might need larger QR codes
    important_locations = [
        {
            "location_id": "MAIN_ENTRANCE",
            "floor_level": "0",
            "coordinates": "0,32",
            "description": "Main Building Entrance - FICT Building"
        },
        {
            "location_id": "FACULTY_OFFICE",
            "floor_level": "1",
            "coordinates": "10,5",
            "description": "Faculty General Office - First Floor"
        },
        {
            "location_id": "LECTURE_ROOM_MAIN",
            "floor_level": "0",
            "coordinates": "150,10",
            "description": "Main Lecture Room Area - Ground Floor"
        },
        {
            "location_id": "LABORATORY_AREA",
            "floor_level": "0",
            "coordinates": "150,50",
            "description": "Main Laboratory Area - Ground Floor"
        }
    ]
    
    output_dir = "data/qr_schemas/fic_building/important_locations"
    os.makedirs(output_dir, exist_ok=True)
    
    for location in important_locations:
        # Generate with automatic color coding
        qr_image = generator.generate_color_coded_qr(location, size=500)
        
        filename = f"{location['location_id']}_IMPORTANT_QR.png"
        filepath = os.path.join(output_dir, filename)
        qr_image.save(filepath, 'PNG', optimize=True)
        
        print(f"✓ Generated important location QR: {filename}")
    
    print(f"✓ Important location QR codes saved to: {output_dir}")

def main():
    """Main function to generate all FICT Building QR codes."""
    try:
        # Generate all building QR codes
        result = generate_fic_building_qr_codes()
        
        # Generate specific important location QR codes
        generate_specific_location_qr()
        
        print(f"\n🎉 FICT Building QR Code Generation Complete!")
        print(f"📁 All files saved to: {result['output_dir']}")
        print(f"🔢 Total QR codes: {result['total']}")
        
        # List generated directories
        print(f"\n📂 Generated directories:")
        print(f"  - {result['output_dir']}/ground_floor/ (Blue QR codes)")
        print(f"  - {result['output_dir']}/first_floor/ (Red QR codes)")
        print(f"  - {result['output_dir']}/important_locations/ (Large QR codes)")
        print(f"  - {result['output_dir']}/location_summary.txt (Summary file)")
        
    except Exception as e:
        print(f"❌ Error generating FICT Building QR codes: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
