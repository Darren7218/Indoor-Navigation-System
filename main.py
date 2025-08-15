"""
Main System Integration
Indoor Navigation System - Main entry point and system coordination
"""

import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Import system modules
from config import create_directories, save_config, UI_SETTINGS, THEMES
from qr_detection import QRCodeDetector
from qr_reader import QRCodeReader, LocationData
from route_guidance import RouteGuidance
from fic_navigation_integration import FICTNavigationSystem
from user_interface import NavigationInterface

# Import PyQt5 for GUI
try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
except ImportError:
    print("PyQt5 not available. Please install PyQt5 to run the GUI.")
    print("Install with: pip install PyQt5")
    sys.exit(1)

class IndoorNavigationSystem:
    """Main system coordinator for the Indoor Navigation System"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.qr_detector = None
        self.qr_reader = None
        self.route_guidance = None
        self.gui = None
        self.app = None
        
        # System state
        self.is_initialized = False
        self.current_location = None
        self.active_route = None
        
        self.logger.info("Indoor Navigation System initializing...")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/navigation_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("Creating system directories...")
            create_directories()
            
            self.logger.info("Initializing QR code detector...")
            self.qr_detector = QRCodeDetector()
            
            self.logger.info("Initializing QR code reader...")
            self.qr_reader = QRCodeReader()
            
            self.logger.info("Initializing route guidance...")
            self.route_guidance = RouteGuidance()
            
            # Initialize FICT integration (used for FICT-only flows)
            self.logger.info("Initializing FICT navigation integration...")
            self.fict_nav = FICTNavigationSystem()

            self.logger.info("System initialization completed successfully")
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    def start_gui(self):
        """Start the graphical user interface"""
        try:
            if not self.is_initialized:
                self.logger.error("Cannot start GUI - system not initialized")
                return False
            
            self.logger.info("Starting graphical user interface...")
            
            # Create Qt application
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Indoor Navigation System")
            self.app.setApplicationVersion("1.0.0")
            
            # Apply system theme
            self._apply_system_theme()
            
            # Create and show main window
            self.gui = NavigationInterface()
            self.gui.show()
            
            self.logger.info("GUI started successfully")
            
            # Run the application
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"Failed to start GUI: {e}")
            QMessageBox.critical(None, "Error", f"Failed to start GUI: {e}")
            return False
    
    def _apply_system_theme(self):
        """Apply system-wide theme settings"""
        try:
            theme_name = UI_SETTINGS.get('theme', 'dark')
            if theme_name in THEMES:
                theme = THEMES[theme_name]
                
                # Apply application-wide stylesheet
                stylesheet = f"""
                QApplication {{
                    background-color: {theme['window_bg']};
                    color: {theme['text_color']};
                }}
                QMainWindow {{
                    background-color: {theme['window_bg']};
                    color: {theme['text_color']};
                }}
                QWidget {{
                    background-color: {theme['window_bg']};
                    color: {theme['text_color']};
                }}
                QPushButton {{
                    background-color: {theme['button_bg']};
                    color: {theme['button_text']};
                    border: 1px solid {theme['border_color']};
                    padding: 8px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {theme['highlight_bg']};
                    color: {theme['highlight_text']};
                }}
                QPushButton:pressed {{
                    background-color: {theme['highlight_bg']};
                    color: {theme['highlight_text']};
                }}
                QLabel {{
                    color: {theme['text_color']};
                }}
                QGroupBox {{
                    color: {theme['text_color']};
                    border: 1px solid {theme['border_color']};
                    border-radius: 4px;
                    margin-top: 10px;
                    padding-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }}
                QComboBox {{
                    background-color: {theme['button_bg']};
                    color: {theme['button_text']};
                    border: 1px solid {theme['border_color']};
                    border-radius: 4px;
                    padding: 5px;
                }}
                QTextEdit {{
                    background-color: {theme['window_bg']};
                    color: {theme['text_color']};
                    border: 1px solid {theme['border_color']};
                    border-radius: 4px;
                }}
                """
                
                self.app.setStyleSheet(stylesheet)
                self.logger.info(f"Applied {theme_name} theme")
                
        except Exception as e:
            self.logger.warning(f"Failed to apply theme: {e}")
    
    def run_command_line(self):
        """Run the system in command-line mode for testing"""
        if not self.is_initialized:
            self.logger.error("Cannot run command line - system not initialized")
            return
        
        self.logger.info("Running in command-line mode")
        
        try:
            # Test QR detection
            self._test_qr_detection()
            
            # Test route calculation
            self._test_route_calculation()
            
            # Test audio feedback
            self._test_audio_feedback()
            
        except KeyboardInterrupt:
            self.logger.info("Command line mode interrupted by user")
        except Exception as e:
            self.logger.error(f"Command line mode error: {e}")

    def run_fict_cli(self):
        """Run a FICT-only CLI flow: scan QR -> choose destination -> compute shortest path."""
        if not self.is_initialized:
            self.logger.error("Cannot run FICT CLI - system not initialized")
            return

        print("\nFICT Navigation (CLI)")
        print("Scan a QR code to set your current location (you have ~15 seconds)...")

        # Scan and set current location via FICT integration
        loc_info = self.fict_nav.scan_qr_and_set_location(max_duration=15.0)
        if not loc_info:
            print("No QR detected or unknown location. You can type a location ID manually.")
            manual_id = input("Enter FICT location ID (e.g., MAIN_ENTRANCE): ").strip()
            if not manual_id:
                print("No location provided. Exiting.")
                return
            # Fallback: try to set via string
            detected = self.fict_nav.detect_current_location(manual_id)
            if not detected:
                print("Provided location not found in FICT catalog. Exiting.")
                return

        current_id = self.fict_nav.get_current_location_id()
        print(f"Current location set: {current_id}")

        # Show destinations list (limit to keep concise)
        all_dests = [d for d in self.fict_nav.get_available_destinations() if d != current_id]
        print(f"\nAvailable destinations ({len(all_dests)} total). Showing first 20:")
        preview = all_dests[:20]
        for i, d in enumerate(preview, 1):
            print(f"  {i:2d}. {d}")

        dest = input("\nType destination ID exactly (e.g., N101) or number from list: ").strip()
        if dest.isdigit():
            idx = int(dest) - 1
            if 0 <= idx < len(preview):
                dest = preview[idx]
            else:
                print("Invalid selection index.")
                return

        route_info = self.fict_nav.get_navigation_route(dest)
        if not route_info:
            print("No route could be computed.")
            return

        print("\nROUTE SUMMARY")
        print(f"From: {route_info['current_location']['location_id']}  ->  To: {route_info['destination']['location_id']}")
        print(f"Floor change needed: {route_info['floor_change_needed']}")
        print(f"Estimated time: {route_info['estimated_time']:.1f} minutes")
        print("Instructions:")
        for step in route_info['instructions']:
            print(f"  - {step}")
    
    def _test_qr_detection(self):
        """Test QR code detection functionality"""
        self.logger.info("Testing QR code detection...")
        
        # This would normally test with actual camera
        # For now, we'll just verify the detector is working
        if self.qr_detector and hasattr(self.qr_detector, 'cap'):
            if self.qr_detector.cap and self.qr_detector.cap.isOpened():
                self.logger.info("QR detector camera initialized successfully")
            else:
                self.logger.warning("QR detector camera not available")
        else:
            self.logger.warning("QR detector not properly initialized")
    
    def _test_route_calculation(self):
        """Test route calculation functionality"""
        self.logger.info("Testing route calculation...")
        
        # Create a test location
        test_location = LocationData(
            node_id="A1",
            coordinates=(0, 0),
            floor_level=1,
            exits={"north": "A2", "east": "B1"},
            timestamp=time.time(),
            confidence=0.9
        )
        
        # Calculate a test route
        try:
            route = self.route_guidance.calculate_route(test_location, "C3")
            
            if route:
                self.logger.info("Route calculation test successful")
                route_summary = self.route_guidance.get_route_summary(route)
                print("\n" + "="*50)
                print("ROUTE CALCULATION TEST")
                print("="*50)
                print(route_summary)
                print("="*50)
            else:
                self.logger.warning("Route calculation test failed - no route found")
        except Exception as e:
            self.logger.error(f"Route calculation test error: {e}")
    
    def _test_audio_feedback(self):
        """Test audio feedback functionality"""
        self.logger.info("Testing audio feedback...")
        
        # This would test the TTS engine
        # For now, we'll just log the test
        self.logger.info("Audio feedback test completed")
    
    def shutdown(self):
        """Shutdown the system gracefully"""
        self.logger.info("Shutting down Indoor Navigation System...")
        
        try:
            if self.qr_detector:
                self.qr_detector.stop_detection()
            
            if self.gui:
                self.gui.close()
            
            if self.app:
                self.app.quit()
            
            self.logger.info("System shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

def print_banner():
    """Print system banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                INDOOR NAVIGATION SYSTEM                      ║
    ║                                                              ║
    ║  QR Code Detection • Route Guidance • Accessible Interface   ║
    ║                                                              ║
    ║  Version: 1.0.0                                              ║
    ║  Designed for Visually Impaired Users                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_usage():
    """Print usage information"""
    usage = """
    Usage:
        python main.py [OPTIONS]
    
    Options:
        --gui, -g          Start graphical user interface (default)
        --cli, -c          Run generic command-line tests (legacy)
        --fict, -f         Run FICT-only flow: scan QR -> choose destination -> shortest path
        --help, -h         Show this help message
    
    Examples:
        python main.py          # Start GUI
        python main.py --cli    # Run command-line tests
        python main.py --help   # Show help
    """
    print(usage)

def main():
    """Main entry point"""
    print_banner()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h']:
            print_usage()
            return 0
        elif arg in ['--cli', '-c']:
            run_mode = 'cli'
        elif arg in ['--fict', '-f']:
            run_mode = 'fict'
        elif arg in ['--gui', '-g']:
            run_mode = 'gui'
        else:
            print(f"Unknown option: {arg}")
            print_usage()
            return 1
    else:
        run_mode = 'gui'  # Default to GUI
    
    # Create and initialize the system
    nav_system = IndoorNavigationSystem()
    
    try:
        # Initialize system components
        if not nav_system.initialize_system():
            print("System initialization failed. Check logs for details.")
            return 1
        
        print("System initialized successfully!")
        
        # Run in selected mode
        if run_mode == 'cli':
            nav_system.run_command_line()
        elif run_mode == 'fict':
            nav_system.run_fict_cli()
        else:
            print("Starting graphical user interface...")
            nav_system.start_gui()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nSystem interrupted by user")
        return 0
    except Exception as e:
        print(f"System error: {e}")
        nav_system.logger.error(f"System error: {e}")
        return 1
    finally:
        nav_system.shutdown()

if __name__ == "__main__":
    sys.exit(main())
