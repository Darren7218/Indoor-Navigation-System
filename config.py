"""
Configuration file for Indoor Navigation System
Contains system parameters, color thresholds, and settings
"""

import json
import os

# Color detection thresholds (HSV)
COLOR_THRESHOLDS = {
    'red': {
        'lower1': [0, 100, 100],
        'upper1': [10, 255, 255],
        'lower2': [160, 100, 100],
        'upper2': [180, 255, 255]
    },
    'green': {
        'lower': [40, 100, 100],
        'upper': [80, 255, 255]
    },
    'blue': {
        'lower': [100, 100, 100],
        'upper': [130, 255, 255]
    }
}

# QR Code detection parameters
QR_DETECTION = {
    'min_size': 100,  # Minimum QR code size in pixels
    'max_size': 800,  # Maximum QR code size in pixels
    'confidence_threshold': 0.7,
    'scan_timeout': 5.0  # Seconds to wait for QR detection
}

# Audio feedback settings
AUDIO_SETTINGS = {
    'voice_rate': 150,
    'voice_volume': 0.9,
    'beep_frequency': 1000,
    'beep_duration': 0.1
}

# Navigation settings
NAVIGATION = {
    'recalculation_threshold': 5.0,  # Meters
    'checkpoint_distance': 10.0,    # Meters
    'turn_announcement_distance': 3.0  # Meters
}

# UI settings
UI_SETTINGS = {
    'window_width': 1200,
    'window_height': 800,
    'font_size_large': 24,
    'font_size_medium': 18,
    'font_size_small': 14,
    'high_contrast': True
}

# File paths
PATHS = {
    'floor_maps': 'data/floor_maps/',
    'qr_schemas': 'data/qr_schemas/',
    'audio_cache': 'cache/audio/',
    'logs': 'logs/'
}

def create_directories():
    """Create necessary directories if they don't exist"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

def save_config():
    """Save current configuration to file"""
    config = {
        'color_thresholds': COLOR_THRESHOLDS,
        'qr_detection': QR_DETECTION,
        'audio_settings': AUDIO_SETTINGS,
        'navigation': NAVIGATION,
        'ui_settings': UI_SETTINGS,
        'paths': PATHS
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

def load_config():
    """Load configuration from file"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        # Use default configuration
        return None
