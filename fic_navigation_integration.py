"""
Enhanced FICT Building Navigation Integration - CORRECTED VERSION
Fixed directional mappings and complete adjacent location details based on floor plans
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
    node_type: str  # 'intersection', 'door', 'landmark', 'exit', 'stairs', 'office'
    exits: Dict[str, str]
    accessibility_score: float
    description: str
    orientation: float = 0.0  # Wall orientation in degrees (0 = north wall)
    entrance_direction: float = 0.0  # Direction to face when entering (opposite of wall)

@dataclass
class RouteSegment:
    """Represents a segment of the navigation route with precise directional info"""
    from_node: str
    to_node: str
    distance: float
    turn_direction: str  # 'left', 'right', 'straight', 'turn_around'
    cardinal_direction: str  # 'north', 'south', 'east', 'west', etc.
    instructions: str
    waypoint_description: str
    estimated_time: float

@dataclass
class NavigationRoute:
    """Complete navigation route with enhanced instructions"""
    start_location: Dict[str, Any]
    destination: str
    total_distance: float
    estimated_time: float
    segments: List[RouteSegment]
    checkpoints: List[str]
    floor_changes: List[Dict[str, Any]]
    user_orientation: float  # User's current facing direction

@dataclass
class UserState:
    """Tracks user's current state and orientation"""
    location_id: str
    coordinates: Tuple[float, float]
    facing_direction: float  # Degrees, 0 = north
    floor_level: int
    last_movement_direction: Optional[float] = None

