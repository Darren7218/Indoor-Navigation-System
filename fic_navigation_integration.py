"""
FICT Building Navigation Integration
Integrated navigation system for FICT Building with route guidance
"""

import json
import os
import logging
import networkx as nx
import numpy as np
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from qr_detection import QRCodeDetector
from qr_reader import QRCodeReader, LocationData as QRReaderLocationData

@dataclass
class NavigationNode:
    """Represents a node in the navigation graph"""
    node_id: str
    coordinates: Tuple[float, float]
    floor_level: int
    node_type: str  # 'intersection', 'door', 'landmark', 'exit'
    exits: Dict[str, str]
    accessibility_score: float  # 0.0 to 1.0, higher is more accessible

@dataclass
class RouteSegment:
    """Represents a segment of the navigation route"""
    from_node: str
    to_node: str
    distance: float
    direction: str
    instructions: str
    accessibility_notes: str

@dataclass
class NavigationRoute:
    """Complete navigation route with instructions"""
    start_location: QRReaderLocationData
    destination: str
    total_distance: float
    estimated_time: float
    segments: List[RouteSegment]
    checkpoints: List[str]
    floor_changes: List[int]

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
        
        # Load FICT Building location data
        self.fic_locations = self._load_fic_locations()
        self.current_location = None
        self.current_floor = None
        
        # Route guidance system
        self.floor_graphs = {}  # floor_level -> NetworkX graph
        self.node_data = {}     # node_id -> NavigationNode
        self.walking_speed = 1.4  # m/s average walking speed
        self.turn_penalty = 2.0   # seconds penalty for turns
        self.floor_change_penalty = 30.0  # seconds penalty for floor changes
        
        # Build navigation graphs from FICT locations
        self._build_fic_navigation_graphs()
        
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
            "NG-001": {"coordinates": "14,10", "description": "Office", "type": "office"},
            "NG-002": {"coordinates": "13,10", "description": "Office", "type": "office"},
            "NG-003": {"coordinates": "12,10", "description": "Office", "type": "office"},
            "NG-004": {"coordinates": "11,10", "description": "Office", "type": "office"},
            "NG-005": {"coordinates": "10,10", "description": "Office", "type": "office"},
            "NG-006": {"coordinates": "9,10", "description": "Office", "type": "office"},
            "NG-007": {"coordinates": "8,10", "description": "Office", "type": "office"},
            "NG-008": {"coordinates": "7,10", "description": "Office", "type": "office"},
            "NG-009": {"coordinates": "6,10", "description": "Office", "type": "office"},
            "NG-010": {"coordinates": "5,10", "description": "Office", "type": "office"},
            "NG-011": {"coordinates": "4,10", "description": "Office", "type": "office"},
            "NG-012": {"coordinates": "3,10", "description": "Office", "type": "office"},
            "NG-013": {"coordinates": "2,10", "description": "Office", "type": "office"},
            "NG-014": {"coordinates": "1,10", "description": "Office", "type": "office"},
            "NG-015": {"coordinates": "12,8", "description": "Office", "type": "office"},
            "NG-016": {"coordinates": "11,8", "description": "Office", "type": "office"},
            "NG-017": {"coordinates": "10,8", "description": "Office", "type": "office"},
            "NG-018": {"coordinates": "9,8", "description": "Office", "type": "office"},
            "NG-019": {"coordinates": "8,8", "description": "Office", "type": "office"},
            "NG-020": {"coordinates": "7,8", "description": "Office", "type": "office"},
            "NG-021": {"coordinates": "6,8", "description": "Office", "type": "office"},
            "NG-022": {"coordinates": "5,8", "description": "Office", "type": "office"},
            "NG-023": {"coordinates": "2,7", "description": "Office", "type": "office"},
            "NG-024": {"coordinates": "0,7", "description": "Office", "type": "office"},
            "NG-025": {"coordinates": "0,6", "description": "Office", "type": "office"},
            "NG-026": {"coordinates": "0,5", "description": "Office", "type": "office"},
            "NG-027": {"coordinates": "0,4", "description": "Office", "type": "office"},
            "NG-028": {"coordinates": "0,3", "description": "Office", "type": "office"},
            "NG-029": {"coordinates": "2,4", "description": "Office", "type": "office"},
            "NG-030": {"coordinates": "2,3", "description": "Office", "type": "office"},
            "NG-031": {"coordinates": "0,0", "description": "Office", "type": "office"},
            "NG-032": {"coordinates": "1,0", "description": "Office", "type": "office"},
            "NG-033": {"coordinates": "2,0", "description": "Office", "type": "office"},
            "NG-034": {"coordinates": "3,0", "description": "Office", "type": "office"},
            "NG-035": {"coordinates": "4,0", "description": "Office", "type": "office"},
            "NG-036": {"coordinates": "5,1", "description": "Office", "type": "office"},
            "NG-037": {"coordinates": "6,1", "description": "Office", "type": "office"},
            "NG-038": {"coordinates": "7,1", "description": "Office", "type": "office"},
            "NG-039": {"coordinates": "8,1", "description": "Office", "type": "office"},
            "NG-040": {"coordinates": "9,1", "description": "Office", "type": "office"},
            "NG-041": {"coordinates": "10,1", "description": "Office", "type": "office"},
            "NG-042": {"coordinates": "11,1", "description": "Office", "type": "office"},
            "NG-043": {"coordinates": "13,1", "description": "Office", "type": "office"},
            "NG-044": {"coordinates": "12,3", "description": "Office", "type": "office"},
            "NG-045": {"coordinates": "11,3", "description": "Office", "type": "office"},
            "NG-046": {"coordinates": "10,3", "description": "Office", "type": "office"},
            "NG-047": {"coordinates": "9,3", "description": "Office", "type": "office"},
            "NG-048": {"coordinates": "8,3", "description": "Office", "type": "office"},
            "NG-049": {"coordinates": "7,3", "description": "Office", "type": "office"},
            "NG-050": {"coordinates": "6,3", "description": "Office", "type": "office"},
            "NG-051": {"coordinates": "5,3", "description": "Office", "type": "office"},
            "NG-052": {"coordinates": "4,3", "description": "Office", "type": "office"},
            "N007": {"coordinates": "18,5", "description": "Lecture Room 7 - Open-Office Style Classroom", "type": "lecture_room"},
            "N006": {"coordinates": "23,5", "description": "Lecture Room 6", "type": "lecture_room"},
            "N005": {"coordinates": "28,5", "description": "Lecture Room 5", "type": "lecture_room"},
            "N004": {"coordinates": "33,5", "description": "Lecture Room 4", "type": "lecture_room"},
            "N003": {"coordinates": "43,5", "description": "Lecture Room 3", "type": "lecture_room"},
            "N002": {"coordinates": "48,5", "description": "Lecture Room 2", "type": "lecture_room"},
            "N001": {"coordinates": "53,5", "description": "Lecture Room 1", "type": "lecture_room"},
            "N008": {"coordinates": "17,2", "description": "Microsoft Software Engineering Laboratory", "type": "laboratory"},
            "N009": {"coordinates": "27,2", "description": "Silverlake Lab", "type": "laboratory"},
            "N010": {"coordinates": "32,2", "description": "Cisco Networking Academy Laboratory", "type": "laboratory"},
            "N011": {"coordinates": "42,2", "description": "IPSR Lab", "type": "laboratory"},
            "N012": {"coordinates": "47,2", "description": "Laboratory", "type": "laboratory"},
            "NGT6": {"coordinates": "5,8", "description": "Female Toilet", "type": "facility"},
            "NGT7": {"coordinates": "5,6", "description": "Male Toilet", "type": "facility"},
            "NGT3": {"coordinates": "22,2", "description": "Disable Toilet", "type": "facility"},
            "NGT5": {"coordinates": "22,2", "description": "Female Toilet", "type": "facility"},
            "NGT4": {"coordinates": "22,2", "description": "Male Toilet", "type": "facility"},
            "NGT1": {"coordinates": "53,2", "description": "Female Toilet", "type": "facility"},
            "NGT2": {"coordinates": "50,2", "description": "Male Toilet", "type": "facility"},
            "STAIRS_G1": {"coordinates": "13,5", "description": "Staircase to First Floor", "type": "stairs"},
            "STAIRS_G2": {"coordinates": "38,5", "description": "Staircase to First Floor", "type": "stairs"},
            "STAIRS_G3": {"coordinates": "156,2", "description": "Staircase to First Floor", "type": "stairs"},
            "MAIN_ENTRANCE": {"coordinates": "39,10", "description": "Main Building Entrance (between N004,N003)", "type": "entrance"},
            "SECOND_ENTRANCE": {"coordinates": "15,9", "description": "Entrance beside of NG-001", "type": "entrance"},
            "THIRD_ENTRANCE": {"coordinates": "15, 2", "description": "Entrance beside NG-043", "type": "entrance"},
            "FOURTH_ENTRANCE": {"coordinates": "37,2", "description": "Entrance between N010 and N011", "type": "entrance"},
            "CORRIDOR_1": {"coordinates": "15,4", "description": "Corridor in front of STAIRS_G1", "type": "corridor"},
            "CORRIDOR_2": {"coordinates": "22,3", "description": "Corridor in front of NGT3 disable toilet", "type": "corridor"},
            "CORRIDOR_3": {"coordinates": "39,4", "description": "Corridor in front of MAIN_ENTRANCE", "type": "corridor"}
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
        
        # Calculate route using integrated route guidance system
        # Convert current location to LocationData format
        start_location_data = QRReaderLocationData(
            qr_data=json.dumps(self.current_location),
            confidence=1.0
        )
        
        route = self.calculate_route(
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
            'estimated_time': route.estimated_time if route else 0.0,
            'instructions': self._generate_navigation_instructions(route, floor_change_needed)
        }
    
    def _generate_navigation_instructions(self, route, floor_change: bool) -> List[str]:   
        """Generate enhanced human-readable navigation instructions with specific locations"""
        instructions = []
        
        if floor_change:
            instructions.append("This route requires changing floors - look for staircases or elevators")
        
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
                # Use the enhanced instructions from RouteSegment objects (no duplicate step numbering)
                instructions.append(f"Step {i+1}: {segment.instructions}")
                
                # Add accessibility notes inline if important (not as separate step)
                if hasattr(segment, 'accessibility_notes') and segment.accessibility_notes != "Route is fully accessible":
                    instructions[-1] += f" - {segment.accessibility_notes}"
                    
            elif isinstance(segment, dict):
                # Handle dictionary segments with enhanced descriptions
                step_instruction = f"Step {i+1}: "
                
                if segment.get('type') == 'move':
                    from_loc = segment.get('from_location', 'current position')
                    to_loc = segment.get('to_location', 'next waypoint')
                    direction = segment.get('direction', 'forward')
                    distance = segment.get('distance', 0)
                    
                    step_instruction += f"From {from_loc}, walk {self._get_direction_text(direction)} for {distance}m to {to_loc}"
                    
                elif segment.get('type') == 'turn':
                    direction = segment.get('direction', 'right')
                    landmark = segment.get('landmark', 'waypoint')
                    step_instruction += f"Turn {direction} at {landmark}"
                    
                elif segment.get('type') == 'floor_change':
                    target_floor = segment.get('target_floor', 'unknown')
                    stair_location = segment.get('stair_location', 'staircase')
                    step_instruction += f"Take the {stair_location} to floor {target_floor}"
                    
                elif segment.get('type') == 'arrive':
                    destination = segment.get('destination', 'your destination')
                    step_instruction += f"You have arrived at {destination}"
                    
                instructions.append(step_instruction)
            else:
                instructions.append(f"Step {i+1}: Continue to next waypoint")
        
        # Add final arrival confirmation (no duplicate step numbering)
        if segments:
            destination_info = "your destination"
            if hasattr(route, 'destination') and route.destination in self.fic_locations:
                dest_data = self.fic_locations[route.destination]
                destination_info = f"{dest_data.get('description', route.destination)} ({route.destination})"
            
            instructions.append(f"Final step: You should now be at {destination_info}")
        
        return instructions
    
    def _get_direction_text(self, direction: str) -> str:
        """Convert direction to more natural language"""
        direction_map = {
            'north': 'straight ahead',
            'south': 'back/reverse direction',
            'east': 'to the right',
            'west': 'to the left',
            'northeast': 'diagonally right-forward',
            'northwest': 'diagonally left-forward',
            'southeast': 'diagonally right-back',
            'southwest': 'diagonally left-back',
            'forward': 'straight ahead'
        }
        return direction_map.get(direction.lower(), direction)

    def _get_crossing_context(self, from_node: str, to_node: str, direction: str) -> str:
        """Generate context about what areas/rooms you'll be crossing"""
        from_coords = self._parse_coordinates(self.fic_locations.get(from_node, {}).get('coordinates', '0,0'))
        to_coords = self._parse_coordinates(self.fic_locations.get(to_node, {}).get('coordinates', '0,0'))
        
        # Get floor level
        from_floor = self.fic_locations.get(from_node, {}).get('floor_level', '0')
        
        # Check for notable landmarks or areas between the two points
        crossing_areas = []
        
        # Check if crossing major corridors or open spaces
        if from_floor == '0':  # Ground floor
            if self._path_crosses_area(from_coords, to_coords, [(39, 4), (39, 10)]):  # Main entrance area
                crossing_areas.append("passing by the main entrance area")
            elif self._path_crosses_area(from_coords, to_coords, [(22, 2), (22, 3)]):  # Toilet corridor
                crossing_areas.append("passing through the restroom corridor")
            elif self._path_crosses_area(from_coords, to_coords, [(25, 5), (45, 5)]):  # Lecture room corridor
                crossing_areas.append("crossing through the lecture room corridor")
            elif self._path_crosses_area(from_coords, to_coords, [(25, 2), (45, 2)]):  # Laboratory corridor
                crossing_areas.append("going through the laboratory corridor")
                
        elif from_floor == '1':  # First floor
            if self._path_crosses_area(from_coords, to_coords, [(150, 30), (170, 30)]):  # Central open space
                crossing_areas.append("crossing through the central open space")
            elif self._path_crosses_area(from_coords, to_coords, [(85, 30), (100, 30)]):  # Main corridor
                crossing_areas.append("along the main corridor")
            elif self._path_crosses_area(from_coords, to_coords, [(150, 5), (180, 5)]):  # Lecture room corridor
                crossing_areas.append("through the lecture room corridor")
            elif self._path_crosses_area(from_coords, to_coords, [(150, 55), (180, 55)]):  # Laboratory corridor
                crossing_areas.append("via the laboratory corridor")
        
        # Check if passing notable facilities
        if self._path_near_facilities(from_coords, to_coords, from_floor):
            facilities = self._get_nearby_facilities(from_coords, to_coords, from_floor)
            if facilities:
                crossing_areas.append(f"near {facilities}")
        
        if crossing_areas:
            return f"({', '.join(crossing_areas)})"
        
        return ""

    def _path_crosses_area(self, from_coords: tuple, to_coords: tuple, area_coords: list) -> bool:
        """Check if the path between two points crosses through a specific area"""
        # Simple geometric check - if the path line intersects the area
        x1, y1 = from_coords
        x2, y2 = to_coords
        
        # Check if path intersects with the area (simplified)
        for ax, ay in area_coords:
            # Check if any area point is close to the path line
            if self._point_near_line(x1, y1, x2, y2, ax, ay, threshold=5.0):
                return True
        return False

    def _point_near_line(self, x1: float, y1: float, x2: float, y2: float, 
                        px: float, py: float, threshold: float = 5.0) -> bool:
        """Check if a point is near a line segment"""
        # Calculate distance from point to line
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        if A == 0 and B == 0:
            return False
        
        distance = abs(A * px + B * py + C) / (A * A + B * B) ** 0.5
        return distance <= threshold

    def _path_near_facilities(self, from_coords: tuple, to_coords: tuple, floor: str) -> bool:
        """Check if path goes near important facilities"""
        # Get facilities on the same floor
        facilities = {k: v for k, v in self.fic_locations.items() 
                     if v.get('floor_level') == floor and v.get('type') == 'facility'}
        
        for facility_id, facility_info in facilities.items():
            facility_coords = self._parse_coordinates(facility_info.get('coordinates', '0,0'))
            if self._point_near_line(from_coords[0], from_coords[1], 
                                    to_coords[0], to_coords[1], 
                                    facility_coords[0], facility_coords[1], 
                                    threshold=8.0):
                return True
        return False

    def _get_nearby_facilities(self, from_coords: tuple, to_coords: tuple, floor: str) -> str:
        """Get names of nearby facilities along the path"""
        facilities = {k: v for k, v in self.fic_locations.items() 
                     if v.get('floor_level') == floor and v.get('type') == 'facility'}
        
        nearby = []
        for facility_id, facility_info in facilities.items():
            facility_coords = self._parse_coordinates(facility_info.get('coordinates', '0,0'))
            if self._point_near_line(from_coords[0], from_coords[1], 
                                    to_coords[0], to_coords[1], 
                                    facility_coords[0], facility_coords[1], 
                                    threshold=8.0):
                nearby.append(facility_info.get('description', facility_id))
        
        if len(nearby) == 1:
            return nearby[0]
        elif len(nearby) > 1:
            return f"{', '.join(nearby[:-1])}, and {nearby[-1]}"
        return ""
    
    def _create_fallback_route(self, destination: Dict[str, Any]):
        """Create a simple fallback route when main routing fails."""
        # Create a proper NavigationRoute object instead of MockRoute
        from qr_reader import LocationData
        
        # Create a mock start location
        start_location = LocationData(
            qr_data=json.dumps(self.current_location),
            confidence=1.0
        )
        
        # Create a simple route segment
        segment = RouteSegment(
            from_node=self.current_location.get('location_id', 'START'),
            to_node=destination.get('location_id', 'DESTINATION'),
            distance=50.0,  # Default distance
            direction='forward',
            instructions=f"Walk towards {destination.get('description', 'destination')}",
            accessibility_notes="Route is fully accessible"
        )
        
        # Create the route object
        route = NavigationRoute(
            start_location=start_location,
            destination=destination.get('location_id', 'DESTINATION'),
            total_distance=50.0,
            estimated_time=35.7,  # 50m / 1.4 m/s
            segments=[segment],
            checkpoints=[destination.get('location_id', 'DESTINATION')],
            floor_changes=[]
        )
        
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
    
    def _build_fic_navigation_graphs(self):
        """Build navigation graphs from FICT Building locations"""
        try:
            # Group locations by floor
            floor_locations = {}
            for location_id, location_info in self.fic_locations.items():
                floor_level = location_info.get('floor_level', '0')
                if floor_level not in floor_locations:
                    floor_locations[floor_level] = {}
                floor_locations[floor_level][location_id] = location_info
            
            # Build graphs for each floor
            for floor_level, locations in floor_locations.items():
                self._build_floor_graph(floor_level, locations)
            
            logging.info(f"Built navigation graphs for {len(floor_locations)} floors")
            
        except Exception as e:
            logging.error(f"Error building navigation graphs: {e}")
    
    def _build_floor_graph(self, floor_level: str, locations: Dict[str, Dict[str, Any]]):
        """Build NetworkX graph for a specific floor"""
        # Create new graph
        G = nx.Graph()
        
        # Add nodes
        for location_id, location_info in locations.items():
            # Parse coordinates
            coordinates = self._parse_coordinates(location_info.get('coordinates', '0,0'))
            
            # Determine node type
            node_type = self._determine_node_type(location_info)
            
            # Create NavigationNode
            nav_node = NavigationNode(
                node_id=location_id,
                coordinates=coordinates,
                floor_level=int(floor_level),
                node_type=node_type,
                exits={},  # Will be populated when adding edges
                accessibility_score=self._calculate_accessibility_score(node_type)
            )
            
            self.node_data[location_id] = nav_node
            G.add_node(location_id, pos=coordinates, type=node_type, accessibility=nav_node.accessibility_score)
        
        # Add edges between nearby locations (simplified connectivity)
        self._add_floor_edges(G, locations)
        
        # Store the graph
        self.floor_graphs[floor_level] = G
    
    def _parse_coordinates(self, coord_str: str) -> Tuple[float, float]:
        """Parse coordinate string to tuple"""
        try:
            if isinstance(coord_str, str):
                parts = coord_str.split(',')
                if len(parts) >= 2:
                    return (float(parts[0].strip()), float(parts[1].strip()))
            return (0.0, 0.0)
        except:
            return (0.0, 0.0)
    
    def _determine_node_type(self, location_info: Dict[str, Any]) -> str:
        """Determine node type based on location information"""
        description = location_info.get('description', '').lower()
        
        if any(word in description for word in ['entrance', 'exit', 'door']):
            return 'exit'
        elif any(word in description for word in ['lecture', 'classroom', 'lab', 'office']):
            return 'landmark'
        elif any(word in description for word in ['corridor', 'hallway', 'passage']):
            return 'intersection'
        else:
            return 'landmark'
    
    def _calculate_accessibility_score(self, node_type: str) -> float:
        """Calculate accessibility score for a node"""
        base_score = 1.0
        
        # Adjust based on node type
        if node_type == 'exit':
            base_score = 0.9
        elif node_type == 'landmark':
            base_score = 0.8
        elif node_type == 'intersection':
            base_score = 0.7
        
        return min(1.0, max(0.1, base_score))
    
    def _add_floor_edges(self, G: nx.Graph, locations: Dict[str, Dict[str, Any]]):
        """Add edges between nearby locations on the same floor"""
        location_ids = list(locations.keys())
        
        for i, loc1_id in enumerate(location_ids):
            for j, loc2_id in enumerate(location_ids[i+1:], i+1):
                loc1_info = locations[loc1_id]
                loc2_info = locations[loc2_id]
                
                # Calculate distance between locations
                coord1 = self._parse_coordinates(loc1_info.get('coordinates', '0,0'))
                coord2 = self._parse_coordinates(loc2_info.get('coordinates', '0,0'))
                distance = self._calculate_distance(coord1, coord2)
                
                # Add edge if locations are reasonably close (within 50 meters)
                if distance <= 50.0:
                    # Determine direction
                    direction = self._calculate_direction(coord1, coord2)
                    
                    # Calculate accessibility penalty
                    accessibility_penalty = self._calculate_accessibility_penalty(
                        self.node_data[loc1_id].accessibility_score,
                        self.node_data[loc2_id].accessibility_score
                    )
                    
                    total_weight = distance + accessibility_penalty
                    
                    G.add_edge(loc1_id, loc2_id, 
                              weight=total_weight,
                              distance=distance,
                              direction=direction,
                              accessibility_penalty=accessibility_penalty)
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _calculate_direction(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> str:
        """Calculate direction from pos1 to pos2"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        
        if abs(dx) > abs(dy):
            return 'east' if dx > 0 else 'west'
        else:
            return 'north' if dy > 0 else 'south'
    
    def _calculate_accessibility_penalty(self, score1: float, score2: float) -> float:
        """Calculate accessibility penalty for edge between two nodes"""
        avg_score = (score1 + score2) / 2
        return (1.0 - avg_score) * 5.0  # Penalty up to 5 meters
    
    def calculate_route(self, start_location: QRReaderLocationData, destination: str) -> Optional[NavigationRoute]:
        """
        Calculate optimal route from current location to destination
        
        Args:
            start_location: Current location from QR code
            destination: Target destination node ID
            
        Returns:
            NavigationRoute object with complete route information
        """
        try:
            # Check if destination exists
            if destination not in self.node_data:
                logging.error(f"Destination {destination} not found in navigation data")
                return None
            
            # Check if start and destination are on same floor
            start_floor = str(start_location.floor_level) if start_location.floor_level is not None else '0'
            dest_floor = str(self.node_data[destination].floor_level)
            
            if start_floor != dest_floor:
                return self._calculate_multi_floor_route(start_location, destination)
            else:
                return self._calculate_single_floor_route(start_location, destination)
                
        except Exception as e:
            logging.error(f"Error calculating route: {e}")
            return None
    
    def _calculate_single_floor_route(self, start_location: QRReaderLocationData, destination: str) -> NavigationRoute:
        """Calculate route on a single floor"""
        floor_level = str(start_location.floor_level) if start_location.floor_level is not None else '0'
        
        if floor_level not in self.floor_graphs:
            logging.error(f"Floor {floor_level} not found in navigation data")
            return None
        
        G = self.floor_graphs[floor_level]
        
        # Find nearest node to start location
        # Handle coordinates from LocationData (might be string or tuple)
        if start_location.coordinates:
            if isinstance(start_location.coordinates, str):
                start_coords = self._parse_coordinates(start_location.coordinates)
            elif isinstance(start_location.coordinates, (list, tuple)):
                start_coords = (float(start_location.coordinates[0]), float(start_location.coordinates[1]))
            else:
                start_coords = (0.0, 0.0)
        else:
            start_coords = (0.0, 0.0)
        
        start_node = self._find_nearest_node(start_coords, floor_level)
        if not start_node:
            logging.error("Could not find suitable start node")
            return None
        
        # Use A* algorithm for pathfinding
        try:
            path = nx.astar_path(G, start_node, destination, weight='weight')
            path_length = nx.astar_path_length(G, start_node, destination, weight='weight')
        except nx.NetworkXNoPath:
            logging.warning("No path found, trying Dijkstra's algorithm")
            try:
                path = nx.dijkstra_path(G, start_node, destination, weight='weight')
                path_length = nx.dijkstra_path_length(G, start_node, destination, weight='weight')
            except nx.NetworkXNoPath:
                logging.error("No path found with any algorithm")
                return None
        
        # Build route segments
        segments = self._build_route_segments(G, path)
        
        # Calculate total metrics
        total_distance = sum(seg.distance for seg in segments)
        estimated_time = self._calculate_route_time(segments)
        
        # Create checkpoints
        checkpoints = self._generate_checkpoints(path)
        
        route = NavigationRoute(
            start_location=start_location,
            destination=destination,
            total_distance=total_distance,
            estimated_time=estimated_time,
            segments=segments,
            checkpoints=checkpoints,
            floor_changes=[]
        )
        
        return route
    
    def _calculate_multi_floor_route(self, start_location: QRReaderLocationData, destination: str) -> NavigationRoute:
        """Calculate route involving floor changes"""
        # This is a simplified implementation
        # In a real system, you'd need to handle stairs, elevators, etc.
        logging.info("Multi-floor routing not fully implemented")
        return None
    
    def _find_nearest_node(self, coordinates: Tuple[float, float], floor_level: str) -> Optional[str]:
        """Find the nearest navigation node to given coordinates"""
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, node in self.node_data.items():
            if str(node.floor_level) == floor_level:
                distance = self._calculate_distance(coordinates, node.coordinates)
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node_id
        
        # If no node found on the specified floor, try to find any node
        if nearest_node is None:
            logging.warning(f"No nodes found on floor {floor_level}, searching all floors")
            for node_id, node in self.node_data.items():
                distance = self._calculate_distance(coordinates, node.coordinates)
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node_id
        
        return nearest_node
    
    def _build_route_segments(self, G: nx.Graph, path: List[str]) -> List[RouteSegment]:
        """Build route segments from path"""
        segments = []
        
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            
            # Get edge data
            edge_data = G.get_edge_data(current_node, next_node)
            
            # Use default values if edge data is missing
            if edge_data is None:
                edge_data = {
                    'distance': 10.0,  # Default distance
                    'direction': 'forward',
                    'accessibility_penalty': 0.0
                }
            
            # Create segment
            segment = RouteSegment(
                from_node=current_node,
                to_node=next_node,
                distance=edge_data.get('distance', 10.0),
                direction=edge_data.get('direction', 'forward'),
                instructions=self._generate_segment_instructions(current_node, next_node, edge_data),
                accessibility_notes=self._generate_accessibility_notes(edge_data)
            )
            
            segments.append(segment)
        
        return segments
    
    def _generate_segment_instructions(self, from_node: str, to_node: str, edge_data: Dict) -> str:
        """Generate human-readable instructions for a route segment with specific location names"""
        direction = edge_data.get('direction', 'forward')
        distance = edge_data.get('distance', 10.0)
        
        # Get location information for better context
        from_location = self.fic_locations.get(from_node, {})
        to_location = self.fic_locations.get(to_node, {})
        
        from_description = from_location.get('description', from_node)
        to_description = to_location.get('description', to_node)
        from_type = from_location.get('type', 'location')
        to_type = to_location.get('type', 'location')
        
        # Build contextual instruction
        instruction_parts = []
        
        # Starting context
        if from_type in ['office', 'lecture_room', 'laboratory']:
            instruction_parts.append(f"From {from_description} ({from_node})")
        elif from_type == 'corridor':
            instruction_parts.append(f"From the {from_description}")
        elif from_type == 'entrance':
            instruction_parts.append(f"From {from_description}")
        elif from_type == 'stairs':
            instruction_parts.append(f"From {from_description}")
        else:
            instruction_parts.append(f"From {from_node}")
        
        # Direction and distance
        direction_text = self._get_direction_text(direction)
        instruction_parts.append(f"go {direction_text} for {distance:.1f} meters")
        
        # Destination context
        if to_type in ['office', 'lecture_room', 'laboratory']:
            instruction_parts.append(f"to {to_description} ({to_node})")
        elif to_type == 'corridor':
            instruction_parts.append(f"to the {to_description}")
        elif to_type == 'entrance':
            instruction_parts.append(f"to {to_description}")
        elif to_type == 'stairs':
            instruction_parts.append(f"to {to_description}")
        elif to_type == 'facility':
            instruction_parts.append(f"towards {to_description} ({to_node})")
        else:
            instruction_parts.append(f"to {to_node}")
        
        # Add room crossing context if passing through significant areas
        crossing_context = self._get_crossing_context(from_node, to_node, direction)
        if crossing_context:
            instruction_parts.append(crossing_context)
        
        return ", ".join(instruction_parts)
    
    def _generate_accessibility_notes(self, edge_data: Dict) -> str:
        """Generate accessibility notes for a route segment"""
        penalty = edge_data.get('accessibility_penalty', 0.0)
        
        if penalty > 3.0:
            return "Note: This route may have accessibility challenges"
        elif penalty > 1.0:
            return "Note: Minor accessibility considerations"
        else:
            return "Route is fully accessible"
    
    def _calculate_route_time(self, segments: List[RouteSegment]) -> float:
        """Calculate estimated travel time for the route"""
        total_distance = sum(seg.distance for seg in segments)
        base_time = total_distance / self.walking_speed
        
        # Add penalties for turns and complexity
        turn_penalties = (len(segments) - 1) * self.turn_penalty
        
        return base_time + turn_penalties
    
    def _generate_checkpoints(self, path: List[str]) -> List[str]:
        """Generate checkpoint nodes for route verification"""
        checkpoints = []
        
        # Add checkpoints at regular intervals
        for i in range(0, len(path), max(1, len(path) // 3)):
            checkpoints.append(path[i])
        
        # Ensure destination is always a checkpoint
        if path[-1] not in checkpoints:
            checkpoints.append(path[-1])
        
        return checkpoints
    
    def get_route_summary(self, route: NavigationRoute) -> str:
        """Generate human-readable route summary"""
        if not route:
            return "No route available"
        
        summary = f"Route to {route.destination}\n"
        summary += f"Total distance: {route.total_distance:.1f} meters\n"
        summary += f"Estimated time: {route.estimated_time:.0f} seconds\n"
        summary += f"Checkpoints: {', '.join(route.checkpoints)}\n\n"
        
        summary += "Turn-by-turn instructions:\n"
        for i, segment in enumerate(route.segments, 1):
            summary += f"{i}. {segment.instructions}\n"
            if segment.accessibility_notes != "Route is fully accessible":
                summary += f"   {segment.accessibility_notes}\n"
        
        return summary