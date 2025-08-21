"""
User Interface Module
Accessible PyQt5 interface with audio feedback and high-contrast design
Optimized for visually impaired users
"""

import sys
import time
import logging
from typing import Optional, List
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QComboBox, QSlider, QGroupBox, QGridLayout,
                             QProgressBar, QMessageBox, QFrame, QAction, QMenuBar)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
import numpy as np
import cv2

from qr_detection import QRCodeDetector
from qr_reader import QRCodeReader, LocationData
from fic_navigation_integration import FICTNavigationSystem, NavigationRoute
from config import UI_SETTINGS, AUDIO_SETTINGS, THEMES
from audio_feedback import AudioFeedback
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None  # type: ignore

from queue import Queue
from threading import Thread

class Beeper:
    """Placeholder beep handler (logs only)."""
    def play_beep(self, frequency: int = None, duration: float = None):
        if frequency is None:
            frequency = AUDIO_SETTINGS['beep_frequency']
        if duration is None:
            duration = AUDIO_SETTINGS['beep_duration']
        try:
            import sys as _sys
            if _sys.platform.startswith('win'):
                import winsound
                winsound.Beep(int(frequency), int(duration * 1000))
            else:
                logging.info(f"Beep: {frequency}Hz for {duration}s (winsound not available)")
        except Exception:
            logging.info(f"Beep: {frequency}Hz for {duration}s (failed to play)")

class AutoVoiceSpeaker:
    """Threaded voice speaker for route instructions using pyttsx3."""
    def __init__(self, rate: int = 160, volume: float = 0.9):
        self.engine = None
        self.available = False
        self.rate = rate
        self.volume = volume
        self.queue = Queue()
        self.running = True
        self.thread = None
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            if pyttsx3 is None:
                logging.warning("pyttsx3 not available")
                return
                
            self.engine = pyttsx3.init()
            logging.info("pyttsx3 engine initialized")
            
            # Configure voice
            try:
                voices = self.engine.getProperty('voices')  # type: ignore
                logging.info(f"Found {len(voices)} available voices")
                
                selected = None
                for v in voices:
                    name = getattr(v, 'name', '')
                    lname = name.lower() if isinstance(name, str) else ''
                    if 'female' in lname or 'zira' in lname or 'aria' in lname or 'jenny' in lname:
                        selected = v
                        break
                if selected is None and voices:
                    selected = voices[0]
                if selected is not None:
                    self.engine.setProperty('voice', selected.id)  # type: ignore
                    logging.info(f"Selected voice: {selected.name}")
            except Exception as e:
                logging.warning(f"Error setting voice: {e}")
                
            # Configure rate and volume
            try:
                self.engine.setProperty('rate', int(self.rate))  # type: ignore
                self.engine.setProperty('volume', float(self.volume))  # type: ignore
                logging.info(f"Set rate: {self.rate}, volume: {self.volume}")
            except Exception as e:
                logging.warning(f"Error setting rate/volume: {e}")
                
            self.available = True
            logging.info("AutoVoiceSpeaker initialized successfully")
            
            # Start the speech processing thread
            self.thread = Thread(target=self._process_queue, daemon=True)
            self.thread.start()
            logging.info("Speech processing thread started")
            
        except Exception as e:
            logging.error(f"Failed to initialize AutoVoiceSpeaker: {e}")
            self.available = False

    def _process_queue(self):
        """Continuously read queue and speak without blocking GUI"""
        logging.info("Speech processing thread started")
        while self.running:
            try:
                text, priority = self.queue.get(timeout=1.0)  # 1 second timeout
                if not text:
                    continue
                    
                logging.info(f"Processing speech: '{text}' (priority: {priority})")
                
                if priority and self.engine:
                    try:
                        self.engine.stop()  # type: ignore
                        logging.info("Stopped current speech due to priority")
                    except Exception as e:
                        logging.warning(f"Error stopping speech: {e}")
                        
                if self.engine:
                    try:
                        self.engine.say(text)  # type: ignore
                        self.engine.runAndWait()  # type: ignore
                        logging.info(f"Successfully spoke: '{text}'")
                    except Exception as e:
                        logging.error(f"Error speaking text: {e}")
                    
            except Exception as e:
                # Timeout or other error, continue
                if "Empty" not in str(e):  # Don't log timeout exceptions
                    logging.warning(f"Speech processing error: {e}")
                continue

    def speak(self, text: str, priority: bool = False) -> None:
        """Queue a new message to speak without blocking"""
        if not text:
            logging.warning("Empty text provided to speak")
            return
        if not self.available:
            logging.warning("AutoVoiceSpeaker not available")
            return
        try:
            self.queue.put((text, priority))
            logging.info(f"Queued speech: '{text}' (priority: {priority})")
        except Exception as e:
            logging.error(f"Error queuing speech: {e}")

    def shutdown(self) -> None:
        """Stop speaker cleanly"""
        logging.info("Shutting down AutoVoiceSpeaker")
        self.running = False
        try:
            if self.engine is not None:
                self.engine.stop()  # type: ignore
                logging.info("Stopped pyttsx3 engine")
        except Exception as e:
            logging.error(f"Error stopping engine: {e}")

