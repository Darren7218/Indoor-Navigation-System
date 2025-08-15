#!/usr/bin/env python3
"""
QR Reader GUI Module
Provides a graphical interface for the QR code reader with live camera feed.
"""

import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QGroupBox, QGridLayout, QMessageBox)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
from qr_reader import QRCodeReader, LocationData

class CameraThread(QThread):
    """Thread for handling camera operations to prevent GUI freezing."""
    
    frame_ready = pyqtSignal(np.ndarray)
    qr_detected = pyqtSignal(LocationData)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, qr_reader):
        super().__init__()
        self.qr_reader = qr_reader
        self.is_running = False
        
    def run(self):
        """Main camera loop."""
        if not self.qr_reader.start_camera():
            self.error_occurred.emit("Failed to start camera")
            return
            
        self.is_running = True
        
        while self.is_running:
            try:
                # Get camera frame
                frame = self.qr_reader.get_camera_feed()
                if frame is not None:
                    # Try to detect QR codes
                    location_data = self.qr_reader.read_qr_code()
                    
                    # Draw overlay if QR code detected
                    if location_data:
                        frame = self.qr_reader.draw_qr_overlay(frame, location_data)
                        self.qr_detected.emit(location_data)
                    
                    # Emit frame for display
                    self.frame_ready.emit(frame)
                
                # Small delay to prevent excessive CPU usage
                self.msleep(30)  # ~30 FPS
                
            except Exception as e:
                self.error_occurred.emit(f"Camera error: {str(e)}")
                break
    
    def stop(self):
        """Stop the camera thread."""
        self.is_running = False
        self.qr_reader.stop_camera()
        self.wait()

class QRReaderGUI(QMainWindow):
    """Main GUI window for the QR Reader application."""
    
    def __init__(self):
        super().__init__()
        self.qr_reader = QRCodeReader()
        self.camera_thread = None
        self.is_scanning = False
        
        self.init_ui()
        self.setup_camera()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("QR Code Reader - Indoor Navigation System")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Camera feed
        left_panel = self.create_camera_panel()
        main_layout.addWidget(left_panel, 2)
        
        # Right panel - Controls and information
        right_panel = self.create_control_panel()
        main_layout.addWidget(right_panel, 1)
        
        # Set window properties
        self.setWindowState(Qt.WindowMaximized)
        
    def create_camera_panel(self):
        """Create the camera display panel."""
        panel = QGroupBox("Live Camera Feed")
        layout = QVBoxLayout(panel)
        
        # Camera display label
        self.camera_label = QLabel("Camera not started")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 5px;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.camera_label)
        
        # Camera status
        self.camera_status = QLabel("Status: Camera stopped")
        self.camera_status.setAlignment(Qt.AlignCenter)
        self.camera_status.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(self.camera_status)
        
        return panel
        
    def create_control_panel(self):
        """Create the control and information panel."""
        panel = QGroupBox("Controls & Information")
        layout = QVBoxLayout(panel)
        
        # Control buttons
        control_group = QGroupBox("Camera Controls")
        control_layout = QGridLayout(control_group)
        
        self.start_button = QPushButton("Start Camera")
        self.start_button.clicked.connect(self.start_camera)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        control_layout.addWidget(self.start_button, 0, 0)
        
        self.stop_button = QPushButton("Stop Camera")
        self.stop_button.clicked.connect(self.stop_camera)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.stop_button, 0, 1)
        
        self.scan_button = QPushButton("Start Scanning")
        self.scan_button.clicked.connect(self.toggle_scanning)
        self.scan_button.setEnabled(False)
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.scan_button, 1, 0)
        
        layout.addWidget(control_group)
        
        # QR Code Information
        info_group = QGroupBox("QR Code Information")
        info_layout = QVBoxLayout(info_group)
        
        self.qr_info = QTextEdit()
        self.qr_info.setMaximumHeight(200)
        self.qr_info.setPlaceholderText("No QR code detected yet...")
        self.qr_info.setReadOnly(True)
        info_layout.addWidget(self.qr_info)
        
        layout.addWidget(info_group)
        
        # Recent Detections
        recent_group = QGroupBox("Recent Detections")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_detections = QTextEdit()
        self.recent_detections.setMaximumHeight(150)
        self.recent_detections.setPlaceholderText("No recent detections...")
        self.recent_detections.setReadOnly(True)
        recent_layout.addWidget(self.recent_detections)
        
        layout.addWidget(recent_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
        
    def setup_camera(self):
        """Setup camera timer for frame updates."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
    def start_camera(self):
        """Start the camera and display feed."""
        try:
            if self.camera_thread is None or not self.camera_thread.isRunning():
                self.camera_thread = CameraThread(self.qr_reader)
                self.camera_thread.frame_ready.connect(self.update_camera_display)
                self.camera_thread.qr_detected.connect(self.on_qr_detected)
                self.camera_thread.error_occurred.connect(self.on_camera_error)
                self.camera_thread.start()
                
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.scan_button.setEnabled(True)
                self.camera_status.setText("Status: Camera running")
                self.camera_status.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        font-weight: bold;
                        padding: 5px;
                    }
                """)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start camera: {str(e)}")
            
    def stop_camera(self):
        """Stop the camera and display."""
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread = None
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Start Scanning")
        self.is_scanning = False
        
        self.camera_status.setText("Status: Camera stopped")
        self.camera_status.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        self.camera_label.setText("Camera stopped")
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 5px;
                font-size: 16px;
            }
        """)
        
    def toggle_scanning(self):
        """Toggle QR code scanning on/off."""
        if not self.is_scanning:
            self.is_scanning = True
            self.scan_button.setText("Stop Scanning")
            self.scan_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
        else:
            self.is_scanning = False
            self.scan_button.setText("Start Scanning")
            self.scan_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            
    def update_camera_display(self, frame):
        """Update the camera display with a new frame."""
        if frame is not None:
            # Convert OpenCV frame to Qt image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Scale image to fit label while maintaining aspect ratio
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.camera_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.camera_label.setPixmap(scaled_pixmap)
            
    def on_qr_detected(self, location_data: LocationData):
        """Handle QR code detection."""
        if not self.is_scanning:
            return
            
        # Update QR code information
        info_text = f"""
Location ID: {location_data.location_id}
Floor Level: {location_data.floor_level or 'Unknown'}
Coordinates: {location_data.coordinates or 'Unknown'}
Description: {location_data.description or 'None'}
Confidence: {location_data.confidence:.2f}
Timestamp: {location_data.timestamp}
Raw Data: {location_data.raw_data}
        """.strip()
        
        self.qr_info.setText(info_text)
        
        # Add to recent detections
        recent_text = self.recent_detections.toPlainText()
        timestamp = time.strftime("%H:%M:%S", time.localtime(location_data.timestamp))
        new_detection = f"[{timestamp}] {location_data.location_id}"
        
        if recent_text:
            recent_text = new_detection + "\n" + recent_text
        else:
            recent_text = new_detection
            
        # Keep only last 10 detections
        lines = recent_text.split('\n')[:10]
        self.recent_detections.setText('\n'.join(lines))
        
    def on_camera_error(self, error_message):
        """Handle camera errors."""
        QMessageBox.critical(self, "Camera Error", error_message)
        self.stop_camera()
        
    def closeEvent(self, event):
        """Handle application closure."""
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
        event.accept()

def main():
    """Main function to run the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = QRReaderGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    import time
    main()
