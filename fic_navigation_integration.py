"""
FICT Building Navigation Integration
Connects QR detection with route guidance for indoor navigation
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from qr_detection import QRCodeDetector
from route_guidance import RouteGuidance
from qr_generator import ColoredQRGenerator
from qr_reader import QRCodeReader, LocationData as QRReaderLocationData

class FICTNavigationSystem:
    """
    Integrated navigation system for FICT Building.
    Combines QR detection, route guidance, and location management.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the FICT navigation system.
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self.qr_detector = QRCodeDetector()
        self.route_guidance = RouteGuidance()
        self.qr_generator = ColoredQRGenerator(config_file)
        
        # Load FICT Building location data
        self.fic_locations = self._load_fic_locations()
        self.current_location = None
        self.current_floor = None
        
        self.setup_logging()
    
    def scan_qr_and_set_location(self, max_duration: Optional[float] = 15.0) -> Optional[Dict[str, Any]]:
        """Open camera, read a QR once, set current location, then close.

        Args:
            max_duration: seconds to scan before giving up

        Returns:
            Location info dict if detected and set, else None
        """
        reader = QRCodeReader()
        detected_location: Optional[QRReaderLocationData] = None

        def _on_qr(loc: QRReaderLocationData):
            nonlocal detected_location
            detected_location = loc

        reader.continuous_scan(callback=_on_qr, max_duration=max_duration)
        if detected_location:
            return self.set_current_location_from_locationdata(detected_location)
        return None

    def set_current_location_from_locationdata(self, location: QRReaderLocationData) -> Optional[Dict[str, Any]]:
        """Set current location from qr_reader.LocationData instance."""
        try:
            if not location or not getattr(location, 'location_id', None):
                return None
            location_id = location.location_id
            if location_id in self.fic_locations:
                location_info = self.fic_locations[location_id].copy()
                location_info['location_id'] = location_id
                # Prefer coordinates/floor from FICT catalog; fall back to QR payload
                if not location_info.get('coordinates') and getattr(location, 'coordinates', None):
                    location_info['coordinates'] = location.coordinates
                if not location_info.get('floor_level') and getattr(location, 'floor_level', None):
                    location_info['floor_level'] = location.floor_level
                # Update internal state
                self.current_location = location_info
                self.current_floor = location_info['floor_level']
                logging.info(f"Current location set from LocationData: {location_id} on floor {self.current_floor}")
                return location_info
            logging.warning(f"Scanned location_id '{location_id}' not in FICT catalog")
            return None
        except Exception as e:
            logging.error(f"Error setting current location from LocationData: {e}")
            return None

    def get_available_destinations(self, floor: Optional[str] = None) -> List[str]:
        """Return sorted list of available destination IDs (optionally filtered by floor)."""
        ids = []
        for loc_id, info in self.fic_locations.items():
            if floor is None or info.get('floor_level') == floor:
                ids.append(loc_id)
        return sorted(ids)

    def get_current_location_id(self) -> Optional[str]:
        """Return current location_id if set."""
        return self.current_location.get('location_id') if self.current_location else None

    def _load_fic_locations(self) -> Dict[str, Dict[str, Any]]:
        """Load FICT Building location data from generated files."""
        locations = {}
        
        # Load ground floor locations (Blue QR codes)
        ground_floor_file = "data/qr_schemas/fic_building/ground_floor"
        if os.path.exists(ground_floor_file):
            for filename in os.listdir(ground_floor_file):
                if filename.endswith('_blue_qr.png'):
                    location_id = filename.replace('_blue_qr.png', '')
                    locations[location_id] = {
                        'floor_level': '0',
                        'color_scheme': 'blue',
                        'qr_file': os.path.join(ground_floor_file, filename)
                    }
        
        # Load first floor locations (Red QR codes)
        first_floor_file = "data/qr_schemas/fic_building/first_floor"
        if os.path.exists(first_floor_file):
            for filename in os.listdir(first_floor_file):
                if filename.endswith('_red_qr.png'):
                    location_id = filename.replace('_red_qr.png', '')
                    locations[location_id] = {
                        'floor_level': '1',
                        'color_scheme': 'red',
                        'qr_file': os.path.join(first_floor_file, filename)
                    }
        
        # Add location details from the generation script
        self._add_location_details(locations)
        
        logging.info(f"Loaded {len(locations)} FICT Building locations")
        return locations
    
    def _add_location_details(self, locations: Dict[str, Dict[str, Any]]):
        """Add detailed location information to the locations dictionary."""
        # Ground Floor locations
        ground_floor_details = {
            "NG-001": {"coordinates": "10,5", "description": "Office", "type": "office"},
            "NG-002": {"coordinates": "15,5", "description": "Office", "type": "office"},
            "NG-003": {"coordinates": "20,5", "description": "Office", "type": "office"},
            "NG-004": {"coordinates": "25,5", "description": "Office", "type": "office"},
            "NG-005": {"coordinates": "30,5", "description": "Office", "type": "office"},
            "NG-006": {"coordinates": "35,5", "description": "Office", "type": "office"},
            "NG-007": {"coordinates": "40,5", "description": "Office", "type": "office"},
            "NG-008": {"coordinates": "45,5", "description": "Office", "type": "office"},
            "NG-009": {"coordinates": "50,5", "description": "Office", "type": "office"},
            "NG-010": {"coordinates": "55,5", "description": "Office", "type": "office"},
            "NG-011": {"coordinates": "60,5", "description": "Office", "type": "office"},
            "NG-012": {"coordinates": "65,5", "description": "Office", "type": "office"},
            "NG-013": {"coordinates": "70,5", "description": "Office", "type": "office"},
            "NG-014": {"coordinates": "75,5", "description": "Office", "type": "office"},
            "NG-015": {"coordinates": "10,15", "description": "Office", "type": "office"},
            "NG-016": {"coordinates": "15,15", "description": "Office", "type": "office"},
            "NG-017": {"coordinates": "20,15", "description": "Office", "type": "office"},
            "NG-018": {"coordinates": "25,15", "description": "Office", "type": "office"},
            "NG-019": {"coordinates": "30,15", "description": "Office", "type": "office"},
            "NG-020": {"coordinates": "35,15", "description": "Office", "type": "office"},
            "NG-021": {"coordinates": "40,15", "description": "Office", "type": "office"},
            "NG-022": {"coordinates": "45,15", "description": "Office", "type": "office"},
            "NG-024": {"coordinates": "5,25", "description": "Office", "type": "office"},
            "NG-025": {"coordinates": "5,30", "description": "Office", "type": "office"},
            "NG-026": {"coordinates": "5,35", "description": "Office", "type": "office"},
            "NG-027": {"coordinates": "5,40", "description": "Office", "type": "office"},
            "NG-028": {"coordinates": "5,45", "description": "Office", "type": "office"},
            "NG-029": {"coordinates": "10,50", "description": "Office", "type": "office"},
            "NG-030": {"coordinates": "15,50", "description": "Office", "type": "office"},
            "NG-031": {"coordinates": "10,60", "description": "Office", "type": "office"},
            "NG-032": {"coordinates": "15,60", "description": "Office", "type": "office"},
            "NG-033": {"coordinates": "20,60", "description": "Office", "type": "office"},
            "NG-034": {"coordinates": "25,60", "description": "Office", "type": "office"},
            "NG-035": {"coordinates": "30,60", "description": "Office", "type": "office"},
            "NG-036": {"coordinates": "35,60", "description": "Office", "type": "office"},
            "NG-037": {"coordinates": "40,60", "description": "Office", "type": "office"},
            "NG-038": {"coordinates": "45,60", "description": "Office", "type": "office"},
            "NG-039": {"coordinates": "50,60", "description": "Office", "type": "office"},
            "NG-040": {"coordinates": "55,60", "description": "Office", "type": "office"},
            "NG-041": {"coordinates": "60,60", "description": "Office", "type": "office"},
            "NG-042": {"coordinates": "65,60", "description": "Office", "type": "office"},
            "NG-043": {"coordinates": "70,60", "description": "Office", "type": "office"},
            "NG-044": {"coordinates": "75,60", "description": "Office", "type": "office"},
            "NG-045": {"coordinates": "80,60", "description": "Office", "type": "office"},
            "NG-046": {"coordinates": "85,60", "description": "Office", "type": "office"},
            "NG-047": {"coordinates": "90,60", "description": "Office", "type": "office"},
            "NG-048": {"coordinates": "95,60", "description": "Office", "type": "office"},
            "NG-049": {"coordinates": "100,60", "description": "Office", "type": "office"},
            "NG-050": {"coordinates": "105,60", "description": "Office", "type": "office"},
            "NG-051": {"coordinates": "110,60", "description": "Office", "type": "office"},
            "NG-052": {"coordinates": "115,60", "description": "Office", "type": "office"},
            "N007": {"coordinates": "120,10", "description": "Lecture Room 7 - Open-Office Style Classroom", "type": "lecture_room"},
            "N006": {"coordinates": "130,10", "description": "Lecture Room 6", "type": "lecture_room"},
            "N005": {"coordinates": "140,10", "description": "Lecture Room 5", "type": "lecture_room"},
            "N004": {"coordinates": "150,10", "description": "Lecture Room 4", "type": "lecture_room"},
            "N003": {"coordinates": "160,10", "description": "Lecture Room 3", "type": "lecture_room"},
            "N002": {"coordinates": "170,10", "description": "Lecture Room 2", "type": "lecture_room"},
            "N001": {"coordinates": "180,10", "description": "Lecture Room 1", "type": "lecture_room"},
            "N008": {"coordinates": "120,50", "description": "Microsoft Software Engineering Laboratory", "type": "laboratory"},
            "N009": {"coordinates": "130,50", "description": "Silverlake Lab", "type": "laboratory"},
            "N010": {"coordinates": "140,50", "description": "Cisco Networking Academy Laboratory", "type": "laboratory"},
            "N011": {"coordinates": "150,50", "description": "IPSR Lab", "type": "laboratory"},
            "N012": {"coordinates": "160,50", "description": "Laboratory", "type": "laboratory"},
            "NGT6": {"coordinates": "50,20", "description": "Female Toilet", "type": "facility"},
            "NGT7": {"coordinates": "55,20", "description": "Male Toilet", "type": "facility"},
            "NGT3": {"coordinates": "155,35", "description": "Disable Toilet", "type": "facility"},
            "NGT5": {"coordinates": "125,45", "description": "Female Toilet", "type": "facility"},
            "NGT4": {"coordinates": "130,45", "description": "Male Toilet", "type": "facility"},
            "NGT1": {"coordinates": "175,45", "description": "Female Toilet", "type": "facility"},
            "NGT2": {"coordinates": "180,45", "description": "Male Toilet", "type": "facility"},
            "STAIRS_G1": {"coordinates": "42,25", "description": "Staircase to First Floor", "type": "stairs"},
            "STAIRS_G2": {"coordinates": "155,25", "description": "Staircase to First Floor", "type": "stairs"},
            "STAIRS_G3": {"coordinates": "175,25", "description": "Staircase to First Floor", "type": "stairs"},
            "MAIN_ENTRANCE": {"coordinates": "0,32", "description": "Main Building Entrance", "type": "entrance"},
            "CORRIDOR_MAIN": {"coordinates": "85,32", "description": "Main Corridor", "type": "corridor"},
            "CORRIDOR_LECTURE": {"coordinates": "150,5", "description": "Lecture Room Corridor", "type": "corridor"},
            "CORRIDOR_LAB": {"coordinates": "150,55", "description": "Laboratory Corridor", "type": "corridor"}
        }
        
        # First Floor locations
        first_floor_details = {
            "NF-022": {"coordinates": "10,5", "description": "Faculty General Office", "type": "office"},
            "NF-023": {"coordinates": "10,15", "description": "Meeting Room", "type": "meeting_room"},
            "NF-022B": {"coordinates": "15,5", "description": "Office", "type": "office"},
            "NF-013": {"coordinates": "20,5", "description": "Office", "type": "office"},
            "NF-012": {"coordinates": "25,5", "description": "Office", "type": "office"},
            "NF-011": {"coordinates": "30,5", "description": "Office", "type": "office"},
            "NF-010": {"coordinates": "35,5", "description": "Office", "type": "office"},
            "NF-009": {"coordinates": "40,5", "description": "Office", "type": "office"},
            "NF-008": {"coordinates": "45,5", "description": "Office", "type": "office"},
            "NF-007": {"coordinates": "50,5", "description": "Office", "type": "office"},
            "NF-006": {"coordinates": "55,5", "description": "Office", "type": "office"},
            "NF-005": {"coordinates": "60,5", "description": "Office", "type": "office"},
            "NF-004": {"coordinates": "65,5", "description": "Office", "type": "office"},
            "NF-003": {"coordinates": "70,5", "description": "Office", "type": "office"},
            "NF-002": {"coordinates": "75,5", "description": "Office", "type": "office"},
            "NF-022C": {"coordinates": "15,15", "description": "Office", "type": "office"},
            "NF-021D": {"coordinates": "20,15", "description": "Office", "type": "office"},
            "NF-024": {"coordinates": "25,15", "description": "Office", "type": "office"},
            "NF-025": {"coordinates": "30,15", "description": "Office", "type": "office"},
            "NF-026": {"coordinates": "35,15", "description": "Office", "type": "office"},
            "NF-027": {"coordinates": "40,15", "description": "Office", "type": "office"},
            "NF-028": {"coordinates": "45,15", "description": "Office", "type": "office"},
            "NF-029": {"coordinates": "50,15", "description": "Office", "type": "office"},
            "NF-030": {"coordinates": "55,15", "description": "Office", "type": "office"},
            "NF-031": {"coordinates": "60,15", "description": "Office", "type": "office"},
            "NF-032": {"coordinates": "65,15", "description": "Office", "type": "office"},
            "NF-033": {"coordinates": "70,15", "description": "Office", "type": "office"},
            "NF-034": {"coordinates": "75,15", "description": "Office", "type": "office"},
            "NF-021": {"coordinates": "20,25", "description": "Office", "type": "office"},
            "NF-020": {"coordinates": "25,25", "description": "Office", "type": "office"},
            "NF-019": {"coordinates": "30,25", "description": "Office", "type": "office"},
            "NF-018": {"coordinates": "35,25", "description": "Office", "type": "office"},
            "NF-017": {"coordinates": "40,25", "description": "Office", "type": "office"},
            "NF-016": {"coordinates": "45,25", "description": "Office", "type": "office"},
            "NF-015": {"coordinates": "50,25", "description": "Office", "type": "office"},
            "NF-014": {"coordinates": "55,25", "description": "Office", "type": "office"},
            "NF-042": {"coordinates": "20,35", "description": "Office", "type": "office"},
            "NF-041": {"coordinates": "25,35", "description": "Office", "type": "office"},
            "NF-040": {"coordinates": "30,35", "description": "Office", "type": "office"},
            "NF-039": {"coordinates": "35,35", "description": "Office", "type": "office"},
            "NF-038": {"coordinates": "40,35", "description": "Office", "type": "office"},
            "NF-037": {"coordinates": "45,35", "description": "Office", "type": "office"},
            "NF-036": {"coordinates": "50,35", "description": "Office", "type": "office"},
            "NF-035": {"coordinates": "55,35", "description": "Office", "type": "office"},
            "N107": {"coordinates": "120,10", "description": "Lecture Room 7", "type": "lecture_room"},
            "N106": {"coordinates": "130,10", "description": "Lecture Room 6", "type": "lecture_room"},
            "N105": {"coordinates": "140,10", "description": "Lecture Room 5", "type": "lecture_room"},
            "N104": {"coordinates": "150,10", "description": "Lecture Room 4 - IoT and Big Data Laboratory", "type": "lecture_room"},
            "N108": {"coordinates": "120,50", "description": "Huawei Networking Laboratory", "type": "laboratory"},
            "N109": {"coordinates": "130,50", "description": "Final Year Project Laboratory", "type": "laboratory"},
            "N103": {"coordinates": "160,10", "description": "Lecture Room 3", "type": "lecture_room"},
            "N102": {"coordinates": "170,10", "description": "Lecture Room 2", "type": "lecture_room"},
            "N101": {"coordinates": "180,10", "description": "Lecture Room 1", "type": "lecture_room"},
            "N110": {"coordinates": "160,50", "description": "Intel AI Lab", "type": "laboratory"},
            "N111": {"coordinates": "170,50", "description": "IPSR Lab", "type": "laboratory"},
            "N112": {"coordinates": "180,50", "description": "GDEX Technovate Lab", "type": "laboratory"},
            "NFT6": {"coordinates": "50,20", "description": "Female Toilet", "type": "facility"},
            "NFT7": {"coordinates": "55,20", "description": "Male Toilet", "type": "facility"},
            "NFT3": {"coordinates": "150,35", "description": "Disable Toilet", "type": "facility"},
            "NFT5": {"coordinates": "125,45", "description": "Female Toilet", "type": "facility"},
            "NFT4": {"coordinates": "130,45", "description": "Male Toilet", "type": "facility"},
            "NFT1": {"coordinates": "175,45", "description": "Female Toilet", "type": "facility"},
            "NFT2": {"coordinates": "180,45", "description": "Male Toilet", "type": "facility"},
            "NFP2": {"coordinates": "60,20", "description": "Pantry", "type": "facility"},
            "STAIRS_F1": {"coordinates": "42,25", "description": "Staircase to Ground Floor", "type": "stairs"},
            "STAIRS_F2": {"coordinates": "150,25", "description": "Staircase to Ground Floor", "type": "stairs"},
            "STAIRS_F3": {"coordinates": "175,25", "description": "Staircase to Ground Floor", "type": "stairs"},
            "OPEN_SPACE_CENTRAL": {"coordinates": "150,30", "description": "Central Open Space", "type": "open_space"},
            "OPEN_SPACE_RIGHT": {"coordinates": "170,30", "description": "Right Section Open Space", "type": "open_space"},
            "CORRIDOR_MAIN_F1": {"coordinates": "85,30", "description": "Main Corridor", "type": "corridor"},
            "CORRIDOR_LECTURE_F1": {"coordinates": "150,5", "description": "Lecture Room Corridor", "type": "corridor"},
            "CORRIDOR_LAB_F1": {"coordinates": "150,55", "description": "Laboratory Corridor", "type": "corridor"}
        }
        
        # Update locations with details
        for location_id, details in ground_floor_details.items():
            if location_id in locations:
                locations[location_id].update(details)
        
        for location_id, details in first_floor_details.items():
            if location_id in locations:
                locations[location_id].update(details)
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def detect_current_location(self, qr_data: str) -> Optional[Dict[str, Any]]:
        """
        Detect current location from QR code data.
        
        Args:
            qr_data (str): QR code data string
            
        Returns:
            Optional[Dict[str, Any]]: Location information if found
        """
        try:
            # Try to parse as JSON first
            if qr_data.startswith('{') and qr_data.endswith('}'):
                data = json.loads(qr_data)
                location_id = data.get('location_id')
            else:
                # Try to parse as simple text
                location_id = qr_data.strip()
            
            if location_id and location_id in self.fic_locations:
                location_info = self.fic_locations[location_id].copy()
                location_info['location_id'] = location_id
                
                # Update current location
                self.current_location = location_info
                self.current_floor = location_info['floor_level']
                
                logging.info(f"Current location detected: {location_id} on floor {self.current_floor}")
                return location_info
            else:
                logging.warning(f"Unknown location ID: {location_id}")
                return None
                
        except Exception as e:
            logging.error(f"Error detecting location: {str(e)}")
            return None
    
    def get_navigation_route(self, destination_id: str) -> Optional[Dict[str, Any]]:
        """
        Get navigation route to destination.
        
        Args:
            destination_id (str): Destination location ID
            
        Returns:
            Optional[Dict[str, Any]]: Route information
        """
        if not self.current_location:
            logging.warning("No current location set. Please detect location first.")
            return None
        
        if destination_id not in self.fic_locations:
            logging.warning(f"Unknown destination: {destination_id}")
            return None
        
        destination = self.fic_locations[destination_id]
        
        # Check if floor change is needed
        floor_change_needed = self.current_floor != destination['floor_level']
        
        # Calculate route using route guidance system
        # Convert current location to LocationData format
        from qr_reader import LocationData
        start_location_data = LocationData(
            qr_data=json.dumps(self.current_location),
            confidence=1.0
        )
        
        route = self.route_guidance.calculate_route(
            start_location=start_location_data,
            destination=destination_id
        )
        
        # If route calculation failed, create a simple fallback route
        if not route:
            route = self._create_fallback_route(destination)
        
        return {
            'current_location': self.current_location,
            'destination': destination,
            'route': route,
            'floor_change_needed': floor_change_needed,
            'estimated_time': self._estimate_travel_time(route),
            'instructions': self._generate_navigation_instructions(route, floor_change_needed)
        }
    
    def _estimate_travel_time(self, route) -> float:
        """Estimate travel time based on route complexity."""
        if not route:
            return 0.0
        
        # Handle NavigationRoute object
        if hasattr(route, 'segments'):
            segments = route.segments
        elif isinstance(route, list):
            segments = route
        else:
            return 0.0
        
        # Base time per step (in minutes)
        base_time_per_step = 0.5
        
        # Additional time for floor changes
        floor_change_penalty = 2.0
        
        total_time = len(segments) * base_time_per_step
        
        # Add penalty for floor changes
        if hasattr(route, 'floor_changes') and route.floor_changes:
            total_time += floor_change_penalty
        
        return total_time
    
    def _generate_navigation_instructions(self, route, floor_change: bool) -> List[str]:
        """Generate human-readable navigation instructions."""
        instructions = []
        
        if floor_change:
            instructions.append("⚠️ Floor change required")
        
        # Handle NavigationRoute object
        if hasattr(route, 'segments'):
            segments = route.segments
        elif isinstance(route, list):
            segments = route
        else:
            instructions.append("Route information not available")
            return instructions
        
        for i, segment in enumerate(segments):
            if hasattr(segment, 'instructions'):
                # Handle RouteSegment objects
                instructions.append(f"{i+1}. {segment.instructions}")
            elif isinstance(segment, dict):
                # Handle dictionary segments
                if segment.get('type') == 'move':
                    direction = segment.get('direction', 'forward')
                    distance = segment.get('distance', 0)
                    instructions.append(f"{i+1}. Walk {direction} for {distance}m")
                elif segment.get('type') == 'turn':
                    direction = segment.get('direction', 'right')
                    instructions.append(f"{i+1}. Turn {direction}")
                elif segment.get('type') == 'floor_change':
                    target_floor = segment.get('target_floor', 'unknown')
                    instructions.append(f"{i+1}. Take stairs/elevator to floor {target_floor}")
                elif segment.get('type') == 'arrive':
                    instructions.append(f"{i+1}. You have arrived at your destination")
            else:
                instructions.append(f"{i+1}. Continue to next waypoint")
        
        return instructions
    
    def _create_fallback_route(self, destination: Dict[str, Any]):
        """Create a simple fallback route when main routing fails."""
        # Create a simple mock route object
        class MockRoute:
            def __init__(self):
                self.segments = []
                self.floor_changes = []
                self.total_distance = 0.0
                self.estimated_time = 0.0
        
        route = MockRoute()
        
        # Add basic route information
        if self.current_location and destination:
            # Calculate approximate distance
            try:
                start_coords = self.current_location.get('coordinates', '0,0')
                end_coords = destination.get('coordinates', '0,0')
                
                if isinstance(start_coords, str) and isinstance(end_coords, str):
                    start_x, start_y = map(float, start_coords.split(','))
                    end_x, end_y = map(float, end_coords.split(','))
                    
                    distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
                    route.total_distance = distance
                    route.estimated_time = distance / 1.4  # 1.4 m/s walking speed
                    
                    # Create a simple segment
                    class MockSegment:
                        def __init__(self, instructions):
                            self.instructions = instructions
                    
                    route.segments = [MockSegment(f"Walk towards {destination.get('description', 'destination')}")]
                    
            except Exception:
                # If coordinate parsing fails, use default values
                route.total_distance = 50.0
                route.estimated_time = 35.7  # 50m / 1.4 m/s
        
        return route
    
    def search_locations(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for locations by name, description, or type.
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict[str, Any]]: Matching locations
        """
        query = query.lower()
        results = []
        
        for location_id, location_info in self.fic_locations.items():
            # Search in location ID
            if query in location_id.lower():
                results.append(location_info.copy())
                results[-1]['location_id'] = location_id
                continue
            
            # Search in description
            if 'description' in location_info and query in location_info['description'].lower():
                results.append(location_info.copy())
                results[-1]['location_id'] = location_id
                continue
            
            # Search in type
            if 'type' in location_info and query in location_info['type'].lower():
                results.append(location_info.copy())
                results[-1]['location_id'] = location_id
                continue
        
        return results
    
    def get_floor_map(self, floor_level: str) -> Dict[str, Any]:
        """
        Get floor map information for specified floor.
        
        Args:
            floor_level (str): Floor level ('0' for ground, '1' for first)
            
        Returns:
            Dict[str, Any]: Floor map information
        """
        floor_locations = {}
        
        for location_id, location_info in self.fic_locations.items():
            if location_info.get('floor_level') == floor_level:
                floor_locations[location_id] = location_info
        
        return {
            'floor_level': floor_level,
            'floor_name': 'Ground Floor' if floor_level == '0' else 'First Floor',
            'color_scheme': 'blue' if floor_level == '0' else 'red',
            'locations': floor_locations,
            'total_locations': len(floor_locations)
        }
    
    def get_location_info(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific location.
        
        Args:
            location_id (str): Location ID
            
        Returns:
            Optional[Dict[str, Any]]: Location information
        """
        if location_id in self.fic_locations:
            location_info = self.fic_locations[location_id].copy()
            location_info['location_id'] = location_id
            return location_info
        return None

