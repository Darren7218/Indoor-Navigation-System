"""
Route Guidance Module
A* pathfinding with weighted graph representation for floor maps
Calculates optimal routes with turn-by-turn instructions
"""

import networkx as nx
import numpy as np
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from qr_reader import LocationData
import math

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
    start_location: LocationData
    destination: str
    total_distance: float
    estimated_time: float
    segments: List[RouteSegment]
    checkpoints: List[str]
    floor_changes: List[int]

class RouteGuidance:
    """Route guidance system using A* pathfinding with weighted graphs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.floor_graphs = {}  # floor_level -> NetworkX graph
        self.node_data = {}     # node_id -> NavigationNode
        self.current_location = None
        
        # Navigation parameters
        self.walking_speed = 1.4  # m/s average walking speed
        self.turn_penalty = 2.0   # seconds penalty for turns
        self.floor_change_penalty = 30.0  # seconds penalty for floor changes
        
        # Load floor maps and build graphs
        self._load_floor_maps()
    
    def _load_floor_maps(self):
        """Load floor maps and build navigation graphs"""
        try:
            # Load from JSON files (create sample data if none exist)
            self._create_sample_floor_maps()
            
            # Build graphs for each floor
            for floor_level in self.floor_graphs.keys():
                self._build_floor_graph(floor_level)
                
            self.logger.info(f"Loaded {len(self.floor_graphs)} floor maps")
            
        except Exception as e:
            self.logger.error(f"Error loading floor maps: {e}")
            # Create minimal working example
            self._create_minimal_floor_map()
    
    def _create_sample_floor_maps(self):
        """Create sample floor maps for demonstration"""
        # Floor 1 - Simple office layout
        floor1_nodes = {
            'A1': {'coordinates': (0, 0), 'type': 'entrance', 'exits': {'north': 'A2', 'east': 'B1'}},
            'A2': {'coordinates': (0, 10), 'type': 'intersection', 'exits': {'north': 'A3', 'south': 'A1', 'east': 'B2'}},
            'A3': {'coordinates': (0, 20), 'type': 'landmark', 'exits': {'south': 'A2', 'east': 'B3'}},
            'B1': {'coordinates': (10, 0), 'type': 'intersection', 'exits': {'north': 'B2', 'west': 'A1', 'east': 'C1'}},
            'B2': {'coordinates': (10, 10), 'type': 'intersection', 'exits': {'north': 'B3', 'south': 'B1', 'west': 'A2', 'east': 'C2'}},
            'B3': {'coordinates': (10, 20), 'type': 'landmark', 'exits': {'south': 'B2', 'west': 'A3', 'east': 'C3'}},
            'C1': {'coordinates': (20, 0), 'type': 'intersection', 'exits': {'north': 'C2', 'west': 'B1'}},
            'C2': {'coordinates': (20, 10), 'type': 'intersection', 'exits': {'north': 'C3', 'south': 'C1', 'west': 'B2'}},
            'C3': {'coordinates': (20, 20), 'type': 'exit', 'exits': {'south': 'C2', 'west': 'B3'}}
        }
        
        # Floor 2 - Different layout
        floor2_nodes = {
            'D1': {'coordinates': (0, 0), 'type': 'entrance', 'exits': {'north': 'D2', 'east': 'E1'}},
            'D2': {'coordinates': (0, 15), 'type': 'intersection', 'exits': {'north': 'D3', 'south': 'D1', 'east': 'E2'}},
            'D3': {'coordinates': (0, 30), 'type': 'landmark', 'exits': {'south': 'D2', 'east': 'E3'}},
            'E1': {'coordinates': (15, 0), 'type': 'intersection', 'exits': {'north': 'E2', 'west': 'D1'}},
            'E2': {'coordinates': (15, 15), 'type': 'intersection', 'exits': {'north': 'E3', 'south': 'E1', 'west': 'D2'}},
            'E3': {'coordinates': (15, 30), 'type': 'exit', 'exits': {'south': 'E2', 'west': 'D3'}}
        }
        
        self.floor_graphs = {
            1: floor1_nodes,
            2: floor2_nodes
        }
    
    def _create_minimal_floor_map(self):
        """Create minimal floor map if loading fails"""
        minimal_nodes = {
            'START': {'coordinates': (0, 0), 'type': 'entrance', 'exits': {'east': 'MID'}},
            'MID': {'coordinates': (10, 0), 'type': 'intersection', 'exits': {'west': 'START', 'east': 'END'}},
            'END': {'coordinates': (20, 0), 'type': 'exit', 'exits': {'west': 'MID'}}
        }
        self.floor_graphs = {1: minimal_nodes}
    
    def _build_floor_graph(self, floor_level: int):
        """Build NetworkX graph for a specific floor"""
        if floor_level not in self.floor_graphs:
            return
        
        # Create new graph
        G = nx.Graph()
        floor_nodes = self.floor_graphs[floor_level]
        
        # Add nodes
        for node_id, node_info in floor_nodes.items():
            coordinates = node_info['coordinates']
            node_type = node_info['type']
            exits = node_info['exits']
            
            # Create NavigationNode
            nav_node = NavigationNode(
                node_id=node_id,
                coordinates=coordinates,
                floor_level=floor_level,
                node_type=node_type,
                exits=exits,
                accessibility_score=self._calculate_accessibility_score(node_type, exits)
            )
            
            self.node_data[node_id] = nav_node
            G.add_node(node_id, pos=coordinates, type=node_type, accessibility=nav_node.accessibility_score)
        
        # Add edges with weights
        for node_id, node_info in floor_nodes.items():
            for direction, target_id in node_info['exits'].items():
                if target_id in floor_nodes:
                    # Calculate distance
                    start_pos = floor_nodes[node_id]['coordinates']
                    end_pos = floor_nodes[target_id]['coordinates']
                    distance = self._calculate_distance(start_pos, end_pos)
                    
                    # Add accessibility penalty
                    accessibility_penalty = self._calculate_accessibility_penalty(
                        self.node_data[node_id].accessibility_score,
                        self.node_data[target_id].accessibility_score
                    )
                    
                    total_weight = distance + accessibility_penalty
                    
                    G.add_edge(node_id, target_id, 
                              weight=total_weight,
                              distance=distance,
                              direction=direction,
                              accessibility_penalty=accessibility_penalty)
        
        # Store the graph
        self.floor_graphs[floor_level] = G
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _calculate_accessibility_score(self, node_type: str, exits: Dict[str, str]) -> float:
        """Calculate accessibility score for a node"""
        base_score = 1.0
        
        # Adjust based on node type
        if node_type == 'entrance':
            base_score = 0.9
        elif node_type == 'exit':
            base_score = 0.8
        elif node_type == 'landmark':
            base_score = 0.7
        
        # Adjust based on number of exits (more exits = more accessible)
        exit_count = len(exits)
        if exit_count == 1:
            base_score *= 0.8
        elif exit_count >= 4:
            base_score *= 1.1
        
        return min(1.0, max(0.1, base_score))
    
    def _calculate_accessibility_penalty(self, score1: float, score2: float) -> float:
        """Calculate accessibility penalty for edge between two nodes"""
        avg_score = (score1 + score2) / 2
        return (1.0 - avg_score) * 5.0  # Penalty up to 5 meters
    
    def calculate_route(self, start_location: LocationData, destination: str) -> Optional[NavigationRoute]:
        """
        Calculate optimal route from current location to destination
        
        Args:
            start_location: Current location from QR code
            destination: Target destination node ID
            
        Returns:
            NavigationRoute object with complete route information
        """
        try:
            self.current_location = start_location
            
            # Check if destination exists
            if destination not in self.node_data:
                self.logger.error(f"Destination {destination} not found in navigation data")
                return None
            
            # Check if start and destination are on same floor
            if start_location.floor_level != self.node_data[destination].floor_level:
                return self._calculate_multi_floor_route(start_location, destination)
            else:
                return self._calculate_single_floor_route(start_location, destination)
                
        except Exception as e:
            self.logger.error(f"Error calculating route: {e}")
            return None
    
    def _calculate_single_floor_route(self, start_location: LocationData, destination: str) -> NavigationRoute:
        """Calculate route on a single floor"""
        floor_level = start_location.floor_level
        if floor_level not in self.floor_graphs:
            self.logger.error(f"Floor {floor_level} not found in navigation data")
            return None
        
        G = self.floor_graphs[floor_level]
        
        # Find nearest node to start location
        start_node = self._find_nearest_node(start_location.coordinates, floor_level)
        if not start_node:
            self.logger.error("Could not find suitable start node")
            return None
        
        # Use A* algorithm for pathfinding
        try:
            path = nx.astar_path(G, start_node, destination, weight='weight')
            path_length = nx.astar_path_length(G, start_node, destination, weight='weight')
        except nx.NetworkXNoPath:
            self.logger.warning("No path found, trying Dijkstra's algorithm")
            try:
                path = nx.dijkstra_path(G, start_node, destination, weight='weight')
                path_length = nx.dijkstra_path_length(G, start_node, destination, weight='weight')
            except nx.NetworkXNoPath:
                self.logger.error("No path found with any algorithm")
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
    
    def _calculate_multi_floor_route(self, start_location: LocationData, destination: str) -> NavigationRoute:
        """Calculate route involving floor changes"""
        # This is a simplified implementation
        # In a real system, you'd need to handle stairs, elevators, etc.
        self.logger.info("Multi-floor routing not fully implemented")
        return None
    
    def _find_nearest_node(self, coordinates: Tuple[float, float], floor_level: int) -> Optional[str]:
        """Find the nearest navigation node to given coordinates"""
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, node in self.node_data.items():
            if node.floor_level == floor_level:
                distance = self._calculate_distance(coordinates, node.coordinates)
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node_id
        
        # If no node found on the specified floor, try to find any node
        if nearest_node is None:
            self.logger.warning(f"No nodes found on floor {floor_level}, searching all floors")
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
        """Generate human-readable instructions for a route segment"""
        direction = edge_data.get('direction', 'forward')
        distance = edge_data.get('distance', 10.0)
        
        # Get node types for context (with safety checks)
        from_type = self.node_data.get(from_node, None)
        to_type = self.node_data.get(to_node, None)
        
        from_type_name = from_type.node_type if from_type else 'location'
        to_type_name = to_type.node_type if to_type else 'location'
        
        instructions = f"Go {direction} for {distance:.1f} meters"
        
        # Add context-specific instructions
        if from_type_name == 'intersection':
            instructions += f" from the {from_type_name}"
        elif from_type_name == 'landmark':
            instructions += f" past the {from_type_name}"
        
        if to_type_name == 'landmark':
            instructions += f" toward the {to_type_name}"
        elif to_type_name == 'exit':
            instructions += f" to the {to_type_name}"
        
        return instructions
    
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
    
    def recalculate_route(self, current_location: LocationData, destination: str) -> Optional[NavigationRoute]:
        """Recalculate route from current location (useful for route updates)"""
        return self.calculate_route(current_location, destination)
    
    def get_nearby_landmarks(self, location: LocationData, radius: float = 20.0) -> List[NavigationNode]:
        """Find landmarks within specified radius of current location"""
        nearby = []
        
        for node_id, node in self.node_data.items():
            if node.floor_level == location.floor_level:
                distance = self._calculate_distance(location.coordinates, node.coordinates)
                if distance <= radius and node.node_type == 'landmark':
                    nearby.append(node)
        
        # Sort by distance
        nearby.sort(key=lambda x: self._calculate_distance(location.coordinates, x.coordinates))
        return nearby

if __name__ == "__main__":
    # Test the route guidance system
    from qr_reader import LocationData
    
    guidance = RouteGuidance()
    
    # Create test location
    test_location = LocationData(
        node_id="A1",
        coordinates=(0, 0),
        floor_level=1,
        exits={"north": "A2", "east": "B1"},
        timestamp=time.time(),
        confidence=0.9
    )
    
    # Calculate route
    route = guidance.calculate_route(test_location, "C3")
    
    if route:
        print("Route calculated successfully!")
        print(guidance.get_route_summary(route))
    else:
        print("Failed to calculate route")