class CameraThread(QThread):
    """Thread for handling camera operations"""
    
    frame_ready = pyqtSignal(np.ndarray)
    qr_detected = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = False
        self.detector = None
    
    def run(self):
        """Main thread loop for camera processing"""
        try:
            self.detector = QRCodeDetector(self.camera_index)
            
            # Check if camera was initialized successfully
            if not self.detector.cap or not self.detector.cap.isOpened():
                self.error_occurred.emit("Failed to initialize camera")
                return
            
            self.is_running = True
            
            while self.is_running:
                if self.detector.cap and self.detector.cap.isOpened():
                    ret, frame = self.detector.cap.read()
                    if ret:
                        try:
                            # Process frame for QR detection (color + optional YOLO)
                            regions = self.detector._find_color_regions(frame)
                            if hasattr(self.detector, 'yolo_model') and self.detector.yolo_model is not None:
                                try:
                                    regions += self.detector._find_yolo_regions(frame)
                                except Exception:
                                    pass
                            if hasattr(self.detector, 'qrdet_model') and self.detector.qrdet_model is not None:
                                try:
                                    regions += self.detector._find_qrdet_regions(frame)
                                except Exception:
                                    pass
                            detected_qrs = []
                            
                            for entry in regions:
                                if len(entry) == 3:
                                    color, roi, bbox = entry
                                    if self.detector._detect_qr_in_region(roi):
                                        detected_qrs.append((color, roi, bbox))
                                elif len(entry) >= 4:
                                    color, roi, bbox, quad = entry[0], entry[1], entry[2], entry[3]
                                    # Try polygon warp first if available
                                    warped = self.detector._warp_from_quad(frame, quad)
                                    if warped is not None and self.detector._detect_qr_in_region(warped):
                                        detected_qrs.append((color, roi, bbox))
                                    else:
                                        if self.detector._detect_qr_in_region(roi):
                                            detected_qrs.append((color, roi, bbox))
                            
                            # Emit signals
                            self.frame_ready.emit(frame)
                            if detected_qrs:
                                self.qr_detected.emit(detected_qrs)
                            
                            # Small delay to prevent overwhelming the system
                            time.sleep(0.033)  # ~30 FPS
                        except Exception as e:
                            # Continue processing even if frame processing fails
                            logging.warning(f"Frame processing error: {e}")
                            continue
                    else:
                        self.error_occurred.emit("Failed to read camera frame")
                        break
                else:
                    self.error_occurred.emit("Camera not available")
                    break
                    
        except Exception as e:
            self.error_occurred.emit(f"Camera thread error: {e}")
        finally:
            if self.detector:
                self.detector.stop_detection()
    
    def stop(self):
        """Stop the camera thread"""
        self.is_running = False
        if self.detector:
            self.detector.stop_detection()

