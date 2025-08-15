"""
QR Code Detection Module
Real-time webcam capture with HSV color segmentation for color-coded QR codes
"""

import cv2
import numpy as np
import time
from typing import Tuple, Optional, List
import logging
from config import COLOR_THRESHOLDS, QR_DETECTION

class QRCodeDetector:
    """Real-time QR code detection using color segmentation and size thresholds"""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_colors = []
        self.qr_regions = []
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize webcam capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.camera_index}")
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.logger.info("Camera initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            raise
    
    def _create_color_mask(self, frame: np.ndarray, color: str) -> np.ndarray:
        """Create binary mask for specified color using HSV thresholds"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        if color == 'red':
            # Red wraps around HSV circle, need two masks
            lower1 = np.array(COLOR_THRESHOLDS['red']['lower1'])
            upper1 = np.array(COLOR_THRESHOLDS['red']['upper1'])
            lower2 = np.array(COLOR_THRESHOLDS['red']['lower2'])
            upper2 = np.array(COLOR_THRESHOLDS['red']['upper2'])
            
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = mask1 + mask2
            
        else:
            lower = np.array(COLOR_THRESHOLDS[color]['lower'])
            upper = np.array(COLOR_THRESHOLDS[color]['upper'])
            mask = cv2.inRange(hsv, lower, upper)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _find_color_regions(self, frame: np.ndarray) -> List[Tuple[str, np.ndarray, Tuple[int, int, int, int]]]:
        """Find regions of specified colors in the frame"""
        color_regions = []
        
        for color in ['red', 'green', 'blue']:
            mask = self._create_color_mask(frame, color)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Filter out small noise
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check if region is within size threshold
                    if (QR_DETECTION['min_size'] <= w <= QR_DETECTION['max_size'] and 
                        QR_DETECTION['min_size'] <= h <= QR_DETECTION['max_size']):
                        
                        # Extract region of interest
                        roi = frame[y:y+h, x:x+w]
                        color_regions.append((color, roi, (x, y, w, h)))
        
        return color_regions
    
    def _detect_qr_in_region(self, region: np.ndarray) -> bool:
        """Check if a region contains a QR code using OpenCV's QR detector"""
        try:
            qr_detector = cv2.QRCodeDetector()
            data, bbox, _ = qr_detector.detectAndDecode(region)
            return data != "" and bbox is not None
        except Exception as e:
            self.logger.debug(f"QR detection error: {e}")
            return False
    
    def start_detection(self):
        """Start real-time QR code detection"""
        if self.cap is None:
            raise RuntimeError("Camera not initialized")
        
        self.is_running = True
        self.logger.info("Starting QR code detection...")
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    continue
                
                self.current_frame = frame.copy()
                
                # Find color regions
                color_regions = self._find_color_regions(frame)
                
                # Check each region for QR codes
                detected_qrs = []
                for color, roi, bbox in color_regions:
                    if self._detect_qr_in_region(roi):
                        detected_qrs.append((color, roi, bbox))
                        self.logger.info(f"QR code detected in {color} region at {bbox}")
                
                # Update detected QR codes
                self.qr_regions = detected_qrs
                
                # Draw detection results on frame
                self._draw_detection_results(frame, color_regions, detected_qrs)
                
                # Display frame
                cv2.imshow('QR Code Detection', frame)
                
                # Check for key press to exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
        except KeyboardInterrupt:
            self.logger.info("Detection stopped by user")
        finally:
            self.stop_detection()
    
    def _draw_detection_results(self, frame: np.ndarray, color_regions: List, detected_qrs: List):
        """Draw detection results on the frame for visualization"""
        # Draw all color regions
        for color, roi, (x, y, w, h) in color_regions:
            color_bgr = {
                'red': (0, 0, 255),
                'green': (0, 255, 0),
                'blue': (255, 0, 0)
            }[color]
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 2)
            cv2.putText(frame, color, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bgr, 2)
        
        # Highlight detected QR codes
        for color, roi, (x, y, w, h) in detected_qrs:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 3)
            cv2.putText(frame, f"QR: {color}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame for external processing"""
        return self.current_frame
    
    def get_detected_qrs(self) -> List:
        """Get list of currently detected QR codes"""
        return self.qr_regions
    
    def is_qr_detected(self) -> bool:
        """Check if any QR code is currently detected"""
        return len(self.qr_regions) > 0
    
    def stop_detection(self):
        """Stop QR code detection and release resources"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.logger.info("QR detection stopped")
    
    def calibrate_hsv(self, color: str, sample_frame: np.ndarray):
        """Fast HSV calibration for improved color detection"""
        self.logger.info(f"Starting HSV calibration for {color}")
        
        # Create trackbars for HSV adjustment
        window_name = f"HSV Calibration - {color}"
        cv2.namedWindow(window_name)
        
        # Initialize trackbar values
        h_min, s_min, v_min = COLOR_THRESHOLDS[color]['lower']
        h_max, s_max, v_max = COLOR_THRESHOLDS[color]['upper']
        
        def nothing(x):
            pass
        
        cv2.createTrackbar('H_min', window_name, h_min, 179, nothing)
        cv2.createTrackbar('S_min', window_name, s_min, 255, nothing)
        cv2.createTrackbar('V_min', window_name, v_min, 255, nothing)
        cv2.createTrackbar('H_max', window_name, h_max, 179, nothing)
        cv2.createTrackbar('S_max', window_name, s_max, 255, nothing)
        cv2.createTrackbar('V_max', window_name, v_max, 255, nothing)
        
        while True:
            h_min = cv2.getTrackbarPos('H_min', window_name)
            s_min = cv2.getTrackbarPos('S_min', window_name)
            v_min = cv2.getTrackbarPos('V_min', window_name)
            h_max = cv2.getTrackbarPos('H_max', window_name)
            s_max = cv2.getTrackbarPos('S_max', window_name)
            v_max = cv2.getTrackbarPos('V_max', window_name)
            
            # Create mask with current values
            hsv = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2HSV)
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv, lower, upper)
            
            # Show result
            result = cv2.bitwise_and(sample_frame, sample_frame, mask=mask)
            cv2.imshow('Calibration Result', result)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):  # Save calibration
                COLOR_THRESHOLDS[color]['lower'] = [h_min, s_min, v_min]
                COLOR_THRESHOLDS[color]['upper'] = [h_max, s_max, v_max]
                self.logger.info(f"HSV calibration saved for {color}")
                break
            elif key == ord('q'):  # Quit without saving
                break
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test the QR detector
    detector = QRCodeDetector()
    try:
        detector.start_detection()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        detector.stop_detection()