class FICTNavigationSystem:
    """
    Enhanced navigation system with corrected directional guidance.
    """
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.qr_detector = QRCodeDetector()
        
        # Load FICT Building location data with corrected spatial information
        self.fic_locations = self._load_corrected_fic_locations()
        self.current_location = None
        self.current_floor = None
        
        # User state tracking
        self.user_state = None
        
        # Enhanced route guidance system
        self.floor_graphs = {}
        self.node_data = {}
        self.stair_connections = {}
        self.walking_speed = 1.4  # m/s
        
        # Directional system with precise mappings
        self.cardinal_directions = {
            0: 'north', 45: 'northeast', 90: 'east', 135: 'southeast',
            180: 'south', 225: 'southwest', 270: 'west', 315: 'northwest'
        }
        
        # Build enhanced navigation system
        self._build_enhanced_navigation_system()
        self.setup_logging()
    
    def _load_corrected_fic_locations(self) -> Dict[str, Dict[str, Any]]:
        """Load FICT Building locations with corrected spatial data"""
        locations = {}
        
        # Load from existing QR code directories
        ground_floor_file = "data/qr_schemas/fict_building/ground_floor"
        first_floor_file = "data/qr_schemas/fict_building/first_floor"
        
        # Process ground floor
        if os.path.exists(ground_floor_file):
            for filename in os.listdir(ground_floor_file):
                if filename.endswith('_nav_blue_qr.png'):
                    location_id = filename.replace('_nav_blue_qr.png', '')
                    locations[location_id] = {
                        'floor_level': '0',
                        'color_scheme': 'blue',
                        'qr_file': os.path.join(ground_floor_file, filename)
                    }
        
        # Process first floor
        if os.path.exists(first_floor_file):
            for filename in os.listdir(first_floor_file):
                if filename.endswith('_nav_red_qr.png'):
                    location_id = filename.replace('_nav_red_qr.png', '')
                    locations[location_id] = {
                        'floor_level': '1',
                        'color_scheme': 'red',
                        'qr_file': os.path.join(first_floor_file, filename)
                    }
        
        # Add corrected location details with precise spatial relationships
        self._add_corrected_spatial_details(locations)
        return locations

    def _add_corrected_spatial_details(self, locations: Dict[str, Dict[str, Any]]):
        """Add corrected spatial details for ALL locations with verified adjacencies"""
        
        # GROUND FLOOR - COMPLETE CORRECTED MAPPING
        ground_floor_details = {
            # Office row NG series - VERIFIED adjacencies (facing north when entering)
            "NG-001": {
                "coordinates": "45,85", 
                "description": "Office NG-001", 
                "type": "office", 
                "wall_orientation": 180,  # South-facing wall
                "entrance_direction": 0,   # User faces north when entering
                "adjacent_locations": {
                    "east": "NG-002",     # To the right when facing north
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-002": {
                "coordinates": "50,85", 
                "description": "Office NG-002", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-003",     # To the right when facing north
                    "west": "NG-001",     # To the left when facing north
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-003": {
                "coordinates": "55,85", 
                "description": "Office NG-003", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-004",
                    "west": "NG-002",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-004": {
                "coordinates": "60,85", 
                "description": "Office NG-004", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-005",
                    "west": "NG-003",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-005": {
                "coordinates": "65,85", 
                "description": "Office NG-005", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-006",
                    "west": "NG-004",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-006": {
                "coordinates": "70,85", 
                "description": "Office NG-006", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-007",
                    "west": "NG-005",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-007": {
                "coordinates": "75,85", 
                "description": "Office NG-007", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-008",
                    "west": "NG-006",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-008": {
                "coordinates": "80,85", 
                "description": "Office NG-008", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-009",
                    "west": "NG-007",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-009": {
                "coordinates": "85,85", 
                "description": "Office NG-009", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-010",
                    "west": "NG-008",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-010": {
                "coordinates": "90,85", 
                "description": "Office NG-010", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-011",
                    "west": "NG-009",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-011": {
                "coordinates": "95,85", 
                "description": "Office NG-011", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-012",
                    "west": "NG-010",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-012": {
                "coordinates": "100,85", 
                "description": "Office NG-012", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-013",
                    "west": "NG-011",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-013": {
                "coordinates": "105,85", 
                "description": "Office NG-013", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NG-014",
                    "west": "NG-012",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },
            "NG-014": {
                "coordinates": "110,85", 
                "description": "Office NG-014", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "west": "NG-013",
                    "south": "CORRIDOR_OFFICE_G"
                }
            },

            # Lecture room row - VERIFIED (facing north when entering)
            "N007": {
                "coordinates": "140,55", 
                "description": "Lecture Room 7 - Open-Office Style Classroom", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,  # User faces north when entering
                "adjacent_locations": {
                    "east": "N006",      # To the right when facing north
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N008"
                }
            },
            "N006": {
                "coordinates": "180,55", 
                "description": "Lecture Room 6", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N005",      # To the right when facing north
                    "west": "N007",      # To the left when facing north
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N009"
                }
            },
            "N005": {
                "coordinates": "220,55", 
                "description": "Lecture Room 5", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N004",
                    "west": "N006",
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N009"
                }
            },
            "N004": {
                "coordinates": "260,55", 
                "description": "Lecture Room 4", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N003",
                    "west": "N005",
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N010"
                }
            },
            "N003": {
                "coordinates": "320,55", 
                "description": "Lecture Room 3", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N002",
                    "west": "N004",
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N011"
                }
            },
            "N002": {
                "coordinates": "360,55", 
                "description": "Lecture Room 2", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N001",
                    "west": "N003",
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N012"
                }
            },
            "N001": {
                "coordinates": "400,55", 
                "description": "Lecture Room 1", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "west": "N002",
                    "north": "CORRIDOR_MAIN_G",
                    "south": "N012"
                }
            },
            
            # Laboratory row - CORRECTED (facing south when entering)
            "N008": {
                "coordinates": "140,15", 
                "description": "Microsoft Software Engineering Laboratory", 
                "type": "laboratory", 
                "wall_orientation": 0,   # North-facing wall
                "entrance_direction": 180, # User faces south when entering
                "adjacent_locations": {
                    "east": "N009",      # To the left when facing south
                    "north": "N007",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            "N009": {
                "coordinates": "200,15", 
                "description": "Silverlake Lab", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "east": "N010",      # To the left when facing south  
                    "west": "N008",      # To the right when facing south
                    "north": "N006",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            "N010": {
                "coordinates": "260,15", 
                "description": "Cisco Networking Academy Laboratory", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "east": "N011",      # To the left when facing south
                    "west": "N009",      # To the right when facing south
                    "north": "N004",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            "N011": {
                "coordinates": "320,15", 
                "description": "IPSR Lab", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "east": "N012",      # To the left when facing south
                    "west": "N010",      # To the right when facing south  
                    "north": "N003",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            "N012": {
                "coordinates": "380,15", 
                "description": "Laboratory N012", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "west": "N011",      # To the right when facing south
                    "north": "N002",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            
            # Infrastructure
            "STAIRS_G1": {
                "coordinates": "115,45", 
                "description": "Main Staircase (West)", 
                "type": "stairs", 
                "wall_orientation": 90, 
                "entrance_direction": 270,
                "connects_to": "STAIRS_F1",
                "adjacent_locations": {
                    "north": "CORRIDOR_MAIN_G",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            "STAIRS_G2": {
                "coordinates": "290,45", 
                "description": "Central Staircase", 
                "type": "stairs", 
                "wall_orientation": 270, 
                "entrance_direction": 90,
                "connects_to": "STAIRS_F2",
                "adjacent_locations": {
                    "north": "CORRIDOR_MAIN_G",
                    "south": "CORRIDOR_LAB_G"
                }
            },
            "MAIN_ENTRANCE": {
                "coordinates": "290,85", 
                "description": "Main Building Entrance", 
                "type": "entrance", 
                "wall_orientation": 180, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "north": "CORRIDOR_MAIN_G"
                }
            },
            
            # Corridors
            "CORRIDOR_MAIN_G": {
                "coordinates": "200,65", 
                "description": "Main Corridor Ground Floor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "north": "MAIN_ENTRANCE",
                    "south": "CORRIDOR_LAB_G",
                    "east": "N004",
                    "west": "CORRIDOR_OFFICE_G"
                }
            },
            "CORRIDOR_LAB_G": {
                "coordinates": "200,35", 
                "description": "Laboratory Corridor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "north": "CORRIDOR_MAIN_G",
                    "east": "N009",
                    "west": "N008"
                }
            },
            "CORRIDOR_OFFICE_G": {
                "coordinates": "75,45", 
                "description": "Office Area Corridor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "CORRIDOR_MAIN_G",
                    "north": "NG-007"
                }
            }
        }
        
        # FIRST FLOOR - COMPLETE CORRECTED MAPPING  
        first_floor_details = {
            # Faculty offices
            "NF-022": {
                "coordinates": "45,75", 
                "description": "Faculty General Office", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,  # Face north when entering
                "adjacent_locations": {
                    "east": "NF-022B",    # To the right when facing north
                    "south": "NF-023",
                    "north": "CORRIDOR_OFFICE_F1"
                }
            },
            "NF-023": {
                "coordinates": "45,55", 
                "description": "Meeting Room", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "north": "NF-022",
                    "east": "NF-022C"
                }
            },
            
            # Top row offices (all face north when entering)
            "NF-022B": {
                "coordinates": "75,85", 
                "description": "Office NF-022B", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-013",    # To the right when facing north
                    "west": "NF-022",    # To the left when facing north
                    "south": "CORRIDOR_OFFICE_F1"
                }
            },
            "NF-013": {
                "coordinates": "95,85", 
                "description": "Office NF-013", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-012",
                    "west": "NF-022B",
                    "south": "NF-021D"
                }
            },
            "NF-012": {
                "coordinates": "115,85", 
                "description": "Office NF-012", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-011",
                    "west": "NF-013",
                    "south": "NF-024"
                }
            },
            # Continue pattern for all NF offices...
            "NF-011": {
                "coordinates": "135,85", 
                "description": "Office NF-011", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-010",
                    "west": "NF-012",
                    "south": "NF-025"
                }
            },
            "NF-010": {
                "coordinates": "155,85", 
                "description": "Office NF-010", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-009",
                    "west": "NF-011",
                    "south": "NF-026"
                }
            },
            "NF-009": {
                "coordinates": "175,85", 
                "description": "Office NF-009", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-008",
                    "west": "NF-010",
                    "south": "NF-027"
                }
            },
            "NF-008": {
                "coordinates": "195,85", 
                "description": "Office NF-008", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-007",
                    "west": "NF-009",
                    "south": "NF-028"
                }
            },
            "NF-007": {
                "coordinates": "215,85", 
                "description": "Office NF-007", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-006",
                    "west": "NF-008",
                    "south": "NF-029"
                }
            },
            "NF-006": {
                "coordinates": "235,85", 
                "description": "Office NF-006", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-005",
                    "west": "NF-007",
                    "south": "NF-030"
                }
            },
            "NF-005": {
                "coordinates": "255,85", 
                "description": "Office NF-005", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-004",
                    "west": "NF-006",
                    "south": "NF-031"
                }
            },
            "NF-004": {
                "coordinates": "275,85", 
                "description": "Office NF-004", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-003",
                    "west": "NF-005",
                    "south": "NF-032"
                }
            },
            "NF-003": {
                "coordinates": "295,85", 
                "description": "Office NF-003", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "NF-002",
                    "west": "NF-004",
                    "south": "NF-033"
                }
            },
            "NF-002": {
                "coordinates": "315,85", 
                "description": "Office NF-002", 
                "type": "office", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "west": "NF-003",
                    "south": "NF-034"
                }
            },
            
            # First floor lecture rooms (face north when entering) 
            "N107": {
                "coordinates": "380,75", 
                "description": "Lecture Room 107", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,   # Face north when entering
                "adjacent_locations": {
                    "east": "N106",       # To the right when facing north
                    "south": "N108",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            "N106": {
                "coordinates": "420,75", 
                "description": "Lecture Room 106", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N105",       # To the right when facing north  
                    "west": "N107",       # To the left when facing north
                    "south": "N109",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            "N105": {
                "coordinates": "460,75", 
                "description": "Lecture Room 105", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N104",
                    "west": "N106",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            "N104": {
                "coordinates": "500,75", 
                "description": "Lecture Room 104 - IoT and Big Data Laboratory", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N103",
                    "west": "N105",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            "N103": {
                "coordinates": "580,75", 
                "description": "Lecture Room 103", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N102",
                    "west": "N104",
                    "south": "N110",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            "N102": {
                "coordinates": "620,75", 
                "description": "Lecture Room 102", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "N101",
                    "west": "N103",
                    "south": "N111",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            "N101": {
                "coordinates": "660,75", 
                "description": "Lecture Room 101", 
                "type": "lecture_room", 
                "wall_orientation": 180,
                "entrance_direction": 0,
                "adjacent_locations": {
                    "west": "N102",
                    "south": "N112",
                    "north": "CORRIDOR_LECTURE_F1"
                }
            },
            
            # First floor laboratories (face south when entering)
            "N108": {
                "coordinates": "380,25", 
                "description": "Huawei Networking Laboratory", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,  # Face south when entering
                "adjacent_locations": {
                    "east": "N109",       # To the left when facing south
                    "north": "N107",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            "N109": {
                "coordinates": "420,25", 
                "description": "Final Year Project Laboratory", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "east": "N110",       # To the left when facing south
                    "west": "N108",       # To the right when facing south  
                    "north": "N106",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            "N110": {
                "coordinates": "580,25", 
                "description": "Intel AI Lab", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "east": "N111",       # To the left when facing south
                    "west": "N109",       # To the right when facing south
                    "north": "N103",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            "N111": {
                "coordinates": "620,25", 
                "description": "IPSR Lab", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "east": "N112",       # To the left when facing south
                    "west": "N110",       # To the right when facing south
                    "north": "N102",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            "N112": {
                "coordinates": "660,25", 
                "description": "GDEX Technovate Lab", 
                "type": "laboratory", 
                "wall_orientation": 0,
                "entrance_direction": 180,
                "adjacent_locations": {
                    "west": "N111",       # To the right when facing south
                    "north": "N101",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            
            # First floor infrastructure  
            "STAIRS_F1": {
                "coordinates": "175,35", 
                "description": "Staircase to Ground Floor", 
                "type": "stairs", 
                "connects_to": "STAIRS_G1",
                "wall_orientation": 90, 
                "entrance_direction": 270,
                "adjacent_locations": {
                    "north": "CORRIDOR_OFFICE_F1",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            "STAIRS_F2": {
                "coordinates": "500,35", 
                "description": "Central Staircase to Ground Floor", 
                "type": "stairs", 
                "connects_to": "STAIRS_G2",
                "wall_orientation": 270, 
                "entrance_direction": 90,
                "adjacent_locations": {
                    "north": "CORRIDOR_LECTURE_F1",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            
            # First floor corridors
            "CORRIDOR_MAIN_F1": {
                "coordinates": "300,75", 
                "description": "Main Corridor First Floor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "west": "CORRIDOR_OFFICE_F1",
                    "east": "CORRIDOR_LECTURE_F1"
                }
            },
            "CORRIDOR_OFFICE_F1": {
                "coordinates": "175,55", 
                "description": "Office Area Corridor First Floor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "east": "CORRIDOR_MAIN_F1",
                    "south": "STAIRS_F1"
                }
            },
            "CORRIDOR_LECTURE_F1": {
                "coordinates": "520,85", 
                "description": "Lecture Room Corridor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "west": "CORRIDOR_MAIN_F1",
                    "south": "CORRIDOR_LAB_F1"
                }
            },
            "CORRIDOR_LAB_F1": {
                "coordinates": "520,15", 
                "description": "Laboratory Corridor First Floor", 
                "type": "corridor", 
                "wall_orientation": 0, 
                "entrance_direction": 0,
                "adjacent_locations": {
                    "north": "CORRIDOR_LECTURE_F1",
                    "west": "STAIRS_F2"
                }
            }
        }
        
        # Apply all details to locations
        for location_id, details in ground_floor_details.items():
            if location_id in locations:
                locations[location_id].update(details)
        
        for location_id, details in first_floor_details.items():
            if location_id in locations:
                locations[location_id].update(details)
    
    def _build_enhanced_navigation_system(self):
        """Build enhanced navigation system with corrected directions"""
        # Build stair connections
        self.stair_connections = {
            ('0', '1'): [
                ('STAIRS_G1', 'STAIRS_F1'),
                ('STAIRS_G2', 'STAIRS_F2')
            ],
            ('1', '0'): [
                ('STAIRS_F1', 'STAIRS_G1'),
                ('STAIRS_F2', 'STAIRS_G2')
            ]
        }
        
        # Build floor graphs with corrected connections
        self._build_corrected_floor_graphs()
    
    def _build_corrected_floor_graphs(self):
        """Build NetworkX graphs with corrected directional logic"""
        # Group locations by floor
        floor_locations = {}
        for location_id, location_info in self.fic_locations.items():
            floor_level = location_info.get('floor_level', '0')
            if floor_level not in floor_locations:
                floor_locations[floor_level] = {}
            floor_locations[floor_level][location_id] = location_info
        
        # Build graphs for each floor
        for floor_level, locations in floor_locations.items():
            self._build_corrected_floor_graph(floor_level, locations)
    
    def _build_corrected_floor_graph(self, floor_level: str, locations: Dict[str, Dict[str, Any]]):
        """Build NetworkX graph with corrected connections"""
        G = nx.Graph()
        
        # Add nodes with enhanced information
        for location_id, location_info in locations.items():
            coordinates = self._parse_coordinates(location_info.get('coordinates', '0,0'))
            node_type = self._determine_node_type(location_info)
            
            nav_node = NavigationNode(
                node_id=location_id,
                coordinates=coordinates,
                floor_level=int(floor_level),
                node_type=node_type,
                exits={},
                accessibility_score=self._calculate_accessibility_score(node_type),
                description=location_info.get('description', location_id),
                orientation=location_info.get('wall_orientation', 0.0),
                entrance_direction=location_info.get('entrance_direction', 0.0)
            )
            
            self.node_data[location_id] = nav_node
            G.add_node(location_id, **nav_node.__dict__)
        
        # Add edges using corrected adjacent location mappings
        self._add_corrected_edges(G, locations, floor_level)
        self.floor_graphs[floor_level] = G
    
    def _add_corrected_edges(self, G: nx.Graph, locations: Dict[str, Dict[str, Any]], floor_level: str):
        """Add edges based on corrected adjacent location mappings"""
        for loc_id, loc_info in locations.items():
            adjacent = loc_info.get('adjacent_locations', {})
            
            for direction, adjacent_id in adjacent.items():
                if adjacent_id in locations:
                    coord1 = self._parse_coordinates(loc_info.get('coordinates', '0,0'))
                    coord2 = self._parse_coordinates(locations[adjacent_id].get('coordinates', '0,0'))
                    distance = self._calculate_distance(coord1, coord2)
                    
                    # Calculate precise directional information
                    bearing = self._calculate_bearing(coord1, coord2)
                    cardinal_dir = self._bearing_to_cardinal(bearing)
                    
                    G.add_edge(loc_id, adjacent_id,
                              weight=distance,
                              distance=distance,
                              direction=direction,
                              cardinal_direction=cardinal_dir,
                              bearing=bearing,
                              travel_time=distance / self.walking_speed)
        
        # Add fallback connections for locations without explicit adjacency
        self._add_fallback_connections(G, locations)
        
        # Add corridor-based connections for complex routing (N009 -> N012 via corridor)
        self._add_corridor_based_connections(G, locations, floor_level)
    
    def _add_corridor_based_connections(self, G: nx.Graph, locations: Dict[str, Dict[str, Any]], floor_level: str):
        """Add corridor-based connections for multi-step routing within same room type"""
        
        # Ground floor: Connect labs through corridor for N009->N012 type routing
        if floor_level == '0':
            lab_rooms = ['N008', 'N009', 'N010', 'N011', 'N012']
            corridor_lab = 'CORRIDOR_LAB_G'
            
            # Connect each lab to the corridor if not already connected
            for lab in lab_rooms:
                if lab in locations and corridor_lab in locations:
                    if not G.has_edge(lab, corridor_lab):
                        lab_coords = self._parse_coordinates(locations[lab].get('coordinates', '0,0'))
                        corridor_coords = self._parse_coordinates(locations[corridor_lab].get('coordinates', '0,0'))
                        distance = self._calculate_distance(lab_coords, corridor_coords)
                        
                        # Add bidirectional connection to corridor
                        G.add_edge(lab, corridor_lab,
                                weight=distance,
                                distance=distance,
                                direction='south',  # Labs are south of corridor
                                cardinal_direction='south',
                                bearing=180,
                                travel_time=distance / self.walking_speed)
            
            # Similar for lecture rooms and offices
            lecture_rooms = ['N001', 'N002', 'N003', 'N004', 'N005', 'N006', 'N007']
            corridor_main = 'CORRIDOR_MAIN_G'
            
            for lecture in lecture_rooms:
                if lecture in locations and corridor_main in locations:
                    if not G.has_edge(lecture, corridor_main):
                        lec_coords = self._parse_coordinates(locations[lecture].get('coordinates', '0,0'))
                        corridor_coords = self._parse_coordinates(locations[corridor_main].get('coordinates', '0,0'))
                        distance = self._calculate_distance(lec_coords, corridor_coords)
                        
                        G.add_edge(lecture, corridor_main,
                                weight=distance,
                                distance=distance,
                                direction='north',  # Lectures are north of main corridor
                                cardinal_direction='north',
                                bearing=0,
                                travel_time=distance / self.walking_speed)
        
        # First floor: Connect rooms through corridors
        elif floor_level == '1':
            # Connect lecture rooms to their corridor
            f1_lecture_rooms = ['N101', 'N102', 'N103', 'N104', 'N105', 'N106', 'N107']
            corridor_lecture_f1 = 'CORRIDOR_LECTURE_F1'
            
            for lecture in f1_lecture_rooms:
                if lecture in locations and corridor_lecture_f1 in locations:
                    if not G.has_edge(lecture, corridor_lecture_f1):
                        lec_coords = self._parse_coordinates(locations[lecture].get('coordinates', '0,0'))
                        corridor_coords = self._parse_coordinates(locations[corridor_lecture_f1].get('coordinates', '0,0'))
                        distance = self._calculate_distance(lec_coords, corridor_coords)
                        
                        G.add_edge(lecture, corridor_lecture_f1,
                                weight=distance,
                                distance=distance,
                                direction='north',
                                cardinal_direction='north',
                                bearing=0,
                                travel_time=distance / self.walking_speed)
            
            # Connect labs to their corridor
            f1_lab_rooms = ['N108', 'N109', 'N110', 'N111', 'N112']
            corridor_lab_f1 = 'CORRIDOR_LAB_F1'
            
            for lab in f1_lab_rooms:
                if lab in locations and corridor_lab_f1 in locations:
                    if not G.has_edge(lab, corridor_lab_f1):
                        lab_coords = self._parse_coordinates(locations[lab].get('coordinates', '0,0'))
                        corridor_coords = self._parse_coordinates(locations[corridor_lab_f1].get('coordinates', '0,0'))
                        distance = self._calculate_distance(lab_coords, corridor_coords)
                        
                        G.add_edge(lab, corridor_lab_f1,
                                weight=distance,
                                distance=distance,
                                direction='south',
                                cardinal_direction='south', 
                                bearing=180,
                                travel_time=distance / self.walking_speed)
    
    def _add_fallback_connections(self, G: nx.Graph, locations: Dict[str, Dict[str, Any]]):
        """Add fallback connections for locations without explicit adjacency"""
        location_ids = list(locations.keys())
        
        for i, loc1_id in enumerate(location_ids):
            for j, loc2_id in enumerate(location_ids[i+1:], i+1):
                # Skip if already connected
                if G.has_edge(loc1_id, loc2_id):
                    continue
                
                loc1_info = locations[loc1_id]
                loc2_info = locations[loc2_id]
                
                coord1 = self._parse_coordinates(loc1_info.get('coordinates', '0,0'))
                coord2 = self._parse_coordinates(loc2_info.get('coordinates', '0,0'))
                distance = self._calculate_distance(coord1, coord2)
                
                # Only connect if very close and appropriate types
                if self._should_connect_fallback(loc1_info, loc2_info, distance):
                    bearing = self._calculate_bearing(coord1, coord2)
                    cardinal_dir = self._bearing_to_cardinal(bearing)
                    
                    G.add_edge(loc1_id, loc2_id,
                              weight=distance,
                              distance=distance,
                              direction='adjacent',
                              cardinal_direction=cardinal_dir,
                              bearing=bearing,
                              travel_time=distance / self.walking_speed)
    
    def _should_connect_fallback(self, loc1: Dict, loc2: Dict, distance: float) -> bool:
        """Determine if two locations should have fallback connection"""
        # Very close distances only
        if distance > 30.0:
            return False
        
        # Connect corridors to nearby locations
        if loc1.get('type') == 'corridor' or loc2.get('type') == 'corridor':
            return distance <= 25.0
        
        # Connect similar types that are very close
        if loc1.get('type') == loc2.get('type'):
            return distance <= 15.0
        
        return False
    
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
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _calculate_bearing(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate bearing from pos1 to pos2 in degrees (0° = North)"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        
        # Calculate angle in radians, then convert to degrees
        angle_rad = math.atan2(dx, dy)  # Note: dx, dy order for correct bearing
        angle_deg = math.degrees(angle_rad)
        
        # Normalize to 0-360 degrees
        return (angle_deg + 360) % 360
    
    def _bearing_to_cardinal(self, bearing: float) -> str:
        """Convert bearing to cardinal direction"""
        bearing = bearing % 360
        
        directions = [
            (0, 'north'), (45, 'northeast'), (90, 'east'), (135, 'southeast'),
            (180, 'south'), (225, 'southwest'), (270, 'west'), (315, 'northwest')
        ]
        
        # Find closest direction
        min_diff = float('inf')
        result = 'north'
        
        for deg, direction in directions:
            diff = min(abs(bearing - deg), 360 - abs(bearing - deg))
            if diff < min_diff:
                min_diff = diff
                result = direction
        
        return result
    
    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert degrees to readable direction"""
        return self._bearing_to_cardinal(degrees)
    
    def _determine_node_type(self, location_info: Dict[str, Any]) -> str:
        """Determine node type based on location information"""
        return location_info.get('type', 'landmark')
    
    def _calculate_accessibility_score(self, node_type: str) -> float:
        """Calculate accessibility score for a node"""
        scores = {
            'stairs': 0.3,  # Low accessibility due to stairs
            'entrance': 0.9,
            'corridor': 0.95,
            'office': 0.8,
            'lecture_room': 0.85,
            'laboratory': 0.8
        }
        return scores.get(node_type, 0.7)
    
    def scan_qr_and_set_location(self, max_duration: Optional[float] = 15.0) -> Optional[Dict[str, Any]]:
        """Scan QR code and set location with proper user orientation"""
        reader = QRCodeReader()
        detected_location: Optional[QRReaderLocationData] = None

        def _on_qr(loc: QRReaderLocationData):
            nonlocal detected_location
            detected_location = loc

        reader.continuous_scan(callback=_on_qr, max_duration=max_duration)
        if detected_location:
            location_info = self.set_current_location_from_locationdata(detected_location)
            if location_info:
                # Set user state with proper orientation
                self._initialize_user_state(location_info)
            return location_info
        return None
    
    def _initialize_user_state(self, location_info: Dict[str, Any]):
        """Initialize user state when scanning QR code"""
        location_id = location_info['location_id']
        coordinates = self._parse_coordinates(location_info.get('coordinates', '0,0'))
        floor_level = int(location_info.get('floor_level', '0'))
        
        # User faces away from wall when scanning QR code
        entrance_direction = location_info.get('entrance_direction', 0.0)
        
        self.user_state = UserState(
            location_id=location_id,
            coordinates=coordinates,
            facing_direction=entrance_direction,
            floor_level=floor_level
        )
        
        logging.info(f"User state initialized: {location_id}, facing {self._degrees_to_direction(entrance_direction)}")
    
    def set_current_location_from_locationdata(self, location: QRReaderLocationData) -> Optional[Dict[str, Any]]:
        """Set current location from QR reader data"""
        try:
            if not location or not getattr(location, 'location_id', None):
                return None
                
            location_id = location.location_id
            if location_id in self.fic_locations:
                location_info = self.fic_locations[location_id].copy()
                location_info['location_id'] = location_id
                
                self.current_location = location_info
                self.current_floor = location_info['floor_level']
                
                # Initialize user state
                self._initialize_user_state(location_info)
                
                logging.info(f"Current location set: {location_id} on floor {self.current_floor}")
                return location_info
                
            logging.warning(f"Location '{location_id}' not found in FICT catalog")
            return None
        except Exception as e:
            logging.error(f"Error setting current location: {e}")
            return None
    
    def detect_current_location(self, location_id: str) -> bool:
        """
        Manually set current location by location ID (fallback for CLI mode)
        
        Args:
            location_id (str): Location ID to set as current
            
        Returns:
            bool: True if location was found and set, False otherwise
        """
        if location_id not in self.fic_locations:
            logging.error(f"Location {location_id} not found in FICT catalog")
            return False
        
        try:
            # Create location info
            location_info = self.fic_locations[location_id].copy()
            location_info['location_id'] = location_id
            
            # Set as current location
            self.current_location = location_info
            self.current_floor = location_info['floor_level']
            
            # Initialize user state
            self._initialize_user_state(location_info)
            
            logging.info(f"Manually set current location: {location_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting location {location_id}: {e}")
            return False
    
    def get_navigation_route(self, destination_id: str) -> Optional[Dict[str, Any]]:
        """Get navigation route with corrected directional guidance"""
        if not self.current_location or not self.user_state:
            return None
        
        if destination_id not in self.fic_locations:
            return None
        
        destination = self.fic_locations[destination_id]
        
        # Calculate route with corrected directions
        route = self._calculate_corrected_route(destination_id)
        
        if not route:
            return None
        
        # Generate corrected turn-by-turn instructions
        instructions = self._generate_corrected_navigation_instructions(route)
        
        return {
            'current_location': self.current_location,
            'destination': destination,
            'route': route,
            'floor_change_needed': len(route) > 0 and any(
                self.fic_locations[seg.from_node].get('floor_level') != 
                self.fic_locations[seg.to_node].get('floor_level') 
                for seg in route
            ),
            'estimated_time': sum(seg.estimated_time for seg in route) / 60.0,
            'instructions': instructions,
            'total_distance': sum(seg.distance for seg in route),
            'user_orientation': self.user_state.facing_direction
        }
    
    def _calculate_corrected_route(self, destination_id: str) -> List[RouteSegment]:
        """Calculate route with corrected turn-by-turn directions including inter-floor navigation"""
        current_floor = str(self.current_location.get('floor_level', '0'))
        dest_floor = str(self.fic_locations[destination_id].get('floor_level', '0'))
        
        if current_floor == dest_floor:
            return self._calculate_same_floor_corrected_route(destination_id)
        else:
            return self._calculate_multi_floor_route(destination_id, current_floor, dest_floor)
    
    def _calculate_same_floor_corrected_route(self, destination_id: str) -> List[RouteSegment]:
        """Calculate route on the same floor with corrected directional guidance"""
        if not self.user_state or not self.current_location:
            return []
        
        current_floor = str(self.current_location.get('floor_level', '0'))
        
        # Get the graph for current floor
        if current_floor not in self.floor_graphs:
            logging.error(f"No graph available for floor {current_floor}")
            return []
        
        G = self.floor_graphs[current_floor]
        current_id = self.user_state.location_id
        
        # Check if both nodes exist in the graph
        if current_id not in G.nodes or destination_id not in G.nodes:
            logging.error(f"Nodes not found in graph: {current_id} or {destination_id}")
            # Fallback to direct route
            return self._create_direct_route_segment(current_id, destination_id)
        
        try:
            # Calculate shortest path using NetworkX
            path = nx.shortest_path(G, current_id, destination_id, weight='weight')
            
            if len(path) < 2:
                return []  # No route needed if already at destination
            
            # Convert path to route segments with corrected directions
            segments = []
            current_facing = self.user_state.facing_direction
            
            for i in range(len(path) - 1):
                from_node = path[i]
                to_node = path[i + 1]
                
                # Create route segment with corrected directional logic
                segment = self._create_corrected_route_segment(from_node, to_node, current_facing, G)
                segments.append(segment)
                
                # Update facing direction for next segment
                current_facing = self._get_movement_direction(from_node, to_node, G)
            
            return segments
            
        except nx.NetworkXNoPath:
            logging.warning(f"No path found from {current_id} to {destination_id} on floor {current_floor}")
            # Return direct route as fallback
            return self._create_direct_route_segment(current_id, destination_id)
        except Exception as e:
            logging.error(f"Error calculating same-floor route: {e}")
            return self._create_direct_route_segment(current_id, destination_id)
    
    def _calculate_multi_floor_route(self, destination_id: str, current_floor: str, dest_floor: str):
        """Calculate route between floors with correct staircase descriptions"""
        segments = []
        
        # Find nearest staircase on current floor
        stair_connections = self.stair_connections.get((current_floor, dest_floor), [])
        
        if not stair_connections:
            logging.error(f"No stair connections found between floors {current_floor} and {dest_floor}")
            return []
        
        # Use first available stair connection
        current_stair, dest_stair = stair_connections[0]
        
        # Route to staircase on current floor (if not already there)
        if current_stair != self.user_state.location_id:
            stair_route = self._calculate_same_floor_corrected_route(current_stair)
            segments.extend(stair_route)
        
        # Correct stair climbing segment descriptions
        direction = 'up' if int(dest_floor) > int(current_floor) else 'down'
        
        # Proper floor naming
        if dest_floor == '0':
            dest_floor_name = 'Ground Floor'
        elif dest_floor == '1':
            dest_floor_name = 'First Floor'
        elif dest_floor == '2':
            dest_floor_name = 'Second Floor'
        else:
            dest_floor_name = f'Floor {dest_floor}'
        
        stair_segment = RouteSegment(
            from_node=current_stair,
            to_node=dest_stair,
            distance=20.0,
            turn_direction='straight',
            cardinal_direction=direction,
            instructions=f"Take the stairs {direction} to {dest_floor_name}",
            waypoint_description=f"Staircase to {dest_floor_name}",
            estimated_time=30.0
        )
        segments.append(stair_segment)
        
        # Route from destination floor staircase to final destination
        original_user_state = self.user_state
        original_current_floor = self.current_floor
        original_current_location = self.current_location
        
        try:
            # Create temporary user state at destination stair
            dest_stair_info = self.fic_locations.get(dest_stair, {})
            dest_stair_coords = self._parse_coordinates(dest_stair_info.get('coordinates', '0,0'))
            temp_user_state = UserState(
                location_id=dest_stair,
                coordinates=dest_stair_coords,
                facing_direction=dest_stair_info.get('entrance_direction', 0),
                floor_level=int(dest_floor)
            )
            
            # Temporarily update system state for destination floor routing
            self.user_state = temp_user_state
            self.current_floor = dest_floor
            temp_location = dest_stair_info.copy()
            temp_location['location_id'] = dest_stair
            self.current_location = temp_location
            
            # Calculate route on destination floor
            dest_route = self._calculate_same_floor_corrected_route(destination_id)
            segments.extend(dest_route)
            
        finally:
            # ALWAYS restore original state
            self.user_state = original_user_state
            self.current_floor = original_current_floor
            self.current_location = original_current_location
        
        return segments
    
    def _create_corrected_route_segment(self, from_node: str, to_node: str, 
                                      current_facing: float, G: nx.Graph) -> RouteSegment:
        """Create corrected route segment with fixed directional logic"""
        from_info = self.fic_locations.get(from_node, {})
        to_info = self.fic_locations.get(to_node, {})
        
        # Get edge data
        edge_data = G.get_edge_data(from_node, to_node, {})
        
        # Calculate movement direction from coordinates
        from_coords = self._parse_coordinates(from_info.get('coordinates', '0,0'))
        to_coords = self._parse_coordinates(to_info.get('coordinates', '0,0'))
        movement_bearing = self._calculate_bearing(from_coords, to_coords)
        
        # Calculate turn direction relative to current facing
        turn_direction = self._calculate_corrected_turn_direction(current_facing, movement_bearing)
        
        # Get precise adjacency-based direction from graph
        adjacency_direction = edge_data.get('direction', 'forward')
        
        # Generate corrected instructions
        instructions = self._generate_corrected_instruction(
            from_info, to_info, turn_direction, adjacency_direction
        )
        
        return RouteSegment(
            from_node=from_node,
            to_node=to_node,
            distance=edge_data.get('distance', 10.0),
            turn_direction=turn_direction,
            cardinal_direction=self._bearing_to_cardinal(movement_bearing),
            instructions=instructions,
            waypoint_description=to_info.get('description', to_node),
            estimated_time=edge_data.get('travel_time', 7.0)
        )
    
    def _calculate_corrected_turn_direction(self, current_facing: float, target_direction: float) -> str:
        """Calculate corrected turn direction with proper logic"""
        # Normalize angles
        current_facing = current_facing % 360
        target_direction = target_direction % 360
        
        # Calculate turn angle
        turn_angle = (target_direction - current_facing) % 360
        if turn_angle > 180:
            turn_angle -= 360
        
        # Determine turn direction
        if abs(turn_angle) <= 10:
            return "straight"
        elif 10 < turn_angle <= 100:
            return "right"
        elif 100 < turn_angle <= 170:
            return "sharp_right"
        elif abs(turn_angle) > 170:
            return "turn_around"
        elif -100 <= turn_angle < -10:
            return "left"
        elif -170 <= turn_angle < -100:
            return "sharp_left"
        else:
            return "straight"
    
    def _generate_corrected_instruction(self, from_info: Dict, to_info: Dict, 
                                      turn_direction: str, adjacency_direction: str) -> str:
        """Generate corrected navigation instruction with fixed logic"""
        from_desc = from_info.get('description', from_info.get('location_id', ''))
        to_desc = to_info.get('description', to_info.get('location_id', ''))
        
        # Direction mapping
        direction_map = {
            'straight': 'continue straight',
            'left': 'turn left',
            'right': 'turn right',
            'sharp_left': 'turn sharply left',
            'sharp_right': 'turn sharply right',
            'turn_around': 'turn around'
        }
        
        # For room-to-room navigation, use corrected adjacency mapping
        if to_info.get('type') in ['office', 'laboratory', 'lecture_room']:
            if adjacency_direction in ['east', 'west', 'north', 'south']:
                # Based on user's entrance direction after scanning QR
                from_entrance_dir = from_info.get('entrance_direction', 0)
                
                if from_entrance_dir == 0:  # Facing north after entering
                    adjacency_map = {
                        'east': 'turn right',     # Room to the right
                        'west': 'turn left',      # Room to the left  
                        'north': 'continue straight',  # Room ahead
                        'south': 'turn around'    # Room behind
                    }
                elif from_entrance_dir == 180:  # Facing south after entering
                    adjacency_map = {
                        'east': 'turn left',      # Room to the left when facing south
                        'west': 'turn right',     # Room to the right when facing south
                        'south': 'continue straight',  # Room ahead
                        'north': 'turn around'    # Room behind
                    }
                else:
                    # Default mapping for other orientations
                    adjacency_map = {
                        'east': 'turn right',
                        'west': 'turn left',
                        'north': 'continue straight',
                        'south': 'turn around'
                    }
                
                action = adjacency_map.get(adjacency_direction, direction_map.get(turn_direction, 'continue'))
            else:
                action = direction_map.get(turn_direction, 'continue')
        else:
            action = direction_map.get(turn_direction, 'continue')
        
        return f"From {from_desc}, {action} to reach {to_desc}"
    
    def _get_movement_direction(self, from_node: str, to_node: str, G: nx.Graph) -> float:
        """Get movement direction between two nodes"""
        from_coords = self._parse_coordinates(self.fic_locations[from_node].get('coordinates', '0,0'))
        to_coords = self._parse_coordinates(self.fic_locations[to_node].get('coordinates', '0,0'))
        return self._calculate_bearing(from_coords, to_coords)
    
    def _create_direct_route_segment(self, start_node: str, destination_id: str) -> List[RouteSegment]:
        """Create direct route segment as fallback"""
        start_info = self.fic_locations.get(start_node, {})
        dest_info = self.fic_locations.get(destination_id, {})
        
        start_coords = self._parse_coordinates(start_info.get('coordinates', '0,0'))
        dest_coords = self._parse_coordinates(dest_info.get('coordinates', '0,0'))
        
        distance = self._calculate_distance(start_coords, dest_coords)
        movement_direction = self._calculate_bearing(start_coords, dest_coords)
        turn_direction = self._calculate_corrected_turn_direction(self.user_state.facing_direction, movement_direction)
        
        instruction = self._generate_corrected_instruction(start_info, dest_info, turn_direction, 'direct')
        
        return [RouteSegment(
            from_node=start_node,
            to_node=destination_id,
            distance=distance,
            turn_direction=turn_direction,
            cardinal_direction=self._bearing_to_cardinal(movement_direction),
            instructions=instruction,
            waypoint_description=dest_info.get('description', destination_id),
            estimated_time=distance / self.walking_speed
        )]
    
    def _generate_corrected_navigation_instructions(self, route: List[RouteSegment]) -> List[str]:
        """Generate corrected navigation instructions"""
        instructions = []
        
        if not route:
            return ["No route segments available"]
        
        # Add initial orientation
        current_dir = self._degrees_to_direction(self.user_state.facing_direction)
        instructions.append(f"You are currently facing {current_dir}")
        
        # Process each segment with corrected instructions
        for i, segment in enumerate(route):
            step_num = i + 1
            
            # Use corrected instruction
            instruction = segment.instructions
            
            # Add distance for longer segments
            if segment.distance > 15:
                instruction += f", walk {int(segment.distance)} meters"
            
            instructions.append(f"Step {step_num}: {instruction}")
        
        # Add arrival instruction
        final_dest = route[-1].waypoint_description
        instructions.append(f"You have arrived at {final_dest}")
        
        return instructions
    
    def get_available_destinations(self, floor: Optional[str] = None) -> List[str]:
        """Get list of available destinations"""
        destinations = []
        current_id = self.current_location.get('location_id') if self.current_location else None
        
        for location_id, location_info in self.fic_locations.items():
            # Skip current location
            if location_id == current_id:
                continue
                
            # Filter by floor if specified
            if floor and location_info.get('floor_level') != floor:
                continue
                
            # Only include actual destinations (not corridors)
            if location_info.get('type') not in ['corridor']:
                destinations.append(location_id)
        
        return sorted(destinations)
    
    def get_current_location_id(self) -> Optional[str]:
        """Get current location ID"""
        return self.current_location.get('location_id') if self.current_location else None
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def update_user_facing_direction(self, new_direction: float):
        """Update user's facing direction during navigation"""
        if self.user_state:
            self.user_state.facing_direction = new_direction % 360
            self.user_state.last_movement_direction = new_direction
            logging.info(f"User now facing: {self._degrees_to_direction(new_direction)}")
    
    def get_real_time_direction_to(self, target_location_id: str) -> Dict[str, str]:
        """Get real-time direction from current position to target"""
        if not self.user_state or target_location_id not in self.fic_locations:
            return {'direction': 'unknown', 'instruction': 'Unable to determine direction'}
        
        current_coords = self.user_state.coordinates
        target_coords = self._parse_coordinates(
            self.fic_locations[target_location_id].get('coordinates', '0,0')
        )
        
        target_bearing = self._calculate_bearing(current_coords, target_coords)
        turn_direction = self._calculate_corrected_turn_direction(self.user_state.facing_direction, target_bearing)
        
        direction_instructions = {
            'straight': f"Continue straight ahead to {target_location_id}",
            'left': f"Turn left to reach {target_location_id}",
            'right': f"Turn right to reach {target_location_id}",
            'sharp_left': f"Turn sharply to your left for {target_location_id}",
            'sharp_right': f"Turn sharply to your right for {target_location_id}",
            'turn_around': f"Turn around to face {target_location_id}"
        }
        
        return {
            'direction': turn_direction,
            'instruction': direction_instructions.get(turn_direction, f"Head towards {target_location_id}"),
            'cardinal_direction': self._bearing_to_cardinal(target_bearing)
        }
            
