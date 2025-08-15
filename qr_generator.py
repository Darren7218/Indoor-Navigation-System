"""
QR Code Generation Module
Generates colored QR codes for indoor navigation system
Supports multiple color schemes and data formats
"""

import qrcode
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
import os
from typing import Dict, Any, Optional, Tuple, List
import logging

class ColoredQRGenerator:
    """
    A class to generate colored QR codes for indoor navigation.
    Supports multiple color schemes and data formats.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the QR code generator.
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.color_schemes = self._initialize_color_schemes()
        self.setup_logging()
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {config_file} not found, using defaults")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file {config_file}")
            return {}
    
    def _initialize_color_schemes(self) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        """Initialize color schemes based on config."""
        schemes = {
            'red': {
                'primary': (255, 0, 0),      # Bright red
                'secondary': (200, 0, 0),    # Darker red
                'accent': (255, 100, 100)    # Light red
            },
            'green': {
                'primary': (0, 255, 0),      # Bright green
                'secondary': (0, 200, 0),    # Darker green
                'accent': (100, 255, 100)    # Light green
            },
            'blue': {
                'primary': (0, 0, 255),      # Bright blue
                'secondary': (0, 0, 200),    # Darker blue
                'accent': (100, 100, 255)    # Light blue
            },
            'mixed': {
                'primary': (255, 165, 0),    # Orange
                'secondary': (128, 0, 128),  # Purple
                'accent': (255, 255, 0)      # Yellow
            }
        }
        
        # Override with config colors if available
        if 'color_thresholds' in self.config:
            for color_name, thresholds in self.config['color_thresholds'].items():
                if color_name in schemes:
                    # Use the upper threshold values as primary colors
                    if 'upper' in thresholds:
                        schemes[color_name]['primary'] = tuple(thresholds['upper'])
                    elif 'upper1' in thresholds:
                        schemes[color_name]['primary'] = tuple(thresholds['upper1'])
        
        return schemes
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def generate_location_qr(
        self,
        location_data: Dict[str, Any],
        color_scheme: str = 'blue',
        size: int = 400,
        border: int = 4,
        include_logo: bool = False,
        logo_path: Optional[str] = None
    ) -> Image.Image:
        """
        Generate a colored QR code for location data.
        
        Args:
            location_data (Dict[str, Any]): Location information
            color_scheme (str): Color scheme to use ('red', 'green', 'blue', 'mixed')
            size (int): Size of the QR code in pixels
            border (int): Border width around the QR code
            include_logo (bool): Whether to include a logo overlay
            logo_path (Optional[str]): Path to logo image file
            
        Returns:
            PIL.Image.Image: Generated QR code image
        """
        try:
            # Validate color scheme
            if color_scheme not in self.color_schemes:
                color_scheme = 'blue'
                logging.warning(f"Invalid color scheme '{color_scheme}', using 'blue'")
            
            # Convert location data to JSON string
            qr_data = json.dumps(location_data, separators=(',', ':'))
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=border
            )
            
            # Add data to QR code
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create QR code image with custom colors
            colors = self.color_schemes[color_scheme]
            qr_image = qr.make_image(
                fill_color=colors['primary'],
                back_color='white'
            )
            
            # Resize to desired size
            qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)
            
            # Add colored border
            qr_image = self._add_colored_border(qr_image, colors['secondary'], border * 2)
            
            # Add logo if requested
            if include_logo and logo_path:
                qr_image = self._add_logo_overlay(qr_image, logo_path, colors['accent'])
            
            # Add location label
            qr_image = self._add_location_label(qr_image, location_data, colors['primary'])
            
            logging.info(f"Generated QR code for location: {location_data.get('location_id', 'Unknown')}")
            return qr_image
            
        except Exception as e:
            logging.error(f"Error generating QR code: {str(e)}")
            raise
    
    def generate_batch_qr_codes(
        self,
        locations: List[Dict[str, Any]],
        output_dir: str = "data/qr_schemas",
        color_scheme: str = 'blue',
        size: int = 400
    ) -> List[str]:
        """
        Generate multiple QR codes for a list of locations.
        
        Args:
            locations (List[Dict[str, Any]]): List of location data dictionaries
            output_dir (str): Directory to save generated QR codes
            color_scheme (str): Color scheme to use
            size (int): Size of QR codes in pixels
            
        Returns:
            List[str]: List of generated file paths
        """
        generated_files = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        for location in locations:
            try:
                # Generate QR code
                qr_image = self.generate_location_qr(
                    location_data=location,
                    color_scheme=color_scheme,
                    size=size
                )
                
                # Generate filename
                location_id = location.get('location_id', 'unknown')
                filename = f"{location_id}_{color_scheme}_qr.png"
                filepath = os.path.join(output_dir, filename)
                
                # Save image
                qr_image.save(filepath, 'PNG', optimize=True)
                generated_files.append(filepath)
                
                logging.info(f"Saved QR code: {filepath}")
                
            except Exception as e:
                logging.error(f"Error generating QR code for {location}: {str(e)}")
                continue
        
        return generated_files
    
    def generate_color_coded_qr(
        self,
        location_data: Dict[str, Any],
        floor_level: Optional[str] = None,
        size: int = 400
    ) -> Image.Image:
        """
        Generate a QR code with color coding based on floor level.
        
        Args:
            location_data (Dict[str, Any]): Location information
            floor_level (Optional[str]): Floor level for color coding
            size (int): Size of QR code in pixels
            
        Returns:
            PIL.Image.Image: Generated QR code image
        """
        # Determine color scheme based on floor level
        if floor_level:
            floor_num = str(floor_level).lower()
            if 'ground' in floor_num or '0' in floor_num:
                color_scheme = 'green'
            elif '1' in floor_num or 'first' in floor_num:
                color_scheme = 'blue'
            elif '2' in floor_num or 'second' in floor_num:
                color_scheme = 'red'
            else:
                color_scheme = 'mixed'
        else:
            color_scheme = 'blue'
        
        return self.generate_location_qr(
            location_data=location_data,
            color_scheme=color_scheme,
            size=size
        )
    
    def _add_colored_border(self, image: Image.Image, color: Tuple[int, int, int], border_width: int) -> Image.Image:
        """Add a colored border around the QR code."""
        # Create new image with border
        new_size = (image.width + border_width * 2, image.height + border_width * 2)
        bordered_image = Image.new('RGB', new_size, color)
        
        # Paste original image in center
        bordered_image.paste(image, (border_width, border_width))
        
        return bordered_image
    
    def _add_logo_overlay(self, image: Image.Image, logo_path: str, accent_color: Tuple[int, int, int]) -> Image.Image:
        """Add a logo overlay to the center of the QR code."""
        try:
            # Load and resize logo
            logo = Image.open(logo_path).convert('RGBA')
            logo_size = min(image.width, image.height) // 4
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Create a white background for logo
            logo_bg = Image.new('RGBA', logo.size, (255, 255, 255, 200))
            logo = Image.alpha_composite(logo_bg, logo)
            
            # Calculate position (center of QR code)
            x = (image.width - logo_size) // 2
            y = (image.height - logo_size) // 2
            
            # Convert main image to RGBA for overlay
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Create new image with logo
            result = image.copy()
            result.paste(logo, (x, y), logo)
            
            return result.convert('RGB')
            
        except Exception as e:
            logging.warning(f"Could not add logo overlay: {str(e)}")
            return image
    
    def _add_location_label(self, image: Image.Image, location_data: Dict[str, Any], color: Tuple[int, int, int]) -> Image.Image:
        """Add a location label below the QR code."""
        try:
            # Create new image with space for label
            label_height = 60
            new_size = (image.width, image.height + label_height)
            labeled_image = Image.new('RGB', new_size, 'white')
            
            # Paste original image
            labeled_image.paste(image, (0, 0))
            
            # Create label
            draw = ImageDraw.Draw(labeled_image)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Get location text
            location_id = location_data.get('location_id', 'Unknown Location')
            floor_level = location_data.get('floor_level', '')
            description = location_data.get('description', '')
            
            # Create label text
            label_text = f"{location_id}"
            if floor_level:
                label_text += f" (Floor {floor_level})"
            if description:
                label_text += f" - {description}"
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (image.width - text_width) // 2
            text_y = image.height + 20
            
            # Draw text
            draw.text((text_x, text_y), label_text, fill=color, font=font)
            
            return labeled_image
            
        except Exception as e:
            logging.warning(f"Could not add location label: {str(e)}")
            return image
    
    def create_sample_locations(self) -> List[Dict[str, Any]]:
        """Create sample location data for testing."""
        return [
            {
                "location_id": "ROOM_101",
                "floor_level": "1",
                "coordinates": "10,20",
                "description": "Main Office"
            },
            {
                "location_id": "ROOM_102",
                "floor_level": "1",
                "coordinates": "15,25",
                "description": "Conference Room"
            },
            {
                "location_id": "EXIT_A",
                "floor_level": "0",
                "coordinates": "5,5",
                "description": "Main Exit"
            },
            {
                "location_id": "STAIRS_1",
                "floor_level": "1",
                "coordinates": "20,10",
                "description": "Stairwell to Ground Floor"
            }
        ]


def main():
    """Main function to demonstrate QR code generation."""
    # Initialize generator
    generator = ColoredQRGenerator()
    
    # Create sample locations
    sample_locations = generator.create_sample_locations()
    
    print("Generating sample QR codes...")
    
    # Generate QR codes for each location
    for location in sample_locations:
        try:
            # Generate QR code with appropriate color scheme
            qr_image = generator.generate_color_coded_qr(location)
            
            # Save to file
            filename = f"{location['location_id']}_qr.png"
            qr_image.save(filename, 'PNG')
            print(f"Generated: {filename}")
            
        except Exception as e:
            print(f"Error generating QR code for {location['location_id']}: {str(e)}")
    
    print("\nQR code generation complete!")
    print("Generated files:")
    for file in os.listdir('.'):
        if file.endswith('_qr.png'):
            print(f"  - {file}")


if __name__ == "__main__":
    main()