def main():
    """Demo the FICT navigation system."""
    print("=== FICT Building Navigation System Demo ===")
    
    # Initialize the system
    nav_system = FICTNavigationSystem()
    
    # Demo location search
    print("\n--- Location Search Demo ---")
    search_results = nav_system.search_locations("lecture")
    print(f"Found {len(search_results)} lecture rooms:")
    for location in search_results[:5]:  # Show first 5
        print(f"  - {location['location_id']}: {location['description']}")
    
    # Demo floor map
    print("\n--- Floor Map Demo ---")
    ground_floor = nav_system.get_floor_map("0")
    print(f"Ground Floor: {ground_floor['total_locations']} locations")
    
    first_floor = nav_system.get_floor_map("1")
    print(f"First Floor: {first_floor['total_locations']} locations")
    
    # Demo navigation (simulate current location)
    print("\n--- Navigation Demo ---")
    # Simulate detecting a QR code
    current_location_data = {
        "location_id": "MAIN_ENTRANCE",
        "floor_level": "0",
        "coordinates": "0,32",
        "description": "Main Building Entrance"
    }
    
    nav_system.current_location = current_location_data
    nav_system.current_floor = "0"
    
    # Get route to a destination
    route_info = nav_system.get_navigation_route("N101")
    if route_info:
        print(f"Route to {route_info['destination']['description']}:")
        print(f"  - Floor change needed: {route_info['floor_change_needed']}")
        print(f"  - Estimated time: {route_info['estimated_time']:.1f} minutes")
        print("  - Instructions:")
        for instruction in route_info['instructions']:
            print(f"    {instruction}")
    
    print("\n✅ FICT Navigation System Demo Complete!")

if __name__ == "__main__":
    main()
