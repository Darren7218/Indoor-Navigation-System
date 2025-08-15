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
import pyttsx3
import numpy as np
import cv2

from qr_detection import QRCodeDetector
from qr_reader import QRCodeReader, LocationData
from route_guidance import RouteGuidance, NavigationRoute
from fic_navigation_integration import FICTNavigationSystem
from config import UI_SETTINGS, AUDIO_SETTINGS, THEMES

class AudioFeedback:
    """Handles text-to-speech and audio feedback"""
    
    def __init__(self):
        self.engine = None
        self.is_initialized = False
        self._init_tts()
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', AUDIO_SETTINGS['voice_rate'])
            self.engine.setProperty('volume', AUDIO_SETTINGS['voice_volume'])
            self.is_initialized = True
            logging.info("Text-to-speech engine initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize TTS engine: {e}")
            self.is_initialized = False
    
    def speak(self, text: str, priority: bool = False):
        """Speak text using TTS engine"""
        if not self.is_initialized or not text:
            return
        
        try:
            if priority:
                # Stop any current speech for priority messages
                self.engine.stop()
            
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS error: {e}")
    
    def play_beep(self, frequency: int = None, duration: float = None):
        """Play a beep sound (placeholder for actual audio implementation)"""
        if frequency is None:
            frequency = AUDIO_SETTINGS['beep_frequency']
        if duration is None:
            duration = AUDIO_SETTINGS['beep_duration']
        
        # In a real implementation, you would use PyAudio or similar
        # For now, we'll just log the beep
        logging.info(f"Beep: {frequency}Hz for {duration}s")

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
                            # Process frame for QR detection
                            color_regions = self.detector._find_color_regions(frame)
                            detected_qrs = []
                            
                            for color, roi, bbox in color_regions:
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
        self.qr_reader = QRCodeReader()
        self.route_guidance = RouteGuidance()
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
        
        camera_controls.addWidget(self.start_camera_btn)
        camera_controls.addWidget(self.stop_camera_btn)
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
        
        # Audio controls
        self.audio_enabled = True
        self.audio_toggle_btn = QPushButton("Audio: ON")
        self.audio_toggle_btn.setFont(self._get_medium_font())
        self.audio_toggle_btn.clicked.connect(self._toggle_audio)
        
        # Volume control
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(90)
        self.volume_slider.valueChanged.connect(self._adjust_volume)
        
        # Voice rate control
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(50, 300)
        self.rate_slider.setValue(150)
        self.rate_slider.valueChanged.connect(self._adjust_speech_rate)
        
        # Test audio button
        self.test_audio_btn = QPushButton("Test Audio")
        self.test_audio_btn.setFont(self._get_medium_font())
        self.test_audio_btn.clicked.connect(self._test_audio)
        
        # Add controls to grid
        control_layout.addWidget(QLabel("Audio:"), 0, 0)
        control_layout.addWidget(self.audio_toggle_btn, 0, 1)
        control_layout.addWidget(QLabel("Volume:"), 1, 0)
        control_layout.addWidget(self.volume_slider, 1, 1)
        control_layout.addWidget(QLabel("Speech Rate:"), 2, 0)
        control_layout.addWidget(self.rate_slider, 2, 1)
        control_layout.addWidget(self.test_audio_btn, 3, 0, 1, 2)
        
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
        if self.audio_feedback.is_initialized:
            self.audio_feedback.speak("Navigation system initialized and ready")
            self._log_status("System initialized with audio feedback")
        else:
            self._log_status("Warning: Audio feedback not available")
    
    def _start_camera(self):
        """Start the camera and QR detection"""
        try:
            self.camera_thread = CameraThread()
            self.camera_thread.frame_ready.connect(self._update_camera_display)
            self.camera_thread.qr_detected.connect(self._handle_qr_detection)
            self.camera_thread.error_occurred.connect(self._handle_camera_error)
            
            self.camera_thread.start()
            
            self.start_camera_btn.setEnabled(False)
            self.stop_camera_btn.setEnabled(True)
            self.status_indicator.setStyleSheet("color: green; font-size: 24px;")
            
            self._log_status("Camera started")
            if self.audio_enabled:
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
        
        self.start_camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)
        self.status_indicator.setStyleSheet("color: red; font-size: 24px;")
        
        self.camera_display.setText("Camera stopped")
        self.qr_status_label.setText("No QR code detected")
        
        self._log_status("Camera stopped")
        if self.audio_enabled:
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
        
        # Try to decode the QR code
        location_data = self.qr_reader.decode_qr_code(roi, color)
        
        if location_data:
            self.current_location = location_data
            # Update FICT current location if possible
            self.fict_nav.set_current_location_from_locationdata(location_data)
            self._update_location_display(location_data)
            self._log_status(f"QR code decoded: {location_data.node_id}")
            
            if self.audio_enabled:
                self.audio_feedback.speak(f"Location identified: {location_data.node_id}")
            
            # Enable route calculation
            self.calculate_route_btn.setEnabled(True)
            
        else:
            self._log_status("QR code detected but could not be decoded")
            if self.audio_enabled:
                self.audio_feedback.speak("QR code detected but could not be read")
    
    def _handle_camera_error(self, error_msg):
        """Handle camera errors"""
        self._log_status(f"Camera error: {error_msg}")
        QMessageBox.warning(self, "Camera Error", f"Camera error: {error_msg}")
        self._stop_camera()
    
    def _update_location_display(self, location_data: LocationData):
        """Update the location display"""
        location_text = f"{location_data.node_id} (Floor {location_data.floor_level})"
        self.location_label.setText(location_text)
        self.qr_status_label.setText(f"QR detected: {location_data.node_id}")
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
            route = route_info['route'] if route_info else None
            
            if route:
                self.current_route = route
                self._display_route(route)
                self._log_status(f"Route calculated to {destination}")
                
                if self.audio_enabled:
                    self.audio_feedback.speak(f"Route calculated to {destination}. {len(route.segments)} steps required.")
                
            else:
                QMessageBox.information(self, "No Route", f"No route found to {destination}")
                self._log_status(f"No route found to {destination}")
                
        except Exception as e:
            self._log_status(f"Error calculating route: {e}")
            QMessageBox.critical(self, "Route Error", f"Failed to calculate route: {e}")
    
    def _display_route(self, route: NavigationRoute):
        """Display the calculated route"""
        route_summary = self.route_guidance.get_route_summary(route)
        self.route_display.setText(route_summary)
        
        # Show progress bar
        self.navigation_progress.setVisible(True)
        self.navigation_progress.setMaximum(len(route.segments))
        self.navigation_progress.setValue(0)
    
    def _toggle_audio(self):
        """Toggle audio feedback on/off"""
        self.audio_enabled = not self.audio_enabled
        
        if self.audio_enabled:
            self.audio_toggle_btn.setText("Audio: ON")
            self.audio_feedback.speak("Audio feedback enabled")
        else:
            self.audio_toggle_btn.setText("Audio: OFF")
            self.audio_feedback.speak("Audio feedback disabled")
        
        self._log_status(f"Audio feedback {'enabled' if self.audio_enabled else 'disabled'}")
    
    def _adjust_volume(self, value):
        """Adjust audio volume"""
        if self.audio_feedback.engine:
            self.audio_feedback.engine.setProperty('volume', value / 100.0)
        self._log_status(f"Volume adjusted to {value}%")
    
    def _adjust_speech_rate(self, value):
        """Adjust speech rate"""
        if self.audio_feedback.engine:
            self.audio_feedback.engine.setProperty('rate', value)
        self._log_status(f"Speech rate adjusted to {value}")
    
    def _test_audio(self):
        """Test audio feedback"""
        if self.audio_enabled:
            self.audio_feedback.speak("Audio feedback test successful")
            self._log_status("Audio test completed")
        else:
            self._log_status("Audio test skipped - audio disabled")
    
    def _log_status(self, message: str):
        """Log status message to the status log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.status_log.append(log_entry)
        
        # Keep only last 100 lines
        lines = self.status_log.toPlainText().split('\n')
        if len(lines) > 100:
            self.status_log.setPlainText('\n'.join(lines[-100:]))
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Space:
            # Spacebar toggles audio
            self._toggle_audio()
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
        
        if self.audio_enabled:
            self.audio_feedback.speak("Navigation system shutting down")
        
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
