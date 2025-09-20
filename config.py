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
    'beep_duration': 0.1,
    # Coqui TTS settings
    'use_tts': True,
    'tts_model': 'tts_models/en/vctk/vits',
    'speaker_id': 'p360',
    'device_preference': 'auto'  # 'auto' | 'cpu' | 'cuda'
}

# Navigation settings
NAVIGATION = {
    'recalculation_threshold': 5.0,  # Meters
    'checkpoint_distance': 10.0,    # Meters
    'turn_announcement_distance': 3.0  # Meters
}


#  QRDET(YOLOv8-based specialized QR detector) settings
QRDET_SETTINGS = {
    'enabled': True,              # Prefer QRDet for robust QR box proposals
    'model_size': 's',            # 'n'|'s'|'m'|'l'
    'conf_th': 0.6,
    'nms_iou': 0.3
}

# UI settings
UI_SETTINGS = {
    'window_width': 1200,
    'window_height': 800,
    'font_size_large': 24,
    'font_size_medium': 18,
    'font_size_small': 14,
    'high_contrast': True,
    'theme': 'light'  # 'light' or 'dark'
}

# Theme configurations
THEMES = {
    'light': {
        'window_bg': '#f0f0f0',
        'text_color': '#000000',
        'button_bg': '#e0e0e0',
        'button_text': '#000000',
        'highlight_bg': '#0078d4',
        'highlight_text': '#ffffff',
        'border_color': '#c0c0c0',
        'status_online': '#28a745',
        'status_offline': '#dc3545',
        'warning_color': '#ffc107'
    },
    'dark': {
        'window_bg': '#2d2d30',
        'text_color': '#ffffff',
        'button_bg': '#3e3e42',
        'button_text': '#ffffff',
        'highlight_bg': '#0078d4',
        'highlight_text': '#ffffff',
        'border_color': '#555555',
        'status_online': '#28a745',
        'status_offline': '#dc3545',
        'warning_color': '#ffc107'
    }
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


