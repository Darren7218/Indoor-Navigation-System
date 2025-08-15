#!/usr/bin/env python3
"""
Demo script for the QR Reader GUI.
This script demonstrates the GUI functionality without requiring a camera.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class DemoWindow(QMainWindow):
    """Demo window to test PyQt5 installation."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the demo UI."""
        self.setWindowTitle("QR Reader GUI Demo")
        self.setGeometry(200, 200, 400, 300)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("QR Reader GUI Demo")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Description
        desc = QLabel("This demo confirms that PyQt5 is working correctly.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Test button
        test_button = QPushButton("Test Button")
        test_button.clicked.connect(self.on_test_click)
        layout.addWidget(test_button)
        
        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add stretch
        layout.addStretch()
        
    def on_test_click(self):
        """Handle test button click."""
        self.status_label.setText("Status: Button clicked successfully!")
        
def main():
    """Main function to run the demo."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    window = DemoWindow()
    window.show()
    
    print("Demo window created successfully!")
    print("If you can see the window, PyQt5 is working correctly.")
    print("You can now run the full GUI with: python qr_reader_ui.py")
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