class NavigationInterface(QMainWindow):
    """Main navigation interface for visually impaired users"""
    
    def __init__(self):
        super().__init__()
        self.audio_feedback = AudioFeedback()
        self._beeper = Beeper()
        # Use the same audio feedback instance instead of creating a separate AutoVoiceSpeaker
        self.auto_speaker = self.audio_feedback
        self.qr_reader = QRCodeReader()
        self.fict_nav = FICTNavigationSystem()
        
        self.current_location = None
        self.current_route = None
        self.camera_thread = None
        
        self._init_ui()
        self._setup_audio_feedback()
    
    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Indoor Navigation System - Accessible Interface")
        self.setGeometry(100, 100, UI_SETTINGS['window_width'], UI_SETTINGS['window_height'])
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create UI sections
        self._create_header_section(main_layout)
        self._create_camera_section(main_layout)
        self._create_navigation_section(main_layout)
        self._create_control_section(main_layout)
        self._create_status_section(main_layout)
        
        # Apply current theme
        self._apply_theme(UI_SETTINGS['theme'])
        
        # Set focus for keyboard navigation
        self.setFocusPolicy(Qt.StrongFocus)
    
    def _create_menu_bar(self):
        """Create menu bar with theme switching"""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Theme submenu
        theme_menu = view_menu.addMenu('Theme')
        
        # Light theme action
        light_action = QAction('Light Theme', self)
        light_action.setCheckable(True)
        light_action.setChecked(UI_SETTINGS['theme'] == 'light')
        light_action.triggered.connect(lambda: self._switch_theme('light'))
        theme_menu.addAction(light_action)
        
        # Dark theme action
        dark_action = QAction('Dark Theme', self)
        dark_action.setCheckable(True)
        dark_action.setChecked(UI_SETTINGS['theme'] == 'dark')
        dark_action.triggered.connect(lambda: self._switch_theme('dark'))
        theme_menu.addAction(dark_action)
        
        # High contrast toggle
        contrast_action = QAction('High Contrast', self)
        contrast_action.setCheckable(True)
        contrast_action.setChecked(UI_SETTINGS['high_contrast'])
        contrast_action.triggered.connect(self._toggle_high_contrast)
        view_menu.addAction(contrast_action)
    
    def _switch_theme(self, theme_name):
        """Switch between light and dark themes"""
        if theme_name in THEMES:
            UI_SETTINGS['theme'] = theme_name
            self._apply_theme(theme_name)
            self.audio_feedback.speak(f"Switched to {theme_name} theme")
    
    def _toggle_high_contrast(self):
        """Toggle high contrast mode"""
        UI_SETTINGS['high_contrast'] = not UI_SETTINGS['high_contrast']
        self._apply_theme(UI_SETTINGS['theme'])
        status = "enabled" if UI_SETTINGS['high_contrast'] else "disabled"
        self.audio_feedback.speak(f"High contrast {status}")
    
    def _apply_theme(self, theme_name):
        """Apply the specified theme"""
        if theme_name not in THEMES:
            return
        
        theme = THEMES[theme_name]
        
        # Create palette
        palette = QPalette()
        
        if UI_SETTINGS['high_contrast']:
            # High contrast mode
            if theme_name == 'light':
                palette.setColor(QPalette.Window, QColor(255, 255, 255))
                palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
                palette.setColor(QPalette.Base, QColor(255, 255, 255))
                palette.setColor(QPalette.Text, QColor(0, 0, 0))
                palette.setColor(QPalette.Button, QColor(0, 0, 0))
                palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            else:  # dark
                palette.setColor(QPalette.Window, QColor(0, 0, 0))
                palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
                palette.setColor(QPalette.Base, QColor(0, 0, 0))
                palette.setColor(QPalette.Text, QColor(255, 255, 255))
                palette.setColor(QPalette.Button, QColor(255, 255, 255))
                palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        else:
            # Normal theme mode
            palette.setColor(QPalette.Window, QColor(theme['window_bg']))
            palette.setColor(QPalette.WindowText, QColor(theme['text_color']))
            palette.setColor(QPalette.Base, QColor(theme['window_bg']))
            palette.setColor(QPalette.AlternateBase, QColor(theme['button_bg']))
            palette.setColor(QPalette.Text, QColor(theme['text_color']))
            palette.setColor(QPalette.Button, QColor(theme['button_bg']))
            palette.setColor(QPalette.ButtonText, QColor(theme['button_text']))
            palette.setColor(QPalette.Highlight, QColor(theme['highlight_bg']))
            palette.setColor(QPalette.HighlightedText, QColor(theme['highlight_text']))
        
        self.setPalette(palette)
        
        # Update status indicator colors
        if hasattr(self, 'status_indicator'):
            self._update_status_colors(theme)
    
    def _update_status_colors(self, theme):
        """Update status indicator colors based on theme"""
        if hasattr(self, 'status_indicator'):
            # This will be updated when status changes
            pass
    
    def _create_header_section(self, layout):
        """Create the header section with title and status"""
        header_group = QGroupBox("Navigation System Status")
        header_layout = QHBoxLayout(header_group)
        
        # Title
        title_label = QLabel("Indoor Navigation System")
        title_font = QFont()
        title_font.setPointSize(UI_SETTINGS['font_size_large'])
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: red; font-size: 24px;")
        self.status_indicator.setToolTip("System Status: Red = Offline, Green = Online")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        
        layout.addWidget(header_group)
    
    def _create_camera_section(self, layout):
        """Create the camera feed section"""
        camera_group = QGroupBox("Camera Feed & QR Detection")
        camera_layout = QVBoxLayout(camera_group)
        
        # Camera controls
        camera_controls = QHBoxLayout()
        
        self.start_camera_btn = QPushButton("Start Camera")
        self.start_camera_btn.setFont(self._get_large_font())
        self.start_camera_btn.clicked.connect(self._start_camera)
        
        self.stop_camera_btn = QPushButton("Stop Camera")
        self.stop_camera_btn.setFont(self._get_large_font())
        self.stop_camera_btn.clicked.connect(self._stop_camera)
        self.stop_camera_btn.setEnabled(False)
        
        self.tips_btn = QPushButton("QR Tips")
        self.tips_btn.setFont(self._get_medium_font())
        self.tips_btn.clicked.connect(self._show_qr_scanning_tips)
        self.tips_btn.setToolTip("Show tips for better QR code scanning")
        
        camera_controls.addWidget(self.start_camera_btn)
        camera_controls.addWidget(self.stop_camera_btn)
        camera_controls.addWidget(self.tips_btn)
        camera_controls.addStretch()
        
        # Camera feed display (placeholder for actual video widget)
        self.camera_display = QLabel("Camera feed will appear here")
        self.camera_display.setMinimumSize(400, 300)
        self.camera_display.setStyleSheet("border: 2px solid gray; background-color: black; color: white;")
        self.camera_display.setAlignment(Qt.AlignCenter)
        
        # QR detection status
        self.qr_status_label = QLabel("No QR code detected")
        self.qr_status_label.setFont(self._get_medium_font())
        self.qr_status_label.setStyleSheet("color: orange;")
        self.qr_status_label.setToolTip("Shows QR code detection status and tips for better scanning")
        
        camera_layout.addLayout(camera_controls)
        camera_layout.addWidget(self.camera_display)
        camera_layout.addWidget(self.qr_status_label)
        
        layout.addWidget(camera_group)
    
    def _create_navigation_section(self, layout):
        """Create the navigation section"""
        nav_group = QGroupBox("Navigation & Route Guidance")
        nav_layout = QVBoxLayout(nav_group)
        
        # Current location display
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Current Location:"))
        self.location_label = QLabel("Unknown")
        self.location_label.setFont(self._get_medium_font())
        self.location_label.setStyleSheet("color: yellow; font-weight: bold;")
        location_layout.addWidget(self.location_label)
        location_layout.addStretch()
        
        # Destination selection
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Destination:"))
        self.destination_combo = QComboBox()
        self.destination_combo.setFont(self._get_medium_font())
        # Populate FICT destinations
        dests = ["Select destination..."] + self.fict_nav.get_available_destinations()
        self.destination_combo.addItems(dests)
        dest_layout.addWidget(self.destination_combo)
        
        self.calculate_route_btn = QPushButton("Calculate Route")
        self.calculate_route_btn.setFont(self._get_medium_font())
        self.calculate_route_btn.clicked.connect(self._calculate_route)
        self.calculate_route_btn.setEnabled(False)
        dest_layout.addWidget(self.calculate_route_btn)
        
        nav_layout.addLayout(location_layout)
        nav_layout.addLayout(dest_layout)
        
        # Route display
        self.route_display = QTextEdit()
        self.route_display.setFont(self._get_small_font())
        self.route_display.setMaximumHeight(150)
        self.route_display.setPlaceholderText("Route information will appear here...")
        
        nav_layout.addWidget(self.route_display)
        
        layout.addWidget(nav_group)
    
    def _create_control_section(self, layout):
        """Create the control section"""
        control_group = QGroupBox("System Controls")
        control_layout = QGridLayout(control_group)
        
        # Simple status label
        self.voice_status_label = QLabel("Voice: Ready")
        self.voice_status_label.setFont(self._get_medium_font())
        self.voice_status_label.setStyleSheet("color: green;")
        
        # Add status to grid
        control_layout.addWidget(self.voice_status_label, 0, 0, 1, 2)
        
        # Add a test voice button
        self.test_voice_btn = QPushButton("Test Voice")
        self.test_voice_btn.setFont(self._get_medium_font())
        self.test_voice_btn.clicked.connect(self._test_voice)
        control_layout.addWidget(self.test_voice_btn, 1, 0, 1, 2)
        
        layout.addWidget(control_group)
    
    def _create_status_section(self, layout):
        """Create the status section"""
        status_group = QGroupBox("System Status & Logs")
        status_layout = QVBoxLayout(status_group)
        
        # Progress bar for navigation
        self.navigation_progress = QProgressBar()
        self.navigation_progress.setVisible(False)
        
        # Status log
        self.status_log = QTextEdit()
        self.status_log.setFont(self._get_small_font())
        self.status_log.setMaximumHeight(100)
        self.status_log.setReadOnly(True)
        
        status_layout.addWidget(self.navigation_progress)
        status_layout.addWidget(self.status_log)
        
        layout.addWidget(status_group)
    
    def _get_large_font(self):
        """Get large font for important elements"""
        font = QFont()
        font.setPointSize(UI_SETTINGS['font_size_large'])
        return font
    
    def _get_medium_font(self):
        """Get medium font for standard elements"""
        font = QFont()
        font.setPointSize(UI_SETTINGS['font_size_medium'])
        return font
    
    def _get_small_font(self):
        """Get small font for detailed information"""
        font = QFont()
        font.setPointSize(UI_SETTINGS['font_size_small'])
        return font
    
    def _setup_audio_feedback(self):
        """Setup initial audio feedback"""
        # Always queue; the worker will speak when ready
        self.audio_feedback.speak("Navigation system initialized and ready")
        self._log_status("System initialized with audio feedback")
    
    def _start_camera(self):
        """Start the camera and QR detection"""
        try:
            # Start the QR reader camera as well
            if not self.qr_reader.start_camera():
                self._log_status("Warning: QR reader camera could not be started")
            
            self.camera_thread = CameraThread()
            self.camera_thread.frame_ready.connect(self._update_camera_display)
            self.camera_thread.qr_detected.connect(self._handle_qr_detection)
            self.camera_thread.error_occurred.connect(self._handle_camera_error)
            
            self.camera_thread.start()
            
            self.start_camera_btn.setEnabled(False)
            self.stop_camera_btn.setEnabled(True)
            self.status_indicator.setStyleSheet("color: green; font-size: 24px;")
            
            self._log_status("Camera started")
            self.audio_feedback.speak("Camera started, scanning for QR codes")
            
        except Exception as e:
            self._log_status(f"Error starting camera: {e}")
            QMessageBox.critical(self, "Camera Error", f"Failed to start camera: {e}")
    
    def _stop_camera(self):
        """Stop the camera and QR detection"""
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread.wait()
            self.camera_thread = None
        
        # Stop the QR reader camera as well
        self.qr_reader.stop_camera()
        
        self.start_camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)
        self.status_indicator.setStyleSheet("color: red; font-size: 24px;")
        
        self.camera_display.setText("Camera stopped")
        self.qr_status_label.setText("No QR code detected")
        
        self._log_status("Camera stopped")
        self.audio_feedback.speak("Camera stopped")
    
    def _update_camera_display(self, frame):
        """Update the camera display with new frame"""
        # Convert frame to QPixmap for display
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage and QPixmap
        from PyQt5.QtGui import QImage
        q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale to fit display
        scaled_pixmap = pixmap.scaled(self.camera_display.size(), Qt.KeepAspectRatio)
        self.camera_display.setPixmap(scaled_pixmap)
    
    def _handle_qr_detection(self, detected_qrs):
        """Handle detected QR codes"""
        if not detected_qrs:
            return
        
        # Process the first detected QR code
        color, roi, bbox = detected_qrs[0]
        
        # Try to decode the QR code using the detected region
        try:
            # Use the QR detector from the camera thread's detector
            if hasattr(self.camera_thread, 'detector') and hasattr(self.camera_thread.detector, 'qr_detector'):
                data, bbox, _ = self.camera_thread.detector.qr_detector.detectAndDecode(roi)
            else:
                # Fallback to creating a new detector
                qr_detector = cv2.QRCodeDetector()
                data, bbox, _ = qr_detector.detectAndDecode(roi)
            
            if data:
                # Create LocationData from the decoded data
                location_data = LocationData(data)
                
                if location_data.is_valid():
                    self.current_location = location_data
                    # Update FICT current location if possible
                    self.fict_nav.set_current_location_from_locationdata(location_data)
                    self._update_location_display(location_data)
                    self._log_status(f"QR code decoded: {location_data.location_id}")
                    
                    self.audio_feedback.speak(f"Location identified: {location_data.location_id}")
                    
                    # Enable route calculation
                    self.calculate_route_btn.setEnabled(True)
                else:
                    self._log_status("QR code detected but data is invalid")
                    self.audio_feedback.speak("QR code detected but data is invalid")
            else:
                self._log_status("QR code detected but could not be decoded")
                self.audio_feedback.speak("QR code detected but could not be read")
                    
        except Exception as e:
            self._log_status(f"Error decoding QR code: {e}")
            if self.auto_speaker.available:
                self.auto_speaker.speak("Error decoding QR code")
    
    def _handle_camera_error(self, error_msg):
        """Handle camera errors"""
        self._log_status(f"Camera error: {error_msg}")
        QMessageBox.warning(self, "Camera Error", f"Camera error: {error_msg}")
        self._stop_camera()
    
    def _update_location_display(self, location_data: LocationData):
        """Update the location display"""
        location_text = f"{location_data.location_id} (Floor {location_data.floor_level or 'Unknown'})"
        self.location_label.setText(location_text)
        self.qr_status_label.setText(f"QR detected: {location_data.location_id}")
        self.qr_status_label.setStyleSheet("color: green;")
    
    def _calculate_route(self):
        """Calculate route to selected destination"""
        if not self.current_location:
            QMessageBox.warning(self, "No Location", "Please scan a QR code first to determine your location")
            return
        
        destination = self.destination_combo.currentText()
        if destination == "Select destination...":
            QMessageBox.warning(self, "No Destination", "Please select a destination")
            return
        
        try:
            # Calculate route via FICT integration (uses QR payload + FICT catalog)
            route_info = self.fict_nav.get_navigation_route(destination)
            
            if route_info and 'route' in route_info:
                route = route_info['route']
                self.current_route = route
                self._display_route(route)
                self._log_status(f"Route calculated to {destination}")
                
                # Automatically speak route instructions
                self._speak_route_instructions(route_info)
                
            else:
                QMessageBox.information(self, "No Route", f"No route found to {destination}")
                self._log_status(f"No route found to {destination}")
                
        except Exception as e:
            self._log_status(f"Error calculating route: {e}")
            QMessageBox.critical(self, "Route Error", f"Failed to calculate route: {e}")
    
    def _display_route(self, route: NavigationRoute):
        """Display the calculated route"""
        route_summary = self.fict_nav.get_route_summary(route)
        self.route_display.setText(route_summary)
        
        # Show progress bar
        self.navigation_progress.setVisible(True)
        self.navigation_progress.setMaximum(len(route.segments))
        self.navigation_progress.setValue(0)
    
    def _speak_route_instructions(self, route_info):
        """Automatically speak route instructions after calculation."""
        self._log_status("Starting route voice instructions...")
        
        # Audible cue to confirm audio path
        try:
            self._beeper.play_beep()
        except Exception:
            pass
        
        try:
            # Debug: Log the route_info structure
            self._log_status(f"Route info keys: {list(route_info.keys())}")
            
            # Get destination info - the destination key contains the location data
            destination_data = route_info.get('destination', {})
            self._log_status(f"Destination data keys: {list(destination_data.keys())}")
            
            destination_id = destination_data.get('description', 'Unknown destination')
            
            self._log_status(f"Speaking route to: {destination_id}")
            
            # Use direct pyttsx3 since we know it works
            import pyttsx3
            engine = pyttsx3.init(driverName='sapi5')
            engine.setProperty('volume', 1.0)
            engine.setProperty('rate', 150)
            
            # Speak route summary
            route_summary = f"Route to {destination_id} calculated. Starting navigation instructions."
            engine.say(route_summary)
            engine.runAndWait()
            self._log_status(f"Spoke route summary: {route_summary}")
            
            # Speak each instruction in sequence
            instructions = route_info.get('instructions', [])
            if instructions:
                self._log_status(f"Found {len(instructions)} instructions to speak")
                for i, instruction in enumerate(instructions, 1):
                    instruction_text = f"Step {i}: {instruction}"
                    engine.say(instruction_text)
                    engine.runAndWait()
                    time.sleep(0.5)  # Small pause between instructions
                    self._log_status(f"Spoke instruction {i}: {instruction_text}")
            else:
                self._log_status("No instructions found, speaking fallback message")
                engine.say("No detailed instructions available for this route.")
                engine.runAndWait()
            
            # Speak completion message
            completion_msg = "Navigation instructions complete. Follow the steps to reach your destination."
            engine.say(completion_msg)
            engine.runAndWait()
            self._log_status(f"Spoke completion message: {completion_msg}")
            
            self._log_status("Route voice instructions completed")
            
        except Exception as e:
            self._log_status(f"Error speaking route: {e}")
            import traceback
            self._log_status(f"Traceback: {traceback.format_exc()}")

    def _test_voice(self):
        """Test the voice system"""
        self._log_status("Testing voice system...")
        
        # Test beep first
        try:
            self._beeper.play_beep()
        except Exception:
            pass
        
        # Use direct pyttsx3 since we know it works
        try:
            import pyttsx3
            engine = pyttsx3.init(driverName='sapi5')
            engine.setProperty('volume', 1.0)
            engine.setProperty('rate', 150)
            
            # Test messages
            engine.say("Voice test. The navigation system is ready to guide you.")
            engine.runAndWait()
            time.sleep(0.5)
            
            engine.say("Voice test complete.")
            engine.runAndWait()
            
            self._log_status("Voice test completed successfully")
        except Exception as e:
            self._log_status(f"Voice test failed: {e}")
            QMessageBox.warning(self, "Voice Test", f"Voice test failed: {e}")
    
    def _log_status(self, message: str):
        """Log status message to the status log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.status_log.append(log_entry)
        
        # Keep only last 100 lines
        lines = self.status_log.toPlainText().split('\n')
        if len(lines) > 100:
            self.status_log.setPlainText('\n'.join(lines[-100:]))
    
    def _show_qr_scanning_tips(self):
        """Show helpful tips for QR code scanning"""
        tips = [
            "💡 QR Scanning Tips:",
            "• Ensure good lighting - avoid shadows and glare",
            "• Hold camera steady and parallel to QR code",
            "• Keep QR code centered in the colored region",
            "• Maintain distance of 20-50cm from QR code",
            "• Make sure QR code is not wrinkled or damaged",
            "• Try different angles if detection fails"
        ]
        
        tip_text = "\n".join(tips)
        QMessageBox.information(self, "QR Scanning Tips", tip_text)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Space:
            # Spacebar toggles audio
            pass # No audio toggle in this version
        elif event.key() == Qt.Key_C:
            # C key toggles camera
            if self.start_camera_btn.isEnabled():
                self._start_camera()
            else:
                self._stop_camera()
        elif event.key() == Qt.Key_R:
            # R key recalculates route
            if self.calculate_route_btn.isEnabled():
                self._calculate_route()
        elif event.key() == Qt.Key_Escape:
            # Escape key closes the application
            self.close()
    
    def closeEvent(self, event):
        """Handle application closure"""
        if self.camera_thread:
            self._stop_camera()
        
        self.audio_feedback.speak("Navigation system shutting down")
        # Ensure audio worker stops
        try:
            if hasattr(self, 'audio_feedback') and self.audio_feedback:
                self.audio_feedback.shutdown()
        except Exception:
            pass
        
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Indoor Navigation System")
    app.setApplicationVersion("1.0.0")
    
    # Create and show the main window
    window = NavigationInterface()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
